"""Investigation Priority and Evidence Confidence formulas.

Unavailable weights are not redistributed. Engine scores are not modified.

V1.1 display:
  Raw Risk = sum(w_i * s_i) for assessable integrated signals  (max 70)
  Investigation Priority = Raw Risk / 0.70

Because each s_i is already 0–100, dividing the 0–70 raw total by 0.70
produces a 0–100 display (Cost=100 only → 25 / 0.70 = 35.7).

The divisor is always the planned integrated weight (0.70), never the
currently available weight. Cost=100 with other signals missing stays
capped by the missing-signal penalty; it does not become 100.
"""

from __future__ import annotations

from app.domain.enums import DataMode, InvestigationPriorityBand, RecommendedAction, RiskSignalState
from app.engines.fusion.constants import (
    EC_COVERAGE_WEIGHT,
    EC_FUTURE_COVERAGE_WEIGHT,
    EC_HYBRID_CAP,
    EC_INDEPENDENCE_WEIGHT,
    EC_NONE_ASSESSABLE_CAP,
    EC_QUALITY_WEIGHT,
    EC_REAL_CAP,
    EC_SYNTHETIC_CAP,
    ENGINE_FLAG_THRESHOLD,
    FUTURE_WEIGHT_SUM,
    INSPECT_ACTION_MAX,
    INTEGRATED_SIGNAL_IDS,
    INTEGRATED_WEIGHT_SUM,
    LOW_PRIORITY_MAX,
    MEDIUM_PRIORITY_MAX,
)
from app.engines.fusion.types import SignalContribution


def bounded_score(value: float) -> int:
    """Deterministic integer in 0–100. Non-negative half-up rounding."""
    if value != value:  # NaN
        return 0
    if value <= 0:
        return 0
    if value >= 100:
        return 100
    return int(value + 0.5)


def raw_risk(signals: list[SignalContribution]) -> float:
    """Un-renormalized weighted sum of assessable risk scores.

    Theoretical V1/V1.1 maximum is 70 (integrated weights only).
    Unavailable, NOT_ASSESSABLE, INCONCLUSIVE, and not-yet-integrated
    slots contribute 0 and their weights are not given to other signals.
    """
    total = 0.0
    for item in signals:
        if item.signal_id not in INTEGRATED_SIGNAL_IDS:
            continue
        if item.state != RiskSignalState.ASSESSABLE:
            continue
        if item.risk_score is None:
            continue
        total += item.weight * float(item.risk_score)
    return round(total, 4)


def investigation_priority_0_100(signals: list[SignalContribution]) -> float:
    """Display formula before integer rounding: Raw Risk / 0.70."""
    raw = raw_risk(signals)
    if INTEGRATED_WEIGHT_SUM <= 0:
        return 0.0
    value = raw / INTEGRATED_WEIGHT_SUM
    if value != value:
        return 0.0
    return round(min(100.0, max(0.0, value)), 1)


def investigation_priority(signals: list[SignalContribution]) -> int:
    """Displayed Investigation Priority on a 0–100 scale.

    IP = clip(round(Raw Risk / 0.70), 0, 100)

    Equivalent to scaling the 0–70 raw total onto 0–100. This is NOT a
    silent renormalization onto currently available signals. The divisor is
    always 0.70, so missing integrated weight remains a penalty.
    """
    raw = raw_risk(signals)
    if INTEGRATED_WEIGHT_SUM <= 0:
        return 0
    return bounded_score(raw / INTEGRATED_WEIGHT_SUM)


def available_weight(signals: list[SignalContribution]) -> float:
    return available_signal_weight(signals)


def available_signal_weight(signals: list[SignalContribution]) -> float:
    return round(
        sum(
            item.weight
            for item in signals
            if item.signal_id in INTEGRATED_SIGNAL_IDS
            and item.state == RiskSignalState.ASSESSABLE
        ),
        4,
    )


def unavailable_signal_weight(signals: list[SignalContribution]) -> float:
    """Unused integrated weight (0.70 minus available). Excludes reserved 30%."""
    return round(INTEGRATED_WEIGHT_SUM - available_signal_weight(signals), 4)


def unused_weight(signals: list[SignalContribution]) -> float:
    """All non-assessable planned weight, including reserved future slots."""
    return round(
        sum(item.weight for item in signals if item.state != RiskSignalState.ASSESSABLE),
        4,
    )


def evidence_coverage(signals: list[SignalContribution]) -> float:
    """Available integrated weight divided by the planned 0.70 subtotal."""
    if INTEGRATED_WEIGHT_SUM <= 0:
        return 0.0
    return round(available_signal_weight(signals) / INTEGRATED_WEIGHT_SUM, 4)


def signal_is_flagged(item: SignalContribution) -> bool:
    if item.state != RiskSignalState.ASSESSABLE:
        return False
    if item.flagged:
        return True
    if item.disposition == "WHY_FLAGGED":
        return True
    if item.risk_score is not None and item.risk_score >= ENGINE_FLAG_THRESHOLD:
        return True
    return False


def evidence_confidence(
    signals: list[SignalContribution],
    *,
    data_mode: DataMode,
) -> int:
    """Separate from Investigation Priority.

    EC = 100 * (
        0.40 * (W_assessable / 0.70) +
        0.35 * quality +
        0.15 * (n_assessable / 4) +
        0.10 * 0   # reserved 30% always unavailable in V1.1
    )

    Then cap by data mode. Low evidence is not the same as low risk.
    """
    assessable = [
        item
        for item in signals
        if item.signal_id in INTEGRATED_SIGNAL_IDS and item.state == RiskSignalState.ASSESSABLE
    ]
    not_assessable = [
        item
        for item in signals
        if item.signal_id in INTEGRATED_SIGNAL_IDS
        and item.state == RiskSignalState.NOT_ASSESSABLE
        and item.evidence_confidence is not None
    ]
    if not assessable:
        if not not_assessable:
            return 0
        mean_c = sum(item.evidence_confidence or 0.0 for item in not_assessable) / len(
            not_assessable
        )
        return min(EC_NONE_ASSESSABLE_CAP, bounded_score(100 * 0.25 * mean_c))

    w_assessable = sum(item.weight for item in assessable)
    coverage = w_assessable / INTEGRATED_WEIGHT_SUM if INTEGRATED_WEIGHT_SUM else 0.0
    quality_num = 0.0
    quality_den = 0.0
    for item in assessable:
        conf = item.evidence_confidence if item.evidence_confidence is not None else 0.0
        quality_num += item.weight * max(0.0, min(1.0, conf))
        quality_den += item.weight
    quality = (quality_num / quality_den) if quality_den else 0.0
    independence = len(assessable) / float(len(INTEGRATED_SIGNAL_IDS))
    future_coverage = 0.0  # reserved 30% is unavailable; not renormalized
    raw = 100.0 * (
        EC_COVERAGE_WEIGHT * coverage
        + EC_QUALITY_WEIGHT * quality
        + EC_INDEPENDENCE_WEIGHT * independence
        + EC_FUTURE_COVERAGE_WEIGHT * future_coverage
    )
    score = bounded_score(raw)
    if data_mode == DataMode.HYBRID:
        return min(score, EC_HYBRID_CAP)
    if data_mode == DataMode.SYNTHETIC:
        return min(score, EC_SYNTHETIC_CAP)
    return min(score, EC_REAL_CAP)


def priority_band(priority: int) -> InvestigationPriorityBand:
    if priority <= LOW_PRIORITY_MAX:
        return InvestigationPriorityBand.LOW
    if priority <= MEDIUM_PRIORITY_MAX:
        return InvestigationPriorityBand.MEDIUM
    return InvestigationPriorityBand.HIGH


def recommended_action(priority: int) -> RecommendedAction:
    """Transparent mapping on the displayed 0–100 Investigation Priority.

    Not a legal or administrative decision. Evidence Confidence is consulted
    by the explanation, not used to invent a fraud conclusion.
    """
    if priority <= LOW_PRIORITY_MAX:
        return RecommendedAction.MONITOR
    if priority <= MEDIUM_PRIORITY_MAX:
        return RecommendedAction.REVIEW
    if priority <= INSPECT_ACTION_MAX:
        return RecommendedAction.INSPECT
    return RecommendedAction.INVESTIGATE


def future_weight() -> float:
    return FUTURE_WEIGHT_SUM
