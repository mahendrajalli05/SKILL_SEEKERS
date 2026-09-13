"""Load HYBRID GPS for overlap tests without scenario-label leakage.

Allowed operational-style inputs: latitude, longitude.
Forbidden label columns are never stored on the GPS object.
``overlap_group_id`` is loaded only as a held-out evaluation label.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.engines.overlap.constants import FORBIDDEN_MODEL_INPUT_COLUMNS
from app.pipeline.synthetic import DEFAULT_OUTPUT_CSV

_GPS_CACHE: dict[str, dict[str, "HybridGps"]] = {}


@dataclass(frozen=True)
class HybridGps:
    internal_project_id: str
    latitude: float | None
    longitude: float | None


@dataclass(frozen=True)
class HeldOutOverlapLabel:
    scenario_type: str
    demo_case_id: str
    mixed_signals: str
    overlap_group_id: str


def _opt_float(value: object) -> float | None:
    text = str(value or "").strip()
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _row_to_gps(row: dict[str, str]) -> HybridGps | None:
    internal_id = (row.get("internal_project_id") or "").strip()
    if not internal_id:
        return None
    return HybridGps(
        internal_project_id=internal_id,
        latitude=_opt_float(row.get("latitude")),
        longitude=_opt_float(row.get("longitude")),
    )


def load_hybrid_gps(path: Path | None = None) -> dict[str, HybridGps]:
    """Load synthetic coordinates only. Label columns are ignored."""
    import csv

    csv_path = path or DEFAULT_OUTPUT_CSV
    key = str(csv_path.resolve()) if csv_path.exists() else str(csv_path)
    if key in _GPS_CACHE:
        return _GPS_CACHE[key]
    gps: dict[str, HybridGps] = {}
    if not csv_path.is_file():
        _GPS_CACHE[key] = gps
        return gps
    with csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            item = _row_to_gps(row)
            if item is None:
                continue
            gps[item.internal_project_id] = item
    _GPS_CACHE[key] = gps
    return gps


def load_held_out_overlap_labels(path: Path | None = None) -> dict[str, HeldOutOverlapLabel]:
    """Post-scoring evaluation labels only. Never passed into scoring."""
    import csv

    csv_path = path or DEFAULT_OUTPUT_CSV
    labels: dict[str, HeldOutOverlapLabel] = {}
    if not csv_path.is_file():
        return labels
    with csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            internal_id = (row.get("internal_project_id") or "").strip()
            if not internal_id:
                continue
            labels[internal_id] = HeldOutOverlapLabel(
                scenario_type=(row.get("scenario_type") or "").strip(),
                demo_case_id=(row.get("demo_case_id") or "").strip(),
                mixed_signals=(row.get("mixed_signals") or "").strip(),
                overlap_group_id=(row.get("overlap_group_id") or "").strip(),
            )
    return labels


def assert_no_label_fields(obj: object) -> None:
    names = set(getattr(obj, "__dataclass_fields__", {}) or {})
    leaked = names.intersection(FORBIDDEN_MODEL_INPUT_COLUMNS)
    if leaked:
        raise RuntimeError(f"Forbidden label fields present: {sorted(leaked)}")


def clear_gps_cache() -> None:
    _GPS_CACHE.clear()
