"""Optional local/open model provider.

Never used unless an explicit local base URL is configured. Failures fall
through to the deterministic provider in the service layer.
"""

from __future__ import annotations

import json

import httpx

from app.copilot.answer import build_deterministic_answer
from app.copilot.context import compact_context
from app.copilot.errors import CopilotError
from app.copilot.types import (
    CopilotDraft,
    CopilotIntent,
    CopilotProviderName,
    CopilotRecommendation,
    CopilotSections,
    InvestigationBundle,
)

_SYSTEM = (
    "You are SARVSAKSHI Investigation Copilot. Answer only from the JSON context. "
    "Never invent facts, evidence IDs, scores, regulations, satellite results, "
    "citizen complaints, or contractor names. Never say fraud is established. "
    "If a field is missing, say that information is not available in the current evidence. "
    "Preserve NOT_ASSESSABLE. Distinguish observed facts from derived findings. "
    "Respond as five labelled sections: ANSWER, WHY, EVIDENCE, MISSING INFORMATION, "
    "RECOMMENDED ACTION. Recommended action must be MONITOR, REVIEW, INSPECT, or "
    "NEED MORE INFORMATION."
)


def _parse_sections(text: str) -> CopilotSections | None:
    labels = [
        "ANSWER",
        "WHY",
        "EVIDENCE",
        "MISSING INFORMATION",
        "RECOMMENDED ACTION",
    ]
    positions: list[tuple[str, int]] = []
    upper = text.upper()
    for label in labels:
        idx = upper.find(label + ":")
        if idx < 0:
            idx = upper.find(label)
        if idx < 0:
            return None
        positions.append((label, idx))
    positions.sort(key=lambda item: item[1])
    values: dict[str, str] = {}
    for index, (label, start) in enumerate(positions):
        end = positions[index + 1][1] if index + 1 < len(positions) else len(text)
        chunk = text[start:end]
        chunk = chunk.split(":", 1)[1] if ":" in chunk[:40] else chunk[len(label) :]
        values[label] = chunk.strip()
    if len(values) < 5:
        return None
    return CopilotSections(
        answer=values["ANSWER"],
        why=values["WHY"],
        evidence=values["EVIDENCE"],
        missing=values["MISSING INFORMATION"],
        recommended_action=values["RECOMMENDED ACTION"],
    )


class LocalProvider:
    name = CopilotProviderName.LOCAL.value
    uses_llm = True

    def __init__(self, base_url: str, model: str, timeout: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model or "local"
        self.timeout = timeout

    def complete(
        self,
        question: str,
        bundle: InvestigationBundle,
        intent: CopilotIntent,
        history: list[dict[str, str]],
    ) -> CopilotDraft:
        fallback = build_deterministic_answer(bundle, intent)
        context = compact_context(bundle, intent)
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": _SYSTEM},
                {
                    "role": "user",
                    "content": json.dumps(
                        {"question": question, "history": history[-4:], "context": context},
                        default=str,
                    ),
                },
            ],
            "temperature": 0,
        }
        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            body = response.json()
            text = body["choices"][0]["message"]["content"]
        except Exception as exc:  # noqa: BLE001 — local model is optional
            raise CopilotError(
                "Local model is unavailable; using the grounded fallback.",
                code="local_llm_unavailable",
                status_code=503,
            ) from exc
        sections = _parse_sections(text)
        if sections is None:
            return fallback
        action_text = sections.recommended_action.strip().upper()
        try:
            action = CopilotRecommendation(action_text)
        except ValueError:
            action = fallback.recommended_action
            sections.recommended_action = action.value
        fallback.sections = sections
        fallback.recommended_action = action
        fallback.provider = CopilotProviderName.LOCAL
        fallback.used_llm = True
        return fallback
