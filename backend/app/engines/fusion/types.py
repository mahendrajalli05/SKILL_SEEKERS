"""Dataclasses for Risk Fusion V1.1."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.enums import (
    DataMode,
    EvidenceDisposition,
    FusionExplanationType,
    InvestigationPriorityBand,
    RecommendedAction,
    RiskSignalState,
)
from app.engines.fusion.constants import ENGINE_VERSION


@dataclass(frozen=True)
class SignalContribution:
    """One planned fusion slot. Unavailable is distinct from a 0 risk score."""

    signal_id: str
    display_name: str
    weight: float
    state: RiskSignalState
    risk_score: int | None
    contribution: float
    evidence_confidence: float | None
    evidence_id: str | None
    disposition: str | None
    finding: str | None
    support: str | None
    unavailable_reason: str | None
    data_mode: str | None = None
    flagged: bool = False
    peer_quality: int | None = None

    def as_payload(self) -> dict[str, object]:
        return {
            "signal_id": self.signal_id,
            "display_name": self.display_name,
            "weight": self.weight,
            "state": self.state.value,
            "risk_score": self.risk_score,
            "contribution": self.contribution,
            "evidence_confidence": self.evidence_confidence,
            "evidence_id": self.evidence_id,
            "disposition": self.disposition,
            "finding": self.finding,
            "support": self.support,
            "unavailable_reason": self.unavailable_reason,
            "data_mode": self.data_mode,
            "flagged": self.flagged,
            "peer_quality": self.peer_quality,
        }


@dataclass
class FusionResult:
    """Fused Investigation Priority and Evidence Confidence. Not a legal finding."""

    project_id: int
    internal_project_id: str | None
    investigation_priority: int
    investigation_priority_0_100: float
    raw_risk: float
    evidence_confidence: int
    priority_band: InvestigationPriorityBand
    explanation_type: FusionExplanationType
    recommended_action: RecommendedAction
    data_mode: DataMode
    contributing_signals: list[SignalContribution]
    unavailable_signals: list[SignalContribution]
    all_signals: list[SignalContribution]
    evidence_ids: list[str]
    ignored_duplicate_evidence_ids: list[str]
    explanation: str
    recommendation: str
    available_weight: float
    available_signal_weight: float
    unavailable_signal_weight: float
    unused_weight: float
    reserved_unavailable_weight: float
    evidence_coverage: float
    weight_note: str
    governance_note: str
    engine_version: str = ENGINE_VERSION
    explanation_types: list[str] = field(default_factory=list)
    held_out_scenario_type: str | None = None
    held_out_demo_case_id: str | None = None
    held_out_mixed_signals: str | None = None
