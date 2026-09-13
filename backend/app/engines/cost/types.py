"""Dataclasses for Cost Intelligence V1.1."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum

from app.domain.enums import EvidenceSeverity, EvidenceStatus


class CostAssessmentOutcome(str, Enum):
    COST_ANOMALY = "COST_ANOMALY"
    WITHIN_PEER_RANGE = "WITHIN_PEER_RANGE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    INVALID_AMOUNT = "INVALID_AMOUNT"


@dataclass(frozen=True)
class PeerRecord:
    """One comparable (or subject) work. Amounts are as recorded."""

    project_id: int
    internal_project_id: str
    constituency: str
    category: str
    state: str
    work_description: str
    derived_work_type: str
    allocation_amount: int | None
    recommended_date: date | None = None
    is_synthetic: bool = False


@dataclass(frozen=True)
class PeerScope:
    id: str
    label: str
    geography: str
    category: str | None
    derived_work_type: str | None
    precise_work_type: bool = False


@dataclass(frozen=True)
class PeerSelection:
    scope: PeerScope | None
    peers: tuple[PeerRecord, ...]
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
class PeerStatistics:
    peer_count: int
    median: float
    percentile_25: float
    percentile_75: float
    percentile_10: float | None
    percentile_90: float | None
    mad: float
    log_median: float
    log_mad: float


@dataclass(frozen=True)
class PeerQuality:
    score: int
    rationale: str
    median_work_type_similarity: float
    category_match_rate: float


@dataclass(frozen=True)
class ComparableProject:
    project_id: int
    internal_project_id: str
    constituency: str
    category: str
    derived_work_type: str
    allocation_amount: int
    recommended_date: date | None
    amount_distance: int
    work_type_similarity: float = 0.0


@dataclass
class CostIntelligenceResult:
    project_id: int
    internal_project_id: str
    engine: str
    engine_version: str
    evidence_type: str
    outcome: CostAssessmentOutcome
    flagged: bool
    status: EvidenceStatus
    severity: EvidenceSeverity
    peer_scope: str | None
    peer_scope_label: str | None
    peer_count: int
    baseline: float | None
    actual_amount: int | None
    deviation_percentage: float | None
    percentile_25: float | None
    percentile_75: float | None
    percentile_10: float | None
    percentile_90: float | None
    mad: float | None
    modified_z: float | None
    cost_anomaly_score: int | None
    evidence_confidence: int
    explanation: str
    why_flagged: str | None
    why_not_flagged: str | None
    comparable_projects: list[ComparableProject] = field(default_factory=list)
    peer_project_ids: list[int] = field(default_factory=list)
    derived_work_type: str = ""
    observed_category: str = ""
    constituency: str = ""
    amount_unit_note: str = ""
    attempted_scopes: tuple[str, ...] = ()
    expected_range_low: float | None = None
    expected_range_high: float | None = None
    best_attempt_peer_count: int = 0
    peer_quality: int = 0
    similarity_rationale: str = ""
    median_work_type_similarity: float | None = None
    constituency_kind: str = ""
    constituency_usable: bool = True
    constituency_exclusion_reason: str | None = None
    signal_kind: str = "allocation_cost_anomaly"
    score_method: str | None = None
    log_mad: float | None = None
