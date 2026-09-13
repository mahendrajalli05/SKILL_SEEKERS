"""Officer-facing fusion explanations. Never claims fraud."""

from __future__ import annotations

from app.domain.enums import (
    DataMode,
    FusionExplanationType,
    InvestigationPriorityBand,
    RecommendedAction,
    RiskSignalState,
)
from app.engines.fusion.constants import (
    FUTURE_WEIGHT_SUM,
    GOVERNANCE_NOTE,
    INTEGRATED_SIGNAL_IDS,
    WEIGHT_NOTE,
)
from app.engines.fusion.scoring import signal_is_flagged
from app.engines.fusion.types import SignalContribution


_ACTION_TEXT = {
    RecommendedAction.MONITOR: (
        "Monitor the work using the available records. No fused signal currently "
        "warrants a higher review queue on its own. This uses the displayed "
        "Investigation Priority and Evidence Confidence; it is not a legal "
        "conclusion."
    ),
    RecommendedAction.REVIEW: (
        "Review comparable works and inspect supporting evidence before taking "
        "further action. This uses the displayed Investigation Priority and "
        "Evidence Confidence; it is not a legal conclusion."
    ),
    RecommendedAction.INSPECT: (
        "Inspect supporting documents, comparables, and field evidence before "
        "taking further action. This is a review recommendation based on "
        "Investigation Priority and Evidence Confidence, not a legal finding."
    ),
    RecommendedAction.INVESTIGATE: (
        "Investigate the contributing evidence in detail. This is a recommended "
        "investigation action based on Investigation Priority and Evidence "
        "Confidence, not a legal or administrative decision."
    ),
}


def _band_word(band: InvestigationPriorityBand) -> str:
    return band.value.lower()


def _assessable(signals: list[SignalContribution]) -> list[SignalContribution]:
    return [
        item
        for item in signals
        if item.signal_id in INTEGRATED_SIGNAL_IDS and item.state == RiskSignalState.ASSESSABLE
    ]


def explanation_type(
    signals: list[SignalContribution],
    *,
    priority: int,
    band: InvestigationPriorityBand,
) -> FusionExplanationType:
    assessable = _assessable(signals)
    flagged = [item for item in assessable if signal_is_flagged(item)]
    if not assessable:
        return FusionExplanationType.INSUFFICIENT_EVIDENCE
    if flagged and band != InvestigationPriorityBand.LOW:
        return FusionExplanationType.WHY_FLAGGED
    if flagged and band == InvestigationPriorityBand.LOW:
        return FusionExplanationType.INCONCLUSIVE
    if len(assessable) >= 2 and not flagged and band == InvestigationPriorityBand.LOW:
        return FusionExplanationType.WHY_NOT_FLAGGED
    if len(assessable) == 1 and not flagged:
        return FusionExplanationType.INCONCLUSIVE
    return FusionExplanationType.INCONCLUSIVE


def _signal_phrase(item: SignalContribution) -> str:
    if item.risk_score is None:
        return f"{item.display_name} is unavailable"
    return f"{item.display_name} {item.risk_score}"


def _available_phrase(item: SignalContribution) -> str:
    score = "n/a" if item.risk_score is None else str(item.risk_score)
    return f"{item.display_name} {score} (weight {item.weight:.2f})"


def _unavailable_phrase(item: SignalContribution) -> str:
    if item.state == RiskSignalState.NOT_ASSESSABLE:
        status = "not assessable"
    elif item.state == RiskSignalState.NOT_YET_INTEGRATED:
        status = "not yet integrated"
    else:
        status = "unavailable"
    return f"{item.display_name} ({status}, weight {item.weight:.2f})"


def _top_contributing(assessable: list[SignalContribution], limit: int = 3) -> list[SignalContribution]:
    return sorted(
        assessable,
        key=lambda item: (-(item.contribution or 0.0), item.signal_id),
    )[:limit]


def build_explanation(
    signals: list[SignalContribution],
    *,
    priority: int,
    confidence: int,
    band: InvestigationPriorityBand,
    data_mode: DataMode,
    kind: FusionExplanationType,
    raw_risk: float = 0.0,
    investigation_priority_0_100: float = 0.0,
    available_signal_weight: float = 0.0,
    unavailable_signal_weight: float = 0.0,
    evidence_coverage: float = 0.0,
) -> str:
    assessable = _assessable(signals)
    flagged = [item for item in assessable if signal_is_flagged(item)]
    not_flagged = [item for item in assessable if not signal_is_flagged(item)]
    integrated_unavailable = [
        item
        for item in signals
        if item.signal_id in INTEGRATED_SIGNAL_IDS and item.state != RiskSignalState.ASSESSABLE
    ]
    future = [
        item
        for item in signals
        if item.state == RiskSignalState.NOT_YET_INTEGRATED
    ]

    parts: list[str] = []
    n = len(assessable)

    parts.append(
        f"Investigation Priority is {priority} on the 0-100 display scale "
        f"(formula result {investigation_priority_0_100}; "
        f"Raw Risk {raw_risk} / 0.70). "
        f"Priority band is {_band_word(band)}."
    )

    if kind == FusionExplanationType.INSUFFICIENT_EVIDENCE:
        parts.append(
            "Investigation Priority is low because no assessable intelligence "
            "signals were available to fuse (inconclusive)."
        )
    elif kind == FusionExplanationType.WHY_FLAGGED:
        names = ", ".join(item.display_name for item in flagged) or "available signals"
        parts.append(
            f"{n} assessable signal(s) were fused and {names} indicated elevated "
            "review need."
        )
    elif kind == FusionExplanationType.WHY_NOT_FLAGGED:
        parts.append(
            f"{n} assessable signals were within their engine review flags, so "
            "Investigation Priority remains low."
        )
    else:
        if flagged and not_flagged:
            parts.append(
                "Signals conflict: "
                + ", ".join(_signal_phrase(item) for item in assessable)
                + "."
            )
        else:
            parts.append(
                f"{n} assessable signal(s) were fused. Evidence is not sufficient "
                "for a stronger conclusion."
            )

    parts.append(
        f"Evidence Confidence is {confidence}, calculated separately from "
        "Investigation Priority. A high priority with low confidence is not a "
        "highly certain conclusion."
    )

    if assessable:
        parts.append(
            "Available signals: "
            + "; ".join(_available_phrase(item) for item in assessable)
            + f". Available signal weight={available_signal_weight:.2f}; "
            f"evidence coverage={evidence_coverage:.4f}."
        )
        details: list[str] = []
        for item in assessable:
            support = item.support or item.finding or "engine evidence object"
            details.append(
                f"The {item.display_name.lower()} signal is {item.risk_score} "
                f"({item.disposition or 'assessable'}). Evidence: {support}"
            )
        parts.append(" ".join(details))
        top = _top_contributing(assessable)
        parts.append(
            "Top contributing signals: "
            + "; ".join(
                f"{item.display_name} {item.risk_score} (raw contribution "
                f"{item.contribution:.2f})"
                for item in top
            )
            + "."
        )
    else:
        parts.append(
            "Available signals: none. "
            f"Available signal weight={available_signal_weight:.2f}; "
            f"evidence coverage={evidence_coverage:.4f}."
        )

    unavailable_labels = [_unavailable_phrase(item) for item in integrated_unavailable]
    if unavailable_labels:
        parts.append(
            "Unavailable signals: "
            + "; ".join(unavailable_labels)
            + f". Unavailable signal weight={unavailable_signal_weight:.2f}. "
            "Missing weights were not redistributed to the remaining signals."
        )
    else:
        parts.append(
            "Unavailable signals: none among the four integrated engines. "
            f"Unavailable signal weight={unavailable_signal_weight:.2f}."
        )

    future_names = ", ".join(item.display_name for item in future)
    parts.append(
        f"Reserved signals ({int(FUTURE_WEIGHT_SUM * 100)}% combined: {future_names}) "
        "are not yet integrated. No evidence was invented for them. "
        "Display scaling is Raw Risk / 0.70, not a renormalization onto "
        f"currently available signals only. {WEIGHT_NOTE}"
    )

    if data_mode == DataMode.HYBRID:
        parts.append(
            "Data mode is HYBRID: observed MPLADS fields plus synthetic enrichment. "
            "Synthetic fields are not official MPLADS values."
        )
    elif data_mode == DataMode.SYNTHETIC:
        parts.append(
            "Data mode is SYNTHETIC: this is a test record, not a government project."
        )
    else:
        parts.append("Data mode is REAL: fusion used observed MPLADS evidence only.")

    parts.append(
        "Recommended action uses the displayed Investigation Priority together "
        "with Evidence Confidence. It is not a legal conclusion. "
        f"{GOVERNANCE_NOTE}"
    )
    return " ".join(parts)


def build_recommendation(action: RecommendedAction) -> str:
    return _ACTION_TEXT[action]


def explanation_type_list(kind: FusionExplanationType) -> list[str]:
    return [kind.value]
