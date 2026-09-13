"""Load HYBRID-TEST execution/expenditure fields without scenario-label leakage.

Allowed operational-style inputs: synthetic dates and amounts needed by
sourced rules that cannot run on REAL fields alone.
Forbidden label columns are never stored on the enrichment object.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from app.engines.compliance.constants import (
    DEFAULT_HYBRID_AS_OF_DATE,
    FORBIDDEN_MODEL_INPUT_COLUMNS,
)
from app.engines.compliance.fields import as_date, as_number
from app.pipeline.synthetic import DEFAULT_OUTPUT_CSV

_ENRICHMENT_CACHE: dict[str, dict[str, "HybridComplianceFields"]] = {}


@dataclass(frozen=True)
class HybridComplianceFields:
    internal_project_id: str
    sanction_date: date | None
    planned_start_date: date | None
    planned_completion_date: date | None
    actual_start_date: date | None
    actual_completion_date: date | None
    sanctioned_amount: int | None
    expenditure_amount: int | None
    physical_progress_percent: int | None
    as_of_date: date


@dataclass(frozen=True)
class HeldOutComplianceLabel:
    scenario_type: str
    demo_case_id: str
    mixed_signals: str


def _opt_int(value: object) -> int | None:
    number = as_number(value)
    if value is None or (isinstance(value, str) and str(value).strip() == ""):
        return None
    if number is None:
        return None
    return int(number)


def _row_to_fields(row: dict[str, str]) -> HybridComplianceFields | None:
    internal_id = (row.get("internal_project_id") or "").strip()
    if not internal_id:
        return None
    as_of = as_date(row.get("synthetic_as_of_date")) or DEFAULT_HYBRID_AS_OF_DATE
    return HybridComplianceFields(
        internal_project_id=internal_id,
        sanction_date=as_date(row.get("sanction_date")),
        planned_start_date=as_date(row.get("planned_start_date")),
        planned_completion_date=as_date(row.get("planned_completion_date")),
        actual_start_date=as_date(row.get("actual_start_date")),
        actual_completion_date=as_date(row.get("actual_completion_date")),
        sanctioned_amount=_opt_int(row.get("sanctioned_amount")),
        expenditure_amount=_opt_int(row.get("expenditure_amount")),
        physical_progress_percent=_opt_int(row.get("physical_progress_percent")),
        as_of_date=as_of,
    )


def load_hybrid_compliance_fields(path: Path | None = None) -> dict[str, HybridComplianceFields]:
    """Load synthetic execution/amount fields only. Label columns are ignored."""
    import csv

    csv_path = path or DEFAULT_OUTPUT_CSV
    key = str(csv_path.resolve()) if csv_path.exists() else str(csv_path)
    if key in _ENRICHMENT_CACHE:
        return _ENRICHMENT_CACHE[key]
    records: dict[str, HybridComplianceFields] = {}
    if not csv_path.is_file():
        _ENRICHMENT_CACHE[key] = records
        return records
    with csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            item = _row_to_fields(row)
            if item is None:
                continue
            records[item.internal_project_id] = item
    _ENRICHMENT_CACHE[key] = records
    return records


def load_held_out_compliance_labels(path: Path | None = None) -> dict[str, HeldOutComplianceLabel]:
    """Post-scoring evaluation labels only. Never passed into assess_compliance."""
    import csv

    csv_path = path or DEFAULT_OUTPUT_CSV
    labels: dict[str, HeldOutComplianceLabel] = {}
    if not csv_path.is_file():
        return labels
    with csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            internal_id = (row.get("internal_project_id") or "").strip()
            if not internal_id:
                continue
            labels[internal_id] = HeldOutComplianceLabel(
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


def clear_hybrid_cache() -> None:
    _ENRICHMENT_CACHE.clear()
