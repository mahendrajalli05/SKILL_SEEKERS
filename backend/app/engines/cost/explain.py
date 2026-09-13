"""Factual Cost Intelligence explanations.

Uses calculated figures only. Supports WHY FLAGGED and WHY NOT FLAGGED.
This engine reports Allocation Cost Anomaly and Evidence Confidence.
It does not assign Investigation Priority.
"""

from __future__ import annotations

from app.engines.cost.constants import (
    AMOUNT_UNIT_NOTE,
    FLAG_SCORE_THRESHOLD,
    SIGNAL_SEPARATION_NOTE,
)
from app.engines.cost.types import CostAssessmentOutcome


def _format_number(value: float | int) -> str:
    if isinstance(value, int) or (isinstance(value, float) and value.is_integer()):
        return f"{int(value)}"
    return f"{value:.1f}"


def _direction_phrase(deviation_percentage: float) -> str:
    if deviation_percentage > 0:
        return f"{abs(deviation_percentage):.1f}% above"
    if deviation_percentage < 0:
        return f"{abs(deviation_percentage):.1f}% below"
    return "equal to"


def invalid_amount_explanation() -> str:
    return (
        "Allocation Cost Anomaly was not assessed: allocation amount is missing, "
        "zero, or otherwise not a positive recorded value. Evidence Confidence "
        f"is 0. Investigation Priority is not assigned by this engine. "
        f"{SIGNAL_SEPARATION_NOTE} {AMOUNT_UNIT_NOTE}"
    )


def insufficient_peers_explanation(
    *,
    attempted_scopes: tuple[str, ...],
    peer_count: int,
    evidence_confidence: int,
    constituency_exclusion_reason: str | None = None,
) -> str:
    attempted = ", ".join(attempted_scopes) if attempted_scopes else "none"
    geography_note = ""
    if constituency_exclusion_reason:
        geography_note = f" {constituency_exclusion_reason}"
    return (
        "Allocation Cost Anomaly was not assessed: fewer than 5 comparable works "
        f"were available after geographic constituency-first selection and "
        f"Andhra Pradesh state fallback (largest usable group found: {peer_count}; "
        f"scopes attempted: {attempted}).{geography_note} Insufficient evidence; "
        f"no anomaly score is produced. Evidence Confidence is {evidence_confidence}. "
        f"Investigation Priority is not assigned by this engine. {SIGNAL_SEPARATION_NOTE}"
    )


def why_flagged_explanation(
    *,
    deviation_percentage: float,
    peer_count: int,
    peer_scope_label: str,
    baseline: float,
    actual_amount: int,
    score: int,
    evidence_confidence: int,
    peer_quality: int,
    similarity_rationale: str,
    percentile_25: float,
    percentile_75: float,
) -> str:
    direction = _direction_phrase(deviation_percentage)
    return (
        f"Allocation is {direction} the median of {peer_count} comparable works "
        f"in the {peer_scope_label}. Actual allocation is "
        f"{_format_number(actual_amount)} versus peer median "
        f"{_format_number(baseline)} (expected range "
        f"{_format_number(percentile_25)}-{_format_number(percentile_75)}). "
        f"Allocation Cost Anomaly score is {score} "
        f"(review flag at {FLAG_SCORE_THRESHOLD} on the 0-100 log-robust mapping). "
        f"Peer quality is {peer_quality}/100. {similarity_rationale} "
        f"Evidence Confidence is {evidence_confidence}. This Allocation Cost "
        f"Anomaly signal may inform later Investigation Priority. "
        f"{SIGNAL_SEPARATION_NOTE} {AMOUNT_UNIT_NOTE}"
    )


def why_not_flagged_explanation(
    *,
    deviation_percentage: float,
    peer_count: int,
    peer_scope_label: str,
    baseline: float,
    actual_amount: int,
    score: int,
    percentile_25: float,
    percentile_75: float,
    evidence_confidence: int,
    peer_quality: int,
    similarity_rationale: str,
) -> str:
    direction = _direction_phrase(deviation_percentage)
    return (
        f"Allocation is {direction} the median of {peer_count} comparable works "
        f"in the {peer_scope_label}. Actual allocation is "
        f"{_format_number(actual_amount)} versus peer median "
        f"{_format_number(baseline)} (expected range "
        f"{_format_number(percentile_25)}-{_format_number(percentile_75)}). "
        f"Allocation Cost Anomaly score is {score}, below the review flag of "
        f"{FLAG_SCORE_THRESHOLD}. Not flagged as an Allocation Cost Anomaly. "
        f"Peer quality is {peer_quality}/100. {similarity_rationale} "
        f"Evidence Confidence is {evidence_confidence}. Investigation Priority "
        f"is not assigned by this engine. {SIGNAL_SEPARATION_NOTE} {AMOUNT_UNIT_NOTE}"
    )


def explanation_for(
    outcome: CostAssessmentOutcome,
    *,
    deviation_percentage: float | None = None,
    peer_count: int = 0,
    peer_scope_label: str | None = None,
    baseline: float | None = None,
    actual_amount: int | None = None,
    score: int | None = None,
    percentile_25: float | None = None,
    percentile_75: float | None = None,
    attempted_scopes: tuple[str, ...] = (),
    evidence_confidence: int = 0,
    peer_quality: int = 0,
    similarity_rationale: str = "",
    constituency_exclusion_reason: str | None = None,
) -> tuple[str, str | None, str | None]:
    """Return (explanation, why_flagged, why_not_flagged)."""
    if outcome == CostAssessmentOutcome.INVALID_AMOUNT:
        text = invalid_amount_explanation()
        return text, None, text
    if outcome == CostAssessmentOutcome.INSUFFICIENT_EVIDENCE:
        text = insufficient_peers_explanation(
            attempted_scopes=attempted_scopes,
            peer_count=peer_count,
            evidence_confidence=evidence_confidence,
            constituency_exclusion_reason=constituency_exclusion_reason,
        )
        return text, None, text
    assert deviation_percentage is not None
    assert peer_scope_label is not None
    assert baseline is not None
    assert actual_amount is not None
    assert score is not None
    low = percentile_25 if percentile_25 is not None else baseline
    high = percentile_75 if percentile_75 is not None else baseline
    if outcome == CostAssessmentOutcome.COST_ANOMALY:
        flagged = why_flagged_explanation(
            deviation_percentage=deviation_percentage,
            peer_count=peer_count,
            peer_scope_label=peer_scope_label,
            baseline=baseline,
            actual_amount=actual_amount,
            score=score,
            evidence_confidence=evidence_confidence,
            peer_quality=peer_quality,
            similarity_rationale=similarity_rationale,
            percentile_25=low,
            percentile_75=high,
        )
        return flagged, flagged, None
    not_flagged = why_not_flagged_explanation(
        deviation_percentage=deviation_percentage,
        peer_count=peer_count,
        peer_scope_label=peer_scope_label,
        baseline=baseline,
        actual_amount=actual_amount,
        score=score,
        percentile_25=low,
        percentile_75=high,
        evidence_confidence=evidence_confidence,
        peer_quality=peer_quality,
        similarity_rationale=similarity_rationale,
    )
    return not_flagged, None, not_flagged
