from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import EvidenceSeverity, EvidenceStatus
from app.engines.time.constants import ENGINE_NAME, ENGINE_VERSION, EVIDENCE_TYPE
from app.engines.time.types import TimeAssessmentOutcome, TimeIntelligenceResult, TimeMode


class TimeComparableProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    project_id: int
    internal_project_id: str
    constituency: str
    category: str
    derived_work_type: str
    status: str
    planned_duration_days: int | None = None
    actual_duration_days: int | None = None
    elapsed_duration_days: int | None = None
    physical_progress_percent: int | None = None
    work_type_similarity: float = 0.0
    recommended_date: date | None = None


class TimeIntelligenceResponse(BaseModel):
    """Time Anomaly evidence for one work. Investigation Priority is not assigned here."""

    project_id: int
    internal_project_id: str
    engine: str = ENGINE_NAME
    engine_version: str = ENGINE_VERSION
    evidence_type: str = EVIDENCE_TYPE
    dataset_type: str
    time_mode: TimeMode
    outcome: TimeAssessmentOutcome
    flagged: bool
    status: EvidenceStatus
    severity: EvidenceSeverity
    signal_kind: str
    peer_scope: str | None = None
    peer_scope_label: str | None = None
    peer_count: int
    peer_quality: int = 0
    similarity_rationale: str = ""
    observed_status: str = ""
    lifecycle_stage: str = ""
    recommended_date: date | None = None
    observation_date: date | None = None
    recommendation_age_days: int | None = None
    planned_start_date: date | None = None
    planned_completion_date: date | None = None
    actual_start_date: date | None = None
    actual_completion_date: date | None = None
    planned_duration_days: int | None = None
    actual_duration_days: int | None = None
    elapsed_duration_days: int | None = None
    slippage_days: int | None = None
    physical_progress_percent: int | None = None
    expected_progress_percent: float | None = None
    time_consumed_percent: float | None = None
    progress_mismatch_points: float | None = None
    time_anomaly_score: int | None = None
    evidence_confidence: int
    explanation: str
    why_flagged: str | None = None
    why_not_flagged: str | None = None
    delay_detected: bool = False
    cause_established: bool = False
    delay_context_note: str = ""
    comparable_projects: list[TimeComparableProjectRead] = Field(default_factory=list)
    peer_project_ids: list[int] = Field(default_factory=list)
    derived_work_type: str = ""
    observed_category: str = ""
    constituency: str = ""
    attempted_scopes: list[str] = Field(default_factory=list)
    best_attempt_peer_count: int = 0
    constituency_kind: str = ""
    constituency_usable: bool = True
    constituency_exclusion_reason: str | None = None
    score_method: str | None = None
    schedule_family: str = ""
    as_of_date: date | None = None

    @classmethod
    def from_result(cls, result: TimeIntelligenceResult) -> TimeIntelligenceResponse:
        return cls.model_validate(result, from_attributes=True)
