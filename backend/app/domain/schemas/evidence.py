from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import EvidenceEngine, EvidenceSeverity, EvidenceStatus


class EvidenceFact(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    key: str
    value: str
    source: str


class EvidenceObject(BaseModel):
    """Envelope written by engines. Copilot may quote facts only."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    project_id: int
    engine: EvidenceEngine
    engine_version: str
    evidence_type: str
    status: EvidenceStatus = EvidenceStatus.INCONCLUSIVE
    severity: EvidenceSeverity = EvidenceSeverity.INFO
    summary: str | None = None
    comparables: list[int] = Field(default_factory=list)
    rule_ids: list[str] = Field(default_factory=list)
    guideline_refs: list[str] = Field(default_factory=list)
    facts: list[EvidenceFact] = Field(default_factory=list)
    created_at: datetime | None = None
