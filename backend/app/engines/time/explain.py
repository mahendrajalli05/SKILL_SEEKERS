"""Factual Time Intelligence explanations.

Supports WHY FLAGGED, WHY NOT FLAGGED, and INCONCLUSIVE / INSUFFICIENT EVIDENCE.
Never uses legal-fraud language. HYBRID outputs are labelled HYBRID/TEST.
"""

from __future__ import annotations

from datetime import date

from app.engines.time.constants import (
    CAUSE_NOT_ESTABLISHED,
    FLAG_SCORE_THRESHOLD,
    HYBRID_TEST_NOTE,
    LINEAR_PROGRESS_NOTE,
    REAL_LIMITATION_NOTE,
    SIGNAL_SEPARATION_NOTE,
)
from app.engines.time.types import TimeAssessmentOutcome, TimeMode


def _iso(value: date | None) -> str:
    return value.isoformat() if value is not None else "unavailable"


def _num(value: float | int | None) -> str:
    if value is None:
        return "unavailable"
    if isinstance(value, int) or (isinstance(value, float) and value.is_integer()):
        return str(int(value))
    return f"{value:.1f}"


def invalid_dates_explanation(
    *,
    date_issues: tuple[str, ...],
    evidence_confidence: int,
    time_mode: TimeMode,
) -> str:
    codes = ", ".join(date_issues) if date_issues else "invalid date order"
    hybrid = f" {HYBRID_TEST_NOTE}" if time_mode == TimeMode.HYBRID_TEST else ""
    return (
        "Time Anomaly was not assessed: planned or actual dates are internally "
        f"inconsistent ({codes}). Negative duration and completion-before-start "
        f"are not scored. Evidence Confidence is {evidence_confidence}. "
        f"Investigation Priority is not assigned by this engine. "
        f"{SIGNAL_SEPARATION_NOTE}{hybrid}"
    )


def real_insufficient_explanation(
    *,
    recommended_date: date | None,
    observation_date: date | None,
    recommendation_age_days: int | None,
    observed_status: str,
    peer_count: int,
    peer_scope_label: str | None,
    evidence_confidence: int,
    constituency_exclusion_reason: str | None = None,
) -> str:
    geography_note = f" {constituency_exclusion_reason}" if constituency_exclusion_reason else ""
    peer_note = ""
    if peer_scope_label and peer_count:
        peer_note = (
            f" Same-status vintage context uses {peer_count} comparable works "
            f"in the {peer_scope_label}."
        )
    elif peer_count == 0:
        peer_note = " No same-status comparable works were available after constituency-first selection."
    return (
        "INCONCLUSIVE / INSUFFICIENT EVIDENCE for schedule or delay. "
        f"{REAL_LIMITATION_NOTE} Observed recommended date is {_iso(recommended_date)} "
        f"({_num(recommendation_age_days)} days before the snapshot observation clock "
        f"{_iso(observation_date)}). Observed status is "
        f"{observed_status or '(blank)'}.{peer_note}{geography_note} "
        "Recommendation vintage is not execution duration and is not scored as "
        f"Time Anomaly. Evidence Confidence is {evidence_confidence}. "
        f"Investigation Priority is not assigned by this engine. {SIGNAL_SEPARATION_NOTE}"
    )


def hybrid_no_schedule_explanation(*, evidence_confidence: int) -> str:
    return (
        "INCONCLUSIVE / INSUFFICIENT EVIDENCE: this HYBRID/TEST row has no usable "
        "planned start/completion dates, so schedule slippage cannot be measured. "
        f"Evidence Confidence is {evidence_confidence}. "
        f"Investigation Priority is not assigned by this engine. "
        f"{HYBRID_TEST_NOTE} {SIGNAL_SEPARATION_NOTE}"
    )


def why_flagged_closed(
    *,
    planned_duration_days: int,
    actual_duration_days: int,
    slippage_days: int,
    score: int,
    evidence_confidence: int,
    peer_count: int,
    peer_scope_label: str | None,
    delay_context_note: str,
) -> str:
    peer_bit = ""
    if peer_scope_label and peer_count:
        peer_bit = f" Peer comparison used {peer_count} comparable works in the {peer_scope_label}."
    return (
        f"{HYBRID_TEST_NOTE} Planned duration is {_num(planned_duration_days)} days; "
        f"actual duration is {_num(actual_duration_days)} days; schedule slippage is "
        f"{_num(slippage_days)} days. Time Anomaly score is {score} "
        f"(review flag at {FLAG_SCORE_THRESHOLD} on the 0-100 mapping). "
        f"{delay_context_note}{peer_bit} Evidence Confidence is {evidence_confidence}. "
        f"This Time Anomaly signal may inform later Investigation Priority. "
        f"{SIGNAL_SEPARATION_NOTE}"
    )


def why_not_flagged_closed(
    *,
    planned_duration_days: int,
    actual_duration_days: int,
    slippage_days: int | None,
    score: int,
    evidence_confidence: int,
    peer_count: int,
    peer_scope_label: str | None,
    delay_detected: bool,
    delay_context_note: str,
) -> str:
    peer_bit = ""
    if peer_scope_label and peer_count:
        peer_bit = f" Peer comparison used {peer_count} comparable works in the {peer_scope_label}."
    delay_bit = (
        f" {delay_context_note}"
        if delay_detected
        else " No delay versus the planned duration was measured."
    )
    return (
        f"{HYBRID_TEST_NOTE} Planned duration is {_num(planned_duration_days)} days; "
        f"actual duration is {_num(actual_duration_days)} days; schedule slippage is "
        f"{_num(slippage_days)} days. Time Anomaly score is {score}, below the review "
        f"flag of {FLAG_SCORE_THRESHOLD}. Not flagged as a Time Anomaly.{delay_bit}"
        f"{peer_bit} Evidence Confidence is {evidence_confidence}. "
        f"Investigation Priority is not assigned by this engine. {SIGNAL_SEPARATION_NOTE}"
    )


def why_flagged_open(
    *,
    elapsed_duration_days: int | None,
    planned_duration_days: int,
    time_consumed_percent: float | None,
    physical_progress_percent: int | None,
    expected_progress_percent: float | None,
    score: int,
    evidence_confidence: int,
    peer_count: int,
    peer_scope_label: str | None,
    delay_context_note: str,
) -> str:
    peer_bit = ""
    if peer_scope_label and peer_count:
        peer_bit = f" Peer comparison used {peer_count} comparable works in the {peer_scope_label}."
    return (
        f"{HYBRID_TEST_NOTE} Elapsed duration is {_num(elapsed_duration_days)} days of "
        f"{_num(planned_duration_days)} planned days "
        f"({_num(time_consumed_percent)}% of planned time consumed) with physical "
        f"progress {_num(physical_progress_percent)}% versus linear expected progress "
        f"{_num(expected_progress_percent)}%. {LINEAR_PROGRESS_NOTE} "
        f"Time Anomaly score is {score} (review flag at {FLAG_SCORE_THRESHOLD}). "
        f"{delay_context_note}{peer_bit} Evidence Confidence is {evidence_confidence}. "
        f"This Time Anomaly signal may inform later Investigation Priority. "
        f"{SIGNAL_SEPARATION_NOTE}"
    )


def why_not_flagged_open(
    *,
    elapsed_duration_days: int | None,
    planned_duration_days: int,
    time_consumed_percent: float | None,
    physical_progress_percent: int | None,
    expected_progress_percent: float | None,
    score: int,
    evidence_confidence: int,
    peer_count: int,
    peer_scope_label: str | None,
    delay_detected: bool,
    delay_context_note: str,
) -> str:
    peer_bit = ""
    if peer_scope_label and peer_count:
        peer_bit = f" Peer comparison used {peer_count} comparable works in the {peer_scope_label}."
    delay_bit = f" {delay_context_note}" if delay_detected else " Schedule and progress are aligned on the linear test mapping."
    return (
        f"{HYBRID_TEST_NOTE} Elapsed duration is {_num(elapsed_duration_days)} days of "
        f"{_num(planned_duration_days)} planned days "
        f"({_num(time_consumed_percent)}% of planned time consumed) with physical "
        f"progress {_num(physical_progress_percent)}% versus linear expected progress "
        f"{_num(expected_progress_percent)}%. {LINEAR_PROGRESS_NOTE} "
        f"Time Anomaly score is {score}, below the review flag of {FLAG_SCORE_THRESHOLD}. "
        f"Not flagged as a Time Anomaly.{delay_bit}{peer_bit} "
        f"Evidence Confidence is {evidence_confidence}. "
        f"Investigation Priority is not assigned by this engine. {SIGNAL_SEPARATION_NOTE}"
    )


def explanation_for(
    outcome: TimeAssessmentOutcome,
    *,
    time_mode: TimeMode,
    date_issues: tuple[str, ...] = (),
    recommended_date: date | None = None,
    observation_date: date | None = None,
    recommendation_age_days: int | None = None,
    observed_status: str = "",
    planned_duration_days: int | None = None,
    actual_duration_days: int | None = None,
    elapsed_duration_days: int | None = None,
    slippage_days: int | None = None,
    time_consumed_percent: float | None = None,
    physical_progress_percent: int | None = None,
    expected_progress_percent: float | None = None,
    score: int | None = None,
    evidence_confidence: int = 0,
    peer_count: int = 0,
    peer_scope_label: str | None = None,
    delay_detected: bool = False,
    delay_context_note: str = "",
    constituency_exclusion_reason: str | None = None,
    schedule_family: str = "",
) -> tuple[str, str | None, str | None]:
    if outcome == TimeAssessmentOutcome.INVALID_DATES:
        text = invalid_dates_explanation(
            date_issues=date_issues,
            evidence_confidence=evidence_confidence,
            time_mode=time_mode,
        )
        return text, None, text
    if outcome == TimeAssessmentOutcome.INSUFFICIENT_EVIDENCE:
        if time_mode == TimeMode.REAL:
            text = real_insufficient_explanation(
                recommended_date=recommended_date,
                observation_date=observation_date,
                recommendation_age_days=recommendation_age_days,
                observed_status=observed_status,
                peer_count=peer_count,
                peer_scope_label=peer_scope_label,
                evidence_confidence=evidence_confidence,
                constituency_exclusion_reason=constituency_exclusion_reason,
            )
        else:
            text = hybrid_no_schedule_explanation(evidence_confidence=evidence_confidence)
        return text, None, text

    assert score is not None
    context = delay_context_note or (CAUSE_NOT_ESTABLISHED if delay_detected else "")
    if schedule_family == "closed":
        assert planned_duration_days is not None
        assert actual_duration_days is not None
        if outcome == TimeAssessmentOutcome.TIME_ANOMALY:
            flagged = why_flagged_closed(
                planned_duration_days=planned_duration_days,
                actual_duration_days=actual_duration_days,
                slippage_days=slippage_days or 0,
                score=score,
                evidence_confidence=evidence_confidence,
                peer_count=peer_count,
                peer_scope_label=peer_scope_label,
                delay_context_note=context,
            )
            return flagged, flagged, None
        not_flagged = why_not_flagged_closed(
            planned_duration_days=planned_duration_days,
            actual_duration_days=actual_duration_days,
            slippage_days=slippage_days,
            score=score,
            evidence_confidence=evidence_confidence,
            peer_count=peer_count,
            peer_scope_label=peer_scope_label,
            delay_detected=delay_detected,
            delay_context_note=context,
        )
        return not_flagged, None, not_flagged

    assert planned_duration_days is not None
    if outcome == TimeAssessmentOutcome.TIME_ANOMALY:
        flagged = why_flagged_open(
            elapsed_duration_days=elapsed_duration_days,
            planned_duration_days=planned_duration_days,
            time_consumed_percent=time_consumed_percent,
            physical_progress_percent=physical_progress_percent,
            expected_progress_percent=expected_progress_percent,
            score=score,
            evidence_confidence=evidence_confidence,
            peer_count=peer_count,
            peer_scope_label=peer_scope_label,
            delay_context_note=context,
        )
        return flagged, flagged, None
    not_flagged = why_not_flagged_open(
        elapsed_duration_days=elapsed_duration_days,
        planned_duration_days=planned_duration_days,
        time_consumed_percent=time_consumed_percent,
        physical_progress_percent=physical_progress_percent,
        expected_progress_percent=expected_progress_percent,
        score=score,
        evidence_confidence=evidence_confidence,
        peer_count=peer_count,
        peer_scope_label=peer_scope_label,
        delay_detected=delay_detected,
        delay_context_note=context,
    )
    return not_flagged, None, not_flagged
