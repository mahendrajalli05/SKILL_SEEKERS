"""Dataclasses for Overlap / Duplicate Intelligence V1."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum

from app.domain.enums import EvidenceSeverity, EvidenceStatus


class OverlapMode(str, Enum):
    REAL = "REAL"
    HYBRID_TEST = "HYBRID_TEST"


class OverlapAssessmentOutcome(str, Enum):
    POTENTIAL_DUPLICATE = "POTENTIAL_DUPLICATE"
    POTENTIAL_OVERLAP = "POTENTIAL_OVERLAP"
    NOT_LINKED = "NOT_LINKED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True)
class OverlapRecord:
    """One work for overlap comparison.

    Scenario labels are never stored here. GPS is present only when the
    caller attached real or explicitly HYBRID synthetic coordinates.
    """

    project_id: int
    internal_project_id: str
    source_work: str
    work_description: str
    embedding_text: str
    category: str
    constituency: str
    constituency_usable: bool
    constituency_kind: str
    state: str
    allocation_amount: int | None
    recommended_date: date | None
    city: str = ""
    ward: str = ""
    block: str = ""
    village: str = ""
    place_text: str = ""
    rare_tokens: frozenset[str] = field(default_factory=frozenset)
    latitude: float | None = None
    longitude: float | None = None
    gps_is_synthetic: bool = False


@dataclass(frozen=True)
class SignalValue:
    """One scored signal. None means the field was unavailable, not zero."""

    name: str
    value: float | None
    available: bool
    detail: str


@dataclass(frozen=True)
class PairSignals:
    semantic_similarity: float | None
    category_match: bool | None
    constituency_match: bool | None
    amount_similarity: float | None
    date_proximity: float | None
    date_gap_days: int | None
    location_similarity: float | None
    gps_similarity: float | None
    gps_distance_m: float | None
    overall_score: float
    overlap_score: int
    evidence_confidence: int
    supporting_count: int
    supporting_signals: tuple[str, ...]
    unavailable_signals: tuple[str, ...]
    outcome: OverlapAssessmentOutcome
    geographic_evidence_available: bool


@dataclass(frozen=True)
class OverlapMatch:
    project_id: int
    internal_project_id: str
    linked_project_id: int
    linked_internal_project_id: str
    linked_source_work: str
    linked_work_description: str
    linked_category: str
    linked_constituency: str
    linked_allocation_amount: int | None
    linked_recommended_date: date | None
    semantic_similarity: float | None
    category_match: bool | None
    constituency_match: bool | None
    amount_similarity: float | None
    date_proximity: float | None
    date_gap_days: int | None
    location_similarity: float | None
    gps_similarity: float | None
    gps_distance_m: float | None
    overall_overlap_score: int
    evidence_confidence: int
    outcome: OverlapAssessmentOutcome
    flagged: bool
    geographic_evidence_available: bool
    supporting_signals: tuple[str, ...]
    unavailable_signals: tuple[str, ...]
    reasons: tuple[str, ...]
    why_linked: str | None
    why_not_linked: str | None
    explanation: str


@dataclass
class OverlapIntelligenceResult:
    project_id: int
    internal_project_id: str
    engine: str
    engine_version: str
    evidence_type: str
    dataset_type: str
    overlap_mode: OverlapMode
    outcome: OverlapAssessmentOutcome
    flagged: bool
    status: EvidenceStatus
    severity: EvidenceSeverity
    signal_kind: str
    candidate_count: int
    match_count: int
    overlap_score: int | None
    evidence_confidence: int
    embedding_backend: str
    geographic_evidence_available: bool
    explanation: str
    why_linked: str | None
    why_not_linked: str | None
    matches: list[OverlapMatch] = field(default_factory=list)
    source_work: str = ""
    work_description: str = ""
    observed_category: str = ""
    constituency: str = ""
    constituency_kind: str = ""
    constituency_usable: bool = True
    constituency_exclusion_reason: str | None = None
    blocking_strategy: str = ""
    gps_used: bool = False
