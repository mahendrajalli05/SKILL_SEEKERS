from __future__ import annotations

from pydantic import BaseModel, Field

from app.copilot.constants import ENGINE_VERSION, GOVERNANCE_NOTE, SUGGESTED_QUESTIONS
from app.domain.enums import DataMode


class CopilotChatRequest(BaseModel):
    question: str
    session_id: str | None = None
    data_mode: str | None = None


class CopilotSourceRef(BaseModel):
    id: str
    kind: str
    label: str


class CopilotSectionsRead(BaseModel):
    answer: str
    why: str
    evidence: str
    missing: str
    recommended_action: str


class CopilotTurnRead(BaseModel):
    question: str
    answer: str
    intent: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    recommended_action: str | None = None
    provider: str | None = None
    created_at: str | None = None


class CopilotChatResponse(BaseModel):
    project_id: int
    internal_project_id: str
    scheme_id: str | None = None
    session_id: str
    question: str
    intent: str
    answer: str
    sections: CopilotSectionsRead
    evidence_ids: list[str] = Field(default_factory=list)
    source_refs: list[CopilotSourceRef] = Field(default_factory=list)
    data_mode: DataMode
    data_mode_notice: str
    limitations: list[str] = Field(default_factory=list)
    recommended_action: str | None = None
    observed_facts: list[str] = Field(default_factory=list)
    derived_findings: list[str] = Field(default_factory=list)
    unavailable: list[str] = Field(default_factory=list)
    insufficient_evidence: bool = False
    hybrid_used: bool = False
    provider: str
    used_llm: bool = False
    governance_note: str = GOVERNANCE_NOTE
    engine_version: str = ENGINE_VERSION


class CopilotContextResponse(BaseModel):
    project_id: int
    internal_project_id: str
    scheme_id: str | None = None
    data_mode: DataMode
    data_mode_notice: str
    engines_present: list[str] = Field(default_factory=list)
    evidence_count: int = 0
    suggested_questions: list[str] = Field(default_factory=lambda: list(SUGGESTED_QUESTIONS))
    session_id: str
    turns: list[CopilotTurnRead] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    governance_note: str = GOVERNANCE_NOTE
    engine_version: str = ENGINE_VERSION
    llm_provider: str
