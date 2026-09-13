from __future__ import annotations

from datetime import date

from app.engines.time.dates import (
    date_issue_codes,
    duration_days,
    has_invalid_date_order,
    parse_iso_date,
    recommendation_age_days,
)


def test_parse_iso_date() -> None:
    assert parse_iso_date("2024-06-30") == date(2024, 6, 30)
    assert parse_iso_date("2024-06-30T00:00:00") == date(2024, 6, 30)
    assert parse_iso_date("") is None
    assert parse_iso_date("not-a-date") is None


def test_duration_days_and_negative() -> None:
    start = date(2024, 1, 1)
    end = date(2024, 4, 10)
    assert duration_days(start, end) == 100
    assert duration_days(end, start) == -100
    assert duration_days(start, None) is None
    assert duration_days(None, end) is None


def test_completion_before_start_is_invalid() -> None:
    start = date(2024, 3, 1)
    completion = date(2024, 2, 1)
    assert has_invalid_date_order(actual_start=start, actual_completion=completion)
    codes = date_issue_codes(actual_start=start, actual_completion=completion)
    assert "completion_before_start" in codes
    assert "negative_actual_duration" in codes


def test_negative_planned_duration_is_invalid() -> None:
    codes = date_issue_codes(
        planned_start=date(2024, 6, 1),
        planned_completion=date(2024, 5, 1),
    )
    assert "planned_completion_before_planned_start" in codes
    assert "negative_planned_duration" in codes


def test_valid_dates_have_no_issues() -> None:
    codes = date_issue_codes(
        planned_start=date(2024, 1, 1),
        planned_completion=date(2024, 4, 1),
        actual_start=date(2024, 1, 5),
        actual_completion=date(2024, 4, 10),
    )
    assert codes == ()


def test_recommendation_age_is_not_duration() -> None:
    rec = date(2023, 6, 1)
    observation = date(2026, 9, 9)
    age = recommendation_age_days(rec, observation)
    assert age == (observation - rec).days
    assert age is not None
    assert age > 0
