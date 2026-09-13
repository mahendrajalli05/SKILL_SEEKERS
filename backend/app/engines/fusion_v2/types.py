"""Dataclasses for Risk Fusion V2."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from app.domain.enums import (
    DataMode,
    FusionExplanationType,
    InvestigationPriorityBand,
    RecommendedAction,
)
from app.engines.fusion_v2.constants import ENGINE_VERSION


class V2EvidenceState(str, Enum):
    """How a V2 group is treated. Unavailable is not low risk or suspicious."""

    ASSESSABLE = "ASSESSABLE"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    NOT_ASSESSABLE = "NOT_ASSESSABLE"
    INCONCLUSIVE = "INCONCLUSIVE"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_USED_FOR_INVESTIGATION = "NOT_USED_FOR_INVESTIGATION"


class V2SignalPolarity(str, Enum):
    NEGATIVE = "NEGATIVE_SIGNAL"
    POSITIVE = "POSITIVE_SIGNAL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class EvidenceItemContribution:
    """One Evidence Object inside a V2 group."""

    evidence_id: str
    signal_type: str
    engine_name: str
    raw_evidence_score: int | None
    mapped_score: int | None
    confidence: float
    disposition: str
    data_mode: str
    source_ids: list[str]
    finding: str | None

    def as_payload(self) -> dict[str, object]:
        return {
            "evidence_id": self.evidence_id,
            "signal_type": self.signal_type,
            "engine_name": self.engine_name,
            "raw_evidence_score": self.raw_evidence_score,
            "mapped_score": self.mapped_score,
            "confidence": self.confidence,
            "disposition": self.disposition,
            "data_mode": self.data_mode,
            "source_ids": list(self.source_ids),
            "finding": self.finding,
        }


@dataclass
class GroupContribution:
    """One catalog group after mapping, confidence, and correlation."""

    group_id: str
    display_name: str
    weight: float
    state: V2EvidenceState
    polarity: V2SignalPolarity
    raw_evidence_score: int | None
    confidence: float | None
    confidence_adjusted_score: float | None
    correlation_factor: float
    correlation_reason: str | None
    effective_contribution: float
    evidence_ids: list[str]
    source_ids: list[str]
    items: list[EvidenceItemContribution]
    finding: str | None
    support: str | None
    unavailable_reason: str | None
    data_mode: str | None = None
    flagged: bool = False
    peer_quality: int | None = None
    independent: bool = True

    def as_payload(self) -> dict[str, object]:
        return {
            "signal": self.group_id,
            "group_id": self.group_id,
            "display_name": self.display_name,
            "weight": self.weight,
            "state": self.state.value,
            "polarity": self.polarity.value,
            "raw_evidence_score": self.raw_evidence_score,
            "confidence": self.confidence,
            "confidence_adjusted_score": self.confidence_adjusted_score,
            "correlation_factor": self.correlation_factor,
            "correlation_reason": self.correlation_reason,
            "dependency_correlation_adjustment": self.correlation_factor,
            "effective_contribution": self.effective_contribution,
            "evidence_ids": list(self.evidence_ids),
            "source_ids": list(self.source_ids),
            "items": [item.as_payload() for item in self.items],
            "finding": self.finding,
            "support": self.support,
            "unavailable_reason": self.unavailable_reason,
            "data_mode": self.data_mode,
            "flagged": self.flagged,
            "peer_quality": self.peer_quality,
            "independent": self.independent,
        }


@dataclass(frozen=True)
class ConflictRecord:
    left_group: str
    right_group: str
    left_polarity: str
    right_polarity: str
    summary: str

    def as_payload(self) -> dict[str, object]:
        return {
            "left_group": self.left_group,
            "right_group": self.right_group,
            "left_polarity": self.left_polarity,
            "right_polarity": self.right_polarity,
            "summary": self.summary,
        }


@dataclass
class FusionV2Result:
    """Fused Investigation Priority and Evidence Confidence. Not a legal finding."""

    project_id: int
    internal_project_id: str | None
    investigation_priority: int
    investigation_priority_0_100: float
    raw_risk: float
    evidence_confidence: int
    risk_class: InvestigationPriorityBand
    explanation_type: FusionExplanationType
    recommended_action: RecommendedAction
    data_mode: DataMode
    contributing_evidence_groups: list[GroupContribution]
    independent_evidence_groups: list[GroupContribution]
    discounted_correlated_evidence: list[GroupContribution]
    unavailable_evidence: list[GroupContribution]
    not_assessable_evidence: list[GroupContribution]
    conflicting_evidence: list[ConflictRecord]
    all_groups: list[GroupContribution]
    evidence_ids: list[str]
    ignored_duplicate_evidence_ids: list[str]
    explanation: str
    recommendation: str
    available_weight: float
    unavailable_weight: float
    evidence_coverage: float
    weight_note: str
    governance_note: str
    synthetic_disclosure: str | None
    evidence_fingerprint: str
    engine_version: str = ENGINE_VERSION
    explanation_types: list[str] = field(default_factory=list)
    held_out_scenario_type: str | None = None
    held_out_demo_case_id: str | None = None
    prior_result_id: int | None = None
