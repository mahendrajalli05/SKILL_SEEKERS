"""Schedule metrics from observed or HYBRID-TEST dates.

REAL mode never computes planned/actual duration from missing government dates.
HYBRID_TEST uses synthetic dates as a test clock only.
"""

from __future__ import annotations

from datetime import date

from app.engines.time.constants import REAL_OBSERVATION_DATE
from app.engines.time.dates import date_issue_codes, duration_days, recommendation_age_days
from app.engines.time.types import ScheduleFamily, ScheduleMetrics, TimeMode, TimePeerRecord


def classify_family(record: TimePeerRecord) -> ScheduleFamily:
    if record.time_mode == TimeMode.REAL:
        return ScheduleFamily.REAL_RECOMMENDATION_ONLY
    issues = date_issue_codes(
        planned_start=record.planned_start_date,
        planned_completion=record.planned_completion_date,
        actual_start=record.actual_start_date,
        actual_completion=record.actual_completion_date,
    )
    if issues:
        return ScheduleFamily.INVALID
    planned = duration_days(record.planned_start_date, record.planned_completion_date)
    if planned is None:
        return ScheduleFamily.NONE
    if planned <= 0:
        return ScheduleFamily.INVALID
    if record.actual_completion_date is not None:
        return ScheduleFamily.CLOSED
    return ScheduleFamily.OPEN


def _start_for_elapsed(record: TimePeerRecord) -> date | None:
    if record.actual_start_date is not None:
        return record.actual_start_date
    return record.planned_start_date


def compute_schedule_metrics(record: TimePeerRecord) -> ScheduleMetrics:
    family = classify_family(record)
    issues = date_issue_codes(
        planned_start=record.planned_start_date,
        planned_completion=record.planned_completion_date,
        actual_start=record.actual_start_date,
        actual_completion=record.actual_completion_date,
    )
    observation = record.observation_date or REAL_OBSERVATION_DATE
    rec_age = recommendation_age_days(record.recommended_date, observation)

    if record.time_mode == TimeMode.REAL:
        return ScheduleMetrics(
            family=family,
            date_issues=(),
            planned_duration_days=None,
            actual_duration_days=None,
            elapsed_duration_days=None,
            slippage_days=None,
            finish_delay_days=None,
            time_consumed_percent=None,
            physical_progress_percent=None,
            expected_progress_percent=None,
            progress_mismatch_points=None,
            recommendation_age_days=rec_age,
            start_date_used=None,
            as_of_date=None,
        )

    planned_duration = duration_days(record.planned_start_date, record.planned_completion_date)
    actual_duration = duration_days(record.actual_start_date, record.actual_completion_date)
    as_of = record.as_of_date
    start_used = _start_for_elapsed(record)
    elapsed = None
    if family == ScheduleFamily.OPEN and as_of is not None:
        elapsed = duration_days(start_used, as_of)
    finish_delay = duration_days(record.planned_completion_date, record.actual_completion_date)

    slippage: int | None = None
    time_consumed: float | None = None
    expected: float | None = None
    mismatch: float | None = None
    progress = record.physical_progress_percent

    if family == ScheduleFamily.CLOSED and planned_duration is not None and actual_duration is not None:
        slippage = actual_duration - planned_duration
        if finish_delay is not None:
            slippage = max(slippage, finish_delay)
    elif family == ScheduleFamily.OPEN and planned_duration is not None and planned_duration > 0:
        elapsed_for_ratio = 0 if elapsed is None else max(0, elapsed)
        time_consumed = round(100.0 * elapsed_for_ratio / planned_duration, 1)
        expected = round(min(100.0, time_consumed), 1)
        if progress is not None:
            mismatch = round(time_consumed - float(progress), 1)
        if as_of is not None and record.planned_completion_date is not None:
            overdue = duration_days(record.planned_completion_date, as_of)
            if overdue is not None and overdue > 0:
                slippage = overdue
            elif slippage is None:
                slippage = 0

    return ScheduleMetrics(
        family=family,
        date_issues=issues,
        planned_duration_days=planned_duration,
        actual_duration_days=actual_duration,
        elapsed_duration_days=elapsed,
        slippage_days=slippage,
        finish_delay_days=finish_delay,
        time_consumed_percent=time_consumed,
        physical_progress_percent=progress,
        expected_progress_percent=expected,
        progress_mismatch_points=mismatch,
        recommendation_age_days=rec_age,
        start_date_used=start_used,
        as_of_date=as_of,
    )
