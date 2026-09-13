"""LLM provider protocol for Investigation Copilot V1."""

from __future__ import annotations

from typing import Protocol

from app.copilot.types import CopilotDraft, CopilotIntent, InvestigationBundle


class CopilotProvider(Protocol):
    name: str
    uses_llm: bool

    def complete(
        self,
        question: str,
        bundle: InvestigationBundle,
        intent: CopilotIntent,
        history: list[dict[str, str]],
    ) -> CopilotDraft:
        ...
