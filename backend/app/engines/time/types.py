"""Dataclasses for Time Intelligence V1."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum

from app.domain.enums import EvidenceSeverity, EvidenceStatus


class TimeMode(str, Enum):
    REAL = "REAL"
    HYBRID_TEST = "HYBRID_TEST"


class TimeAssessmentOutcome(str, Enum):
    TIME_ANOMALY = "TIME_ANOMALY"
    WITHIN_SCHEDULE = "WITHIN_SCHEDULE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    INVALID_DATES = "INVALID_DATES"


class ScheduleFamily(str, Enum):
    """Date-completeness family. Not a scenario label."""

    NONE = "none"
    OPEN = "open"
    CLOSED = "closed"
    INVALID = "invalid"
    REAL_RECOMMENDATION_ONLY = "real_recommendation_only"


class TimeSignalKind(str, Enum):
    INSUFFICIENT_EXECUTION_TIMING = "insufficient_execution_timing"
    SCHEDULE_SLIPPAGE = "schedule_slippage"
    SCHEDULE_PROGRESS_MISMATCH = "schedule_progress_mismatch"
    INVALID_DATES = "invalid_dates"


@dataclass(frozen=True)
class DelayContext:
    delay_detected: bool
    cause_established: bool
    context_note: str
    recorded_context_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class PeerScope:
    id: str
    label: str
    geography: str
    category: str | None
    derived_work_type: str | None
    precise_work_type: bool = False


@dataclass(frozen=True)
class TimePeerRecord:
    """One work for time comparison.

    HYBRID schedule fields are attached only in HYBRID_TEST mode.
    Scenario labels are never stored here.
    """

    project_id: int
    internal_project_id: str
    constituency: str
    category: str
    state: str
    work_description: str
    derived_work_type: str
    status: str
    lifecycle_stage: str
    recommended_date: date | None
    time_mode: TimeMode
    planned_start_date: date | None = None
    planned_completion_date: date | None = None
    actual_start_date: date | None = None
    actual_completion_date: date | None = None
    physical_progress_percent: int | None = None
    as_of_date: date | None = None
    observation_date: date | None = None


@dataclass(frozen=True)
class PeerSelection:
    scope: PeerScope | None
    peers: tuple[TimePeerRecord, ...]
    attempted_scopes: tuple[str, ...]
    best_attempt_peer_count: int = 0
    constituency_usable: bool = True
    constituency_kind: str = "geographic"
    constituency_exclusion_reason: str | None = None

    @property
    def peer_count(self) -> int:
        return len(self.peers)

    @property
    def sufficient(self) -> bool:
        return self.scope is not None and len(self.peers) > 0


@dataclass(frozen=True)
class PeerQuality:
    score: int
    rationale: str
    median_work_type_similarity: float
    category_match_rate: float


@dataclass(frozen=True)
class ScheduleMetrics:
    family: ScheduleFamily
    date_issues: tuple[str, ...]
    planned_duration_days: int | None
    actual_duration_days: int | None
    elapsed_duration_days: int | None
    slippage_days: int | None
    finish_delay_days: int | None
    time_consumed_percent: float | None
    physical_progress_percent: int | None
    expected_progress_percent: float | None
    progress_mismatch_points: float | None
    recommendation_age_days: int | None
    start_date_used: date | None
    as_of_date: date | None


@dataclass(frozen=True)
class ComparableProject:
    project_id: int
    internal_project_id: str
    constituency: str
    category: str
    derived_work_type: str
    status: str
    planned_duration_days: int | None
    actual_duration_days: int | None
    elapsed_duration_days: int | None
    physical_progress_percent: int | None
    work_type_similarity: float = 0.0
    recommended_date: date | None = None


@dataclass
class TimeIntelligenceResult:
    project_id: int
    internal_project_id: str
    engine: str
    engine_version: str
    evidence_type: str
    dataset_type: str
    time_mode: TimeMode
    outcome: TimeAssessmentOutcome
    flagged: bool
    status: EvidenceStatus
    severity: EvidenceSeverity
    signal_kind: str
    peer_scope: str | None
    peer_scope_label: str | None
    peer_count: int
    peer_quality: int
    similarity_rationale: str
    median_work_type_similarity: float | None
    observed_status: str
    lifecycle_stage: str
    recommended_date: date | None
    observation_date: date | None
    recommendation_age_days: int | None
    planned_start_date: date | None
    planned_completion_date: date | None
    actual_start_date: date | None
    actual_completion_date: date | None
    planned_duration_days: int | None
    actual_duration_days: int | None
    elapsed_duration_days: int | None
    slippage_days: int | None
    physical_progress_percent: int | None
    expected_progress_percent: float | None
    time_consumed_percent: float | None
    progress_mismatch_points: float | None
    peer_median_duration_days: float | None
    time_anomaly_score: int | None
    evidence_confidence: int
    explanation: str
    why_flagged: str | None
    why_not_flagged: str | None
    delay_detected: bool
    cause_established: bool
    delay_context_note: str
    comparable_projects: list[ComparableProject] = field(default_factory=list)
    peer_project_ids: list[int] = field(default_factory=list)
    derived_work_type: str = ""
    observed_category: str = ""
    constituency: str = ""
    attempted_scopes: tuple[str, ...] = ()
    best_attempt_peer_count: int = 0
    constituency_kind: str = ""
    constituency_usable: bool = True
    constituency_exclusion_reason: str | None = None
    score_method: str | None = None
    schedule_family: str = ""
    date_issues: tuple[str, ...] = ()
    as_of_date: date | None = None
