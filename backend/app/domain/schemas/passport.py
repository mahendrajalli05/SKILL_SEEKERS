from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.enums import LifecycleStage
from app.domain.schemas.evidence import EvidenceObject
from app.domain.schemas.project import ProjectRead


class NeedImpactSection(BaseModel):
    """Decision-support placeholder. Full assessment is GET /need-impact."""

    score: float | None = None
    need_score: float | None = None
    impact_score: float | None = None
    priority_score: float | None = None
    priority_class: str | None = None
    unavailable_signals: list[str] = Field(
        default_factory=lambda: [
            "infrastructure_gap",
            "population_reach",
            "access",
            "sc_st_placement",
        ]
    )
    note: str = (
        "Priority recommendation only. Authorized officials make final "
        "administrative decisions. Need & Impact remains INCONCLUSIVE where "
        "census, infrastructure-gap, or beneficiary sources are unavailable."
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
