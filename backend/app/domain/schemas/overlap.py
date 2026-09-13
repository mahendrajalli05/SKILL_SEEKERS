from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import EvidenceSeverity, EvidenceStatus
from app.engines.overlap.constants import ENGINE_NAME, ENGINE_VERSION, EVIDENCE_TYPE
from app.engines.overlap.types import OverlapAssessmentOutcome, OverlapIntelligenceResult, OverlapMode


class OverlapMatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    project_id: int
    internal_project_id: str
    linked_project_id: int
    linked_internal_project_id: str
    linked_source_work: str = ""
    linked_work_description: str = ""
    linked_category: str = ""
    linked_constituency: str = ""
    linked_allocation_amount: int | None = None
    linked_recommended_date: date | None = None
    semantic_similarity: float | None = None
    category_match: bool | None = None
    constituency_match: bool | None = None
    amount_similarity: float | None = None
    date_proximity: float | None = None
    date_gap_days: int | None = None
    location_similarity: float | None = None
    gps_similarity: float | None = None
    gps_distance_m: float | None = None
    overall_overlap_score: int
    evidence_confidence: int
    outcome: OverlapAssessmentOutcome
    flagged: bool
    geographic_evidence_available: bool
    supporting_signals: list[str] = Field(default_factory=list)
    unavailable_signals: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    why_linked: str | None = None
    why_not_linked: str | None = None
    explanation: str = ""


class OverlapIntelligenceResponse(BaseModel):
    """Potential Overlap evidence for one work. Investigation Priority is not assigned here."""

    project_id: int
    internal_project_id: str
    engine: str = ENGINE_NAME
    engine_version: str = ENGINE_VERSION
    evidence_type: str = EVIDENCE_TYPE
    dataset_type: str
    overlap_mode: OverlapMode
    outcome: OverlapAssessmentOutcome
    flagged: bool
    status: EvidenceStatus
    severity: EvidenceSeverity
    signal_kind: str
    candidate_count: int
    match_count: int
    overlap_score: int | None = None
    evidence_confidence: int
    embedding_backend: str = ""
    geographic_evidence_available: bool = False
    explanation: str
    why_linked: str | None = None
    why_not_linked: str | None = None
    matches: list[OverlapMatchRead] = Field(default_factory=list)
    source_work: str = ""
    work_description: str = ""
    observed_category: str = ""
    constituency: str = ""
    constituency_kind: str = ""
    constituency_usable: bool = True
    constituency_exclusion_reason: str | None = None
    blocking_strategy: str = ""
    gps_used: bool = False

    @classmethod
    def from_result(cls, result: OverlapIntelligenceResult) -> OverlapIntelligenceResponse:
        return cls(
            project_id=result.project_id,
            internal_project_id=result.internal_project_id,
            engine=result.engine,
            engine_version=result.engine_version,
            evidence_type=result.evidence_type,
            dataset_type=result.dataset_type,
            overlap_mode=result.overlap_mode,
            outcome=result.outcome,
            flagged=result.flagged,
            status=result.status,
            severity=result.severity,
            signal_kind=result.signal_kind,
            candidate_count=result.candidate_count,
            match_count=result.match_count,
            overlap_score=result.overlap_score,
            evidence_confidence=result.evidence_confidence,
            embedding_backend=result.embedding_backend,
            geographic_evidence_available=result.geographic_evidence_available,
            explanation=result.explanation,
            why_linked=result.why_linked,
            why_not_linked=result.why_not_linked,
            matches=[
                OverlapMatchRead.model_validate(item, from_attributes=True)
                for item in result.matches
            ],
            source_work=result.source_work,
            work_description=result.work_description,
            observed_category=result.observed_category,
            constituency=result.constituency,
            constituency_kind=result.constituency_kind,
            constituency_usable=result.constituency_usable,
            constituency_exclusion_reason=result.constituency_exclusion_reason,
            blocking_strategy=result.blocking_strategy,
            gps_used=result.gps_used,
        )
