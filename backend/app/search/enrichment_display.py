"""Display-only loader for existing HYBRID synthetic enrichment.

Does not feed intelligence engines. Does not modify ``data/raw/`` or real
project rows. Scenario/demo labels are not returned to the officer UI.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from app.pipeline.synthetic import DEFAULT_OUTPUT_CSV

SYNTHETIC_FIELD_DISCLAIMER = (
    "SYNTHETIC prototype enrichment. Not an official MPLADS field."
)

_DISPLAY_CACHE: dict[str, dict[str, "SyntheticEnrichmentDisplay"]] = {}


def _blank(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _opt_int(value: object) -> int | None:
    text = str(value or "").strip()
    if text == "":
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def _opt_float(value: object) -> float | None:
    text = str(value or "").strip()
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None


@dataclass(frozen=True)
class SyntheticEnrichmentDisplay:
    internal_project_id: str
    implementing_district: str | None
    implementing_agency: str | None
    vendor_name: str | None
    sanction_date: str | None
    planned_start_date: str | None
    planned_completion_date: str | None
    actual_start_date: str | None
    actual_completion_date: str | None
    expenditure_amount: int | None
    latitude: float | None
    longitude: float | None
    physical_progress_percent: int | None
    milestone_number: int | None
    milestone_amount: int | None
    milestone_total_amount: int | None

    def as_payload(self) -> dict[str, object]:
        return {
            "label": "SYNTHETIC",
            "disclaimer": SYNTHETIC_FIELD_DISCLAIMER,
            "implementing_district": self.implementing_district,
            "implementing_agency": self.implementing_agency,
            "vendor_name": self.vendor_name,
            "sanction_date": self.sanction_date,
            "start_date": self.actual_start_date or self.planned_start_date,
            "planned_start_date": self.planned_start_date,
            "planned_completion_date": self.planned_completion_date,
            "completion_date": self.actual_completion_date or self.planned_completion_date,
            "actual_start_date": self.actual_start_date,
            "actual_completion_date": self.actual_completion_date,
            "expenditure": self.expenditure_amount,
            "gps_latitude": self.latitude,
            "gps_longitude": self.longitude,
            "physical_progress_percent": self.physical_progress_percent,
            "milestones": {
                "number": self.milestone_number,
                "amount": self.milestone_amount,
                "total_amount": self.milestone_total_amount,
            },
        }


def _row_to_display(row: dict[str, str]) -> SyntheticEnrichmentDisplay | None:
    internal_id = (row.get("internal_project_id") or "").strip()
    if not internal_id:
        return None
    return SyntheticEnrichmentDisplay(
        internal_project_id=internal_id,
        implementing_district=_blank(row.get("implementing_district")),
        implementing_agency=_blank(row.get("implementing_agency")),
        vendor_name=_blank(row.get("vendor_name")),
        sanction_date=_blank(row.get("sanction_date")),
        planned_start_date=_blank(row.get("planned_start_date")),
        planned_completion_date=_blank(row.get("planned_completion_date")),
        actual_start_date=_blank(row.get("actual_start_date")),
        actual_completion_date=_blank(row.get("actual_completion_date")),
        expenditure_amount=_opt_int(row.get("expenditure_amount")),
        latitude=_opt_float(row.get("latitude")),
        longitude=_opt_float(row.get("longitude")),
        physical_progress_percent=_opt_int(row.get("physical_progress_percent")),
        milestone_number=_opt_int(row.get("milestone_number")),
        milestone_amount=_opt_int(row.get("milestone_amount")),
        milestone_total_amount=_opt_int(row.get("milestone_total_amount")),
    )


def load_enrichment_display(path: Path | None = None) -> dict[str, SyntheticEnrichmentDisplay]:
    csv_path = path or DEFAULT_OUTPUT_CSV
    key = str(csv_path.resolve()) if csv_path.exists() else str(csv_path)
    cached = _DISPLAY_CACHE.get(key)
    if cached is not None:
        return cached
    records: dict[str, SyntheticEnrichmentDisplay] = {}
    if csv_path.is_file():
        with csv_path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                item = _row_to_display(row)
                if item is not None:
                    records[item.internal_project_id] = item
    _DISPLAY_CACHE[key] = records
    return records


def enrichment_for(internal_project_id: str, path: Path | None = None) -> SyntheticEnrichmentDisplay | None:
    if not internal_project_id:
        return None
    return load_enrichment_display(path).get(internal_project_id)


def reset_enrichment_display_cache() -> None:
    _DISPLAY_CACHE.clear()
