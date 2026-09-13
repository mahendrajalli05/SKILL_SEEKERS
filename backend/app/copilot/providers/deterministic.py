"""Deterministic fallback provider. Always available without an API key."""

from __future__ import annotations

from app.copilot.answer import build_deterministic_answer
from app.copilot.types import CopilotDraft, CopilotIntent, CopilotProviderName, InvestigationBundle


class DeterministicProvider:
    name = CopilotProviderName.DETERMINISTIC.value
    uses_llm = False

    def complete(
        self,
        question: str,
        bundle: InvestigationBundle,
        intent: CopilotIntent,
        history: list[dict[str, str]],
    ) -> CopilotDraft:
        _ = question, history
        return build_deterministic_answer(bundle, intent)
