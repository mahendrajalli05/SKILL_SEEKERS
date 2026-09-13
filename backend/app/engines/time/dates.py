"""Date parsing, duration, and order checks for Time Intelligence V1."""

from __future__ import annotations

from datetime import date


def parse_iso_date(value: object) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def duration_days(start: date | None, end: date | None) -> int | None:
    """Inclusive-open day count: (end - start).days. None if either date is missing."""
    if start is None or end is None:
        return None
    return (end - start).days


def recommendation_age_days(recommended: date | None, observation: date | None) -> int | None:
    """Days from recommendation to a documented observation clock. Not duration."""
    return duration_days(recommended, observation)


def date_issue_codes(
    *,
    planned_start: date | None = None,
    planned_completion: date | None = None,
    actual_start: date | None = None,
    actual_completion: date | None = None,
) -> tuple[str, ...]:
    """Return stable issue codes. Does not invent missing dates."""
    issues: list[str] = []
    planned = duration_days(planned_start, planned_completion)
    actual = duration_days(actual_start, actual_completion)
    if planned_start is not None and planned_completion is not None and planned_completion < planned_start:
        issues.append("planned_completion_before_planned_start")
    if actual_start is not None and actual_completion is not None and actual_completion < actual_start:
        issues.append("completion_before_start")
    if planned is not None and planned < 0:
        issues.append("negative_planned_duration")
    if actual is not None and actual < 0:
        issues.append("negative_actual_duration")
    # Deduplicate while preserving order.
    seen: set[str] = set()
    ordered: list[str] = []
    for code in issues:
        if code not in seen:
            seen.add(code)
            ordered.append(code)
    return tuple(ordered)


def has_invalid_date_order(
    *,
    planned_start: date | None = None,
    planned_completion: date | None = None,
    actual_start: date | None = None,
    actual_completion: date | None = None,
) -> bool:
    return bool(
        date_issue_codes(
            planned_start=planned_start,
            planned_completion=planned_completion,
            actual_start=actual_start,
            actual_completion=actual_completion,
        )
    )
