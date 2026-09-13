from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import EvidenceSeverity, EvidenceStatus
from app.engines.cost.constants import AMOUNT_UNIT_NOTE, ENGINE_NAME, ENGINE_VERSION, EVIDENCE_TYPE
from app.engines.cost.types import CostAssessmentOutcome, CostIntelligenceResult


class ComparableProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    project_id: int
    internal_project_id: str
    constituency: str
    category: str
    derived_work_type: str
    allocation_amount: int
    recommended_date: date | None = None
    amount_distance: int
    work_type_similarity: float = 0.0


class CostIntelligenceResponse(BaseModel):
    """Allocation Cost Anomaly evidence for one work. Investigation Priority is not assigned here."""

    project_id: int
    internal_project_id: str
    engine: str = ENGINE_NAME
    engine_version: str = ENGINE_VERSION
    evidence_type: str = EVIDENCE_TYPE
    outcome: CostAssessmentOutcome
    flagged: bool
    status: EvidenceStatus
    severity: EvidenceSeverity
    peer_scope: str | None = None
    peer_scope_label: str | None = None
    peer_count: int
    peer_quality: int = 0
    similarity_rationale: str = ""
    median_work_type_similarity: float | None = None
    baseline: float | None = None
    expected_range_low: float | None = None
    expected_range_high: float | None = None
    actual_amount: int | None = None
    deviation_percentage: float | None = None
    percentile_25: float | None = None
    percentile_75: float | None = None
    percentile_10: float | None = None
    percentile_90: float | None = None
    mad: float | None = None
    modified_z: float | None = None
    cost_anomaly_score: int | None = None
    evidence_confidence: int
    explanation: str
    why_flagged: str | None = None
    why_not_flagged: str | None = None
    comparable_projects: list[ComparableProjectRead] = Field(default_factory=list)
    peer_project_ids: list[int] = Field(default_factory=list)
    derived_work_type: str = ""
    observed_category: str = ""
    constituency: str = ""
    amount_unit_note: str = AMOUNT_UNIT_NOTE
    attempted_scopes: list[str] = Field(default_factory=list)
    best_attempt_peer_count: int = 0
    constituency_kind: str = ""
    constituency_usable: bool = True
    constituency_exclusion_reason: str | None = None
    signal_kind: str = "allocation_cost_anomaly"
    score_method: str | None = None
    log_mad: float | None = None

    @classmethod
    def from_result(cls, result: CostIntelligenceResult) -> CostIntelligenceResponse:
        return cls(
            project_id=result.project_id,
            internal_project_id=result.internal_project_id,
            engine=result.engine,
            engine_version=result.engine_version,
            evidence_type=result.evidence_type,
            outcome=result.outcome,
            flagged=result.flagged,
            status=result.status,
            severity=result.severity,
            peer_scope=result.peer_scope,
            peer_scope_label=result.peer_scope_label,
            peer_count=result.peer_count,
            peer_quality=result.peer_quality,
            similarity_rationale=result.similarity_rationale,
            median_work_type_similarity=result.median_work_type_similarity,
            baseline=result.baseline,
            expected_range_low=result.expected_range_low,
            expected_range_high=result.expected_range_high,
            actual_amount=result.actual_amount,
            deviation_percentage=result.deviation_percentage,
            percentile_25=result.percentile_25,
            percentile_75=result.percentile_75,
            percentile_10=result.percentile_10,
            percentile_90=result.percentile_90,
            mad=result.mad,
            modified_z=result.modified_z,
            cost_anomaly_score=result.cost_anomaly_score,
            evidence_confidence=result.evidence_confidence,
            explanation=result.explanation,
            why_flagged=result.why_flagged,
            why_not_flagged=result.why_not_flagged,
            comparable_projects=[
                ComparableProjectRead.model_validate(item, from_attributes=True)
                for item in result.comparable_projects
            ],
            peer_project_ids=result.peer_project_ids,
            derived_work_type=result.derived_work_type,
            observed_category=result.observed_category,
            constituency=result.constituency,
            amount_unit_note=result.amount_unit_note,
            attempted_scopes=list(result.attempted_scopes),
            best_attempt_peer_count=result.best_attempt_peer_count,
            constituency_kind=result.constituency_kind,
            constituency_usable=result.constituency_usable,
            constituency_exclusion_reason=result.constituency_exclusion_reason,
            signal_kind=result.signal_kind,
            score_method=result.score_method,
            log_mad=result.log_mad,
        )
