from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.enums import LifecycleStage
from app.domain.schemas.evidence import EvidenceObject
from app.domain.schemas.project import ProjectRead


class NeedImpactSection(BaseModel):
    """Partial until census / infrastructure-gap sources are actually available."""

    score: float | None = None
    unavailable_signals: list[str] = Field(
        default_factory=lambda: [
            "infrastructure_gap",
            "population_reach",
            "access",
            "sc_st_placement",
        ]
    )
    note: str = (
        "Need & Impact is partial until external data sources are available. "
        "Do not treat a missing score as a place label."
    )


class ProjectDigitalPassport(BaseModel):
    identity: ProjectRead
    lifecycle_stage: LifecycleStage = LifecycleStage.UNKNOWN
    investigation_priority: int | None = Field(default=None, ge=0, le=100)
    evidence_confidence: int | None = Field(default=None, ge=0, le=100)
    why_flagged: list[str] = Field(default_factory=list)
    why_not_flagged: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    evidence: list[EvidenceObject] = Field(default_factory=list)
    need_impact: NeedImpactSection = Field(default_factory=NeedImpactSection)
    provenance_source_url: str | None = None
    provenance_extracted_at: str | None = None
    is_synthetic: bool = False
    synthetic_label: str | None = None
