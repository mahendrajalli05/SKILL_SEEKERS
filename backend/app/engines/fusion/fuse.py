"""Risk Fusion V1.1 core.

Consumes Evidence Objects and produces Investigation Priority and
Evidence Confidence. Does not determine fraud.
Display IP = Raw Risk / 0.70 (0–70 raw total onto a 0–100 scale).
Missing-signal weights are not redistributed onto currently available signals.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.domain.enums import DataMode, RiskSignalState
from app.domain.schemas.evidence import EvidenceObject
from app.engines.fusion.constants import (
    COST_INCLUDED_IN_HYBRID_NOTE,
    ENGINE_VERSION,
    FUTURE_WEIGHT_SUM,
    GOVERNANCE_NOTE,
    INTEGRATED_SIGNAL_IDS,
    WEIGHT_NOTE,
)
from app.engines.fusion.explain import (
    build_explanation,
    build_recommendation,
    explanation_type,
    explanation_type_list,
)
from app.engines.fusion.scoring import (
    available_signal_weight,
    available_weight,
    evidence_confidence,
    evidence_coverage,
    investigation_priority,
    investigation_priority_0_100,
    priority_band,
    raw_risk,
    recommended_action,
    unavailable_signal_weight,
    unused_weight,
)
from app.engines.fusion.signals import build_signal_table
from app.engines.fusion.types import FusionResult, SignalContribution


def resolve_fusion_data_mode(
    objects: Sequence[EvidenceObject],
    *,
    requested: DataMode | None = None,
) -> DataMode:
    modes = {obj.data_mode for obj in objects}
    if DataMode.HYBRID in modes:
        return DataMode.HYBRID
    if DataMode.SYNTHETIC in modes:
        return DataMode.SYNTHETIC
    if DataMode.REAL in modes:
        return DataMode.REAL
    return requested or DataMode.REAL


def _contributing(signals: list[SignalContribution]) -> list[SignalContribution]:
    items = [
        item
        for item in signals
        if item.signal_id in INTEGRATED_SIGNAL_IDS and item.state == RiskSignalState.ASSESSABLE
    ]
    return sorted(items, key=lambda item: (-(item.risk_score or 0), item.signal_id))


def _unavailable(signals: list[SignalContribution]) -> list[SignalContribution]:
    return [
        item
        for item in signals
        if item.state != RiskSignalState.ASSESSABLE
    ]


def fuse_evidence(
    objects: Sequence[EvidenceObject],
    *,
    project_id: int,
    internal_project_id: str | None = None,
    requested_data_mode: DataMode | None = None,
) -> FusionResult:
    """Deterministic fusion. Engine scores are used as-is when assessable."""
    data_mode = resolve_fusion_data_mode(objects, requested=requested_data_mode)
    signals, ignored = build_signal_table(objects, preferred_mode=requested_data_mode)
    raw = raw_risk(signals)
    display_ip = investigation_priority_0_100(signals)
    priority = investigation_priority(signals)
    confidence = evidence_confidence(signals, data_mode=data_mode)
    avail = available_signal_weight(signals)
    unavail = unavailable_signal_weight(signals)
    coverage = evidence_coverage(signals)
    band = priority_band(priority)
    kind = explanation_type(signals, priority=priority, band=band)
    action = recommended_action(priority)
    explanation = build_explanation(
        signals,
        priority=priority,
        confidence=confidence,
        band=band,
        data_mode=data_mode,
        kind=kind,
        raw_risk=raw,
        investigation_priority_0_100=display_ip,
        available_signal_weight=avail,
        unavailable_signal_weight=unavail,
        evidence_coverage=coverage,
    )
    if data_mode == DataMode.HYBRID and any(
        item.signal_id == "cost" and item.data_mode == DataMode.REAL.value for item in signals
    ):
        explanation = f"{explanation} {COST_INCLUDED_IN_HYBRID_NOTE}"
    evidence_ids = [
        item.evidence_id
        for item in signals
        if item.evidence_id
    ]
    return FusionResult(
        project_id=project_id,
        internal_project_id=internal_project_id,
        investigation_priority=priority,
        investigation_priority_0_100=display_ip,
        raw_risk=raw,
        evidence_confidence=confidence,
        priority_band=band,
        explanation_type=kind,
        recommended_action=action,
        data_mode=data_mode,
        contributing_signals=_contributing(signals),
        unavailable_signals=_unavailable(signals),
        all_signals=signals,
        evidence_ids=evidence_ids,
        ignored_duplicate_evidence_ids=ignored,
        explanation=explanation,
        recommendation=build_recommendation(action),
        available_weight=available_weight(signals),
        available_signal_weight=avail,
        unavailable_signal_weight=unavail,
        unused_weight=unused_weight(signals),
        reserved_unavailable_weight=FUTURE_WEIGHT_SUM,
        evidence_coverage=coverage,
        weight_note=WEIGHT_NOTE,
        governance_note=GOVERNANCE_NOTE,
        engine_version=ENGINE_VERSION,
        explanation_types=explanation_type_list(kind),
    )
