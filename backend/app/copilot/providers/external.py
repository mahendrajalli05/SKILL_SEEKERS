"""Optional external LLM provider.

Disabled by default. Sensitive project data is never sent externally unless
SARVSAKSHI_LLM_EXTERNAL_ALLOWED is explicitly true.
"""

from __future__ import annotations

import json

import httpx

from app.copilot.errors import CopilotError
from app.copilot.providers.local import _SYSTEM, _parse_sections
from app.copilot.answer import build_deterministic_answer
from app.copilot.context import compact_context
from app.copilot.types import (
    CopilotDraft,
    CopilotIntent,
    CopilotProviderName,
    CopilotRecommendation,
    InvestigationBundle,
)


class ExternalProvider:
    name = CopilotProviderName.EXTERNAL.value
    uses_llm = True

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str,
        timeout: float,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
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
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            text = response.json()["choices"][0]["message"]["content"]
        except Exception as exc:  # noqa: BLE001 — external LLM is optional
            raise CopilotError(
                "External LLM is unavailable; using the grounded fallback.",
                code="external_llm_unavailable",
                status_code=503,
            ) from exc
        sections = _parse_sections(text)
        if sections is None:
            return fallback
        try:
            action = CopilotRecommendation(sections.recommended_action.strip().upper())
        except ValueError:
            action = fallback.recommended_action
            sections.recommended_action = action.value
        fallback.sections = sections
        fallback.recommended_action = action
        fallback.provider = CopilotProviderName.EXTERNAL
        fallback.used_llm = True
        return fallback
