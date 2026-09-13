from __future__ import annotations

from datetime import date

from app.engines.time.constants import CAUSE_NOT_ESTABLISHED, HYBRID_TEST_NOTE, REAL_LIMITATION_NOTE
from app.engines.time.explain import explanation_for
from app.engines.time.types import TimeAssessmentOutcome, TimeMode


def test_why_flagged_closed_uses_context_and_hybrid_label() -> None:
    text, why_flagged, why_not = explanation_for(
        TimeAssessmentOutcome.TIME_ANOMALY,
        time_mode=TimeMode.HYBRID_TEST,
        planned_duration_days=100,
        actual_duration_days=190,
        slippage_days=90,
        score=90,
        evidence_confidence=58,
        peer_count=8,
        peer_scope_label="same geographic constituency, same category, and similar work title",
        delay_detected=True,
        delay_context_note=CAUSE_NOT_ESTABLISHED,
        schedule_family="closed",
    )
    assert why_flagged is not None
    assert why_not is None
    assert HYBRID_TEST_NOTE in why_flagged
    assert "Planned duration is 100 days" in why_flagged
    assert "actual duration is 190 days" in why_flagged
    assert "schedule slippage is 90 days" in why_flagged
    assert CAUSE_NOT_ESTABLISHED in why_flagged
    assert "Time Anomaly score is 90" in why_flagged
    assert "Evidence Confidence is 58" in why_flagged
    assert "fraud" not in why_flagged.casefold()
    assert text == why_flagged


def test_why_not_flagged_normal_schedule() -> None:
    text, why_flagged, why_not = explanation_for(
        TimeAssessmentOutcome.WITHIN_SCHEDULE,
        time_mode=TimeMode.HYBRID_TEST,
        planned_duration_days=100,
        actual_duration_days=100,
        slippage_days=0,
        score=0,
        evidence_confidence=50,
        peer_count=8,
        peer_scope_label="same geographic constituency, same category, and similar work title",
        delay_detected=False,
        delay_context_note="No delay was detected from available timing evidence.",
        schedule_family="closed",
    )
    assert why_flagged is None
    assert why_not is not None
    assert "Not flagged as a Time Anomaly" in why_not
    assert "No delay versus the planned duration" in why_not
    assert "fraud" not in why_not.casefold()
    assert text == why_not


def test_why_flagged_open_progress_mismatch() -> None:
    text, why_flagged, why_not = explanation_for(
        TimeAssessmentOutcome.TIME_ANOMALY,
        time_mode=TimeMode.HYBRID_TEST,
        planned_duration_days=100,
        elapsed_duration_days=70,
        time_consumed_percent=70.0,
        physical_progress_percent=20,
        expected_progress_percent=70.0,
        score=62,
        evidence_confidence=48,
        delay_detected=True,
        delay_context_note=CAUSE_NOT_ESTABLISHED,
        schedule_family="open",
    )
    assert why_flagged is not None
    assert "70% of planned time consumed" in why_flagged
    assert "physical progress 20%" in why_flagged
    assert CAUSE_NOT_ESTABLISHED in why_flagged
    assert HYBRID_TEST_NOTE in why_flagged
    assert "actual MPLADS execution history" in why_flagged


def test_real_mode_explanation_is_inconclusive() -> None:
    text, why_flagged, why_not = explanation_for(
        TimeAssessmentOutcome.INSUFFICIENT_EVIDENCE,
        time_mode=TimeMode.REAL,
        recommended_date=date(2023, 6, 1),
        observation_date=date(2026, 9, 9),
        recommendation_age_days=1196,
        observed_status="Completed",
        evidence_confidence=12,
        peer_count=8,
        peer_scope_label="same geographic constituency and broader category",
    )
    assert why_flagged is None
    assert why_not == text
    assert "INCONCLUSIVE / INSUFFICIENT EVIDENCE" in text
    assert REAL_LIMITATION_NOTE in text
    assert "Duration is not fabricated" in text
    assert "fraud" not in text.casefold()


def test_invalid_dates_explanation() -> None:
    text, _why_flagged, why_not = explanation_for(
        TimeAssessmentOutcome.INVALID_DATES,
        time_mode=TimeMode.HYBRID_TEST,
        date_issues=("completion_before_start", "negative_actual_duration"),
        evidence_confidence=0,
    )
    assert "internally inconsistent" in text
    assert "completion_before_start" in text
    assert HYBRID_TEST_NOTE in text
    assert why_not == text
    assert "fraud" not in text.casefold()
