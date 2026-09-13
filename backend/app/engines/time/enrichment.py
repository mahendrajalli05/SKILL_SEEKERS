"""Load HYBRID-TEST schedule fields without scenario-label leakage.

Allowed operational-style inputs: synthetic dates and physical progress.
`synthetic_as_of_date` is used only as a clock parameter.
Forbidden label columns are never stored on the schedule object.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from app.engines.time.constants import (
    DEFAULT_HYBRID_AS_OF_DATE,
    FORBIDDEN_MODEL_INPUT_COLUMNS,
)
from app.engines.time.dates import parse_iso_date
from app.pipeline.synthetic import DEFAULT_OUTPUT_CSV

_SCHEDULE_CACHE: dict[str, dict[str, "HybridSchedule"]] = {}


@dataclass(frozen=True)
class HybridSchedule:
    internal_project_id: str
    planned_start_date: date | None
    planned_completion_date: date | None
    actual_start_date: date | None
    actual_completion_date: date | None
    physical_progress_percent: int | None
    as_of_date: date


@dataclass(frozen=True)
class HeldOutTimeLabel:
    scenario_type: str
    demo_case_id: str
    mixed_signals: str


def _opt_int(value: object) -> int | None:
    text = str(value or "").strip()
    if text == "":
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def _row_to_schedule(row: dict[str, str]) -> HybridSchedule | None:
    internal_id = (row.get("internal_project_id") or "").strip()
    if not internal_id:
        return None
    as_of = parse_iso_date(row.get("synthetic_as_of_date")) or DEFAULT_HYBRID_AS_OF_DATE
    return HybridSchedule(
        internal_project_id=internal_id,
        planned_start_date=parse_iso_date(row.get("planned_start_date")),
        planned_completion_date=parse_iso_date(row.get("planned_completion_date")),
        actual_start_date=parse_iso_date(row.get("actual_start_date")),
        actual_completion_date=parse_iso_date(row.get("actual_completion_date")),
        physical_progress_percent=_opt_int(row.get("physical_progress_percent")),
        as_of_date=as_of,
    )


def load_hybrid_schedules(path: Path | None = None) -> dict[str, HybridSchedule]:
    """Load synthetic dates/progress only. Label columns are ignored."""
    import csv

    csv_path = path or DEFAULT_OUTPUT_CSV
    key = str(csv_path.resolve()) if csv_path.exists() else str(csv_path)
    if key in _SCHEDULE_CACHE:
        return _SCHEDULE_CACHE[key]
    schedules: dict[str, HybridSchedule] = {}
    if not csv_path.is_file():
        _SCHEDULE_CACHE[key] = schedules
        return schedules
    with csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            item = _row_to_schedule(row)
            if item is None:
                continue
            schedules[item.internal_project_id] = item
    _SCHEDULE_CACHE[key] = schedules
    return schedules


def load_held_out_time_labels(path: Path | None = None) -> dict[str, HeldOutTimeLabel]:
    """Post-scoring evaluation labels only. Never passed into assess_time."""
    import csv

    csv_path = path or DEFAULT_OUTPUT_CSV
    labels: dict[str, HeldOutTimeLabel] = {}
    if not csv_path.is_file():
        return labels
    with csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            internal_id = (row.get("internal_project_id") or "").strip()
            if not internal_id:
                continue
            labels[internal_id] = HeldOutTimeLabel(
                scenario_type=(row.get("scenario_type") or "").strip(),
                demo_case_id=(row.get("demo_case_id") or "").strip(),
                mixed_signals=(row.get("mixed_signals") or "").strip(),
            )
    return labels


def assert_no_label_fields(obj: object) -> None:
    names = set(getattr(obj, "__dataclass_fields__", {}) or {})
    leaked = names.intersection(FORBIDDEN_MODEL_INPUT_COLUMNS)
    if leaked:
        raise RuntimeError(f"Forbidden label fields present: {sorted(leaked)}")


def clear_schedule_cache() -> None:
    _SCHEDULE_CACHE.clear()
