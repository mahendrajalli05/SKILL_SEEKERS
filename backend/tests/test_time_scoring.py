from __future__ import annotations

from datetime import date, timedelta

from app.engines.time.constants import FLAG_SCORE_THRESHOLD, HYBRID_CONFIDENCE_CAP, REAL_CONFIDENCE_CAP
from app.engines.time.schedule import compute_schedule_metrics
from app.engines.time.scoring import (
    completed_plan_score,
    evidence_confidence,
    is_time_anomaly,
    ongoing_mismatch_score,
    overdue_score,
)
from app.engines.time.types import TimeMode, TimePeerRecord
from app.engines.cost.work_type import derive_work_type

TANKS = "NA - Construction of water tanks"
AS_OF = date(2024, 6, 30)


def _record(
    project_id: int,
    *,
    planned_start: date | None = date(2024, 1, 1),
    planned_end: date | None = date(2024, 4, 10),
    actual_start: date | None = date(2024, 1, 1),
    actual_end: date | None = date(2024, 4, 10),
    progress: int | None = 100,
    as_of: date | None = AS_OF,
    mode: TimeMode = TimeMode.HYBRID_TEST,
) -> TimePeerRecord:
    return TimePeerRecord(
        project_id=project_id,
        internal_project_id=f"internal:time:{project_id}",
        constituency="KURNOOL",
        category="Normal/Others",
        state="Andhra Pradesh",
        work_description=TANKS,
        derived_work_type=derive_work_type(TANKS),
        status="Completed",
        lifecycle_stage="COMPLETED",
        recommended_date=date(2023, 6, 1),
        time_mode=mode,
        planned_start_date=planned_start,
        planned_completion_date=planned_end,
        actual_start_date=actual_start,
        actual_completion_date=actual_end,
        physical_progress_percent=progress,
        as_of_date=as_of,
        observation_date=date(2026, 9, 9),
    )


def test_completed_plan_score_zero_when_on_time() -> None:
    assert completed_plan_score(0, 100) == 0
    assert completed_plan_score(-10, 100) == 0
    assert not is_time_anomaly(0)


def test_completed_plan_score_maps_full_overtime_to_100() -> None:
    assert completed_plan_score(100, 100) == 100
    assert is_time_anomaly(100)


def test_completed_plan_score_is_monotonic() -> None:
    scores = [completed_plan_score(delay, 120) for delay in (0, 30, 60, 90, 120, 240)]
    assert scores == sorted(scores)
    assert scores[0] == 0
    assert scores[-1] == 100


def test_ongoing_progress_mismatch_70_20_is_flagged() -> None:
    score = ongoing_mismatch_score(70.0, 20.0)
    assert score >= FLAG_SCORE_THRESHOLD
    assert 60 <= score <= 70


def test_ongoing_aligned_progress_scores_zero() -> None:
    assert ongoing_mismatch_score(50.0, 50.0) == 0
    assert ongoing_mismatch_score(40.0, 70.0) == 0


def test_ongoing_mismatch_is_monotonic() -> None:
    scores = [ongoing_mismatch_score(t, 20.0) for t in (20.0, 40.0, 60.0, 80.0, 100.0)]
    assert scores == sorted(scores)
    assert scores[0] == 0


def test_overdue_completed_progress_does_not_score() -> None:
    assert overdue_score(80, 100, progress=100) == 0
    assert overdue_score(80, 100, progress=12) >= FLAG_SCORE_THRESHOLD


def test_closed_metrics_compute_slippage() -> None:
    record = _record(
        1,
        planned_start=date(2024, 1, 1),
        planned_end=date(2024, 4, 10),
        actual_start=date(2024, 1, 1),
        actual_end=date(2024, 7, 9),
    )
    metrics = compute_schedule_metrics(record)
    assert metrics.planned_duration_days == 100
    assert metrics.actual_duration_days == 190
    assert metrics.slippage_days == 90
    assert metrics.family.value == "closed"


def test_open_metrics_70_percent_time_20_progress() -> None:
    start = AS_OF - timedelta(days=70)
    record = TimePeerRecord(
        project_id=1,
        internal_project_id="internal:time:open",
        constituency="KURNOOL",
        category="Normal/Others",
        state="Andhra Pradesh",
        work_description=TANKS,
        derived_work_type=derive_work_type(TANKS),
        status="Ongoing",
        lifecycle_stage="ONGOING",
        recommended_date=date(2023, 6, 1),
        time_mode=TimeMode.HYBRID_TEST,
        planned_start_date=start,
        planned_completion_date=start + timedelta(days=100),
        actual_start_date=start,
        actual_completion_date=None,
        physical_progress_percent=20,
        as_of_date=AS_OF,
        observation_date=date(2026, 9, 9),
    )
    metrics = compute_schedule_metrics(record)
    assert metrics.family.value == "open"
    assert metrics.elapsed_duration_days == 70
    assert metrics.time_consumed_percent == 70.0
    assert metrics.physical_progress_percent == 20
    assert metrics.expected_progress_percent == 70.0
    assert metrics.progress_mismatch_points == 50.0


def test_real_mode_does_not_fabricate_duration() -> None:
    record = TimePeerRecord(
        project_id=1,
        internal_project_id="internal:real:1",
        constituency="KURNOOL",
        category="Normal/Others",
        state="Andhra Pradesh",
        work_description=TANKS,
        derived_work_type=derive_work_type(TANKS),
        status="Completed",
        lifecycle_stage="COMPLETED",
        recommended_date=date(2023, 6, 1),
        time_mode=TimeMode.REAL,
        observation_date=date(2026, 9, 9),
    )
    metrics = compute_schedule_metrics(record)
    assert metrics.planned_duration_days is None
    assert metrics.actual_duration_days is None
    assert metrics.elapsed_duration_days is None
    assert metrics.slippage_days is None
    assert metrics.physical_progress_percent is None
    assert metrics.recommendation_age_days is not None


def test_evidence_confidence_real_is_capped_and_separate() -> None:
    real = evidence_confidence(
        time_mode=TimeMode.REAL,
        valid_dates=True,
        sufficient_timing_evidence=False,
        has_recommended_date=True,
        scope_id="constituency_category_work_type",
        peer_count=20,
        peer_quality=90,
        has_planned_dates=False,
        has_actual_dates=False,
        has_progress=False,
    )
    hybrid = evidence_confidence(
        time_mode=TimeMode.HYBRID_TEST,
        valid_dates=True,
        sufficient_timing_evidence=True,
        has_recommended_date=True,
        scope_id="constituency_category_work_type",
        peer_count=8,
        peer_quality=90,
        has_planned_dates=True,
        has_actual_dates=True,
        has_progress=True,
    )
    invalid = evidence_confidence(
        time_mode=TimeMode.HYBRID_TEST,
        valid_dates=False,
        sufficient_timing_evidence=False,
        has_recommended_date=True,
        scope_id=None,
        peer_count=0,
        peer_quality=0,
        has_planned_dates=False,
        has_actual_dates=False,
        has_progress=False,
    )
    missing_rec = evidence_confidence(
        time_mode=TimeMode.REAL,
        valid_dates=True,
        sufficient_timing_evidence=False,
        has_recommended_date=False,
        scope_id=None,
        peer_count=0,
        peer_quality=0,
        has_planned_dates=False,
        has_actual_dates=False,
        has_progress=False,
    )
    assert 0 < real <= REAL_CONFIDENCE_CAP
    assert hybrid > real
    assert hybrid <= HYBRID_CONFIDENCE_CAP
    assert invalid == 0
    assert missing_rec == 0
