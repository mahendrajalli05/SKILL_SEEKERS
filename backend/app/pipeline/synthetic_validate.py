"""Validate the SYNTHETIC HYBRID enrichment layer.

Does not modify real extracts. Distinguishes generator bugs (hard constraints)
from intended prototype anomaly signals.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from app.pipeline.synthetic import (
    DEFAULT_CLEANED_CSV,
    DEFAULT_OUTPUT_CSV,
    ENRICHMENT_SOURCE,
    OUTPUT_COLUMNS,
    RECORD_MODE,
    SYNTHETIC_ID_PREFIX,
    TARGET_RECORD_COUNT,
    parse_int,
    parse_iso_date,
    read_real_projects,
)

HARD_DATE_PAIRS = (
    ("real_recommended_date", "sanction_date"),
    ("sanction_date", "planned_start_date"),
    ("planned_start_date", "planned_completion_date"),
    ("actual_start_date", "actual_completion_date"),
)

NORMAL_SCENARIOS = frozenset({"NORMAL", "DEMO_CLEAN"})
COST_SIGNAL_SCENARIOS = frozenset({"COST_ANOMALY", "DEMO_OVERBILL"})
TIME_SIGNAL_SCENARIOS = frozenset({"TIME_ANOMALY", "DEMO_STUCK"})
GHOST_SIGNAL_SCENARIOS = frozenset({"EVIDENCE_GHOST", "DEMO_GHOST"})


@dataclass
class ValidationIssue:
    code: str
    message: str
    count: int = 1
    severity: str = "error"


@dataclass
class ValidationReport:
    ok: bool
    total_records: int
    unique_internal_project_ids: int
    unique_synthetic_record_ids: int
    duplicate_synthetic_ids: int
    scenario_counts: dict[str, int]
    missing_counts: dict[str, int]
    hard_violations: list[ValidationIssue] = field(default_factory=list)
    intended_anomaly_counts: dict[str, int] = field(default_factory=dict)
    demo_cases: dict[str, str] = field(default_factory=dict)
    samples: list[dict[str, Any]] = field(default_factory=list)

    @property
    def hard_violation_count(self) -> int:
        return sum(item.count for item in self.hard_violations)


def _text(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def _has(value: object) -> bool:
    return _text(value) != ""


def _progress(value: object) -> int | None:
    parsed = parse_int(value)
    return parsed


def _scenario_has_cost(row: pd.Series) -> bool:
    scenario = _text(row.get("scenario_type"))
    mixed = _text(row.get("mixed_signals"))
    return scenario in COST_SIGNAL_SCENARIOS or "COST_ANOMALY" in mixed


def _scenario_has_time(row: pd.Series) -> bool:
    scenario = _text(row.get("scenario_type"))
    mixed = _text(row.get("mixed_signals"))
    return scenario in TIME_SIGNAL_SCENARIOS or "TIME_ANOMALY" in mixed


def _scenario_has_ghost(row: pd.Series) -> bool:
    scenario = _text(row.get("scenario_type"))
    mixed = _text(row.get("mixed_signals"))
    return scenario in GHOST_SIGNAL_SCENARIOS or "EVIDENCE_GHOST" in mixed


def _scenario_is_normal(row: pd.Series) -> bool:
    return _text(row.get("scenario_type")) in NORMAL_SCENARIOS


def missing_counts(frame: pd.DataFrame) -> dict[str, int]:
    counts: dict[str, int] = {}
    for column in frame.columns:
        counts[column] = int((frame[column].map(_text) == "").sum())
    return counts


def sample_rows(frame: pd.DataFrame, limit_each: int = 1) -> list[dict[str, Any]]:
    wanted = [
        "DEMO_CLEAN",
        "DEMO_OVERBILL",
        "DEMO_STUCK",
        "DEMO_GHOST",
        "NORMAL",
        "COST_ANOMALY",
        "TIME_ANOMALY",
        "OVERLAP",
        "EVIDENCE_GHOST",
        "MIXED",
    ]
    samples: list[dict[str, Any]] = []
    show_cols = [
        "synthetic_record_id",
        "internal_project_id",
        "record_mode",
        "enrichment_source",
        "scenario_type",
        "demo_case_id",
        "mixed_signals",
        "real_state",
        "real_constituency",
        "real_status",
        "real_allocation_amount",
        "real_recommended_date",
        "implementing_district",
        "vendor_name",
        "sanction_date",
        "planned_start_date",
        "planned_completion_date",
        "actual_start_date",
        "actual_completion_date",
        "sanctioned_amount",
        "expenditure_amount",
        "latitude",
        "longitude",
        "physical_progress_percent",
        "milestone_number",
        "milestone_amount",
        "milestone_total_amount",
        "anomaly_notes",
    ]
    for scenario in wanted:
        subset = frame[frame["scenario_type"] == scenario]
        for _, row in subset.head(limit_each).iterrows():
            samples.append({col: row.get(col, "") for col in show_cols if col in frame.columns})
    return samples


def validate_enrichment(
    frame: pd.DataFrame,
    *,
    real_ids: set[str] | None = None,
    expected_n: int | None = TARGET_RECORD_COUNT,
) -> ValidationReport:
    issues: list[ValidationIssue] = []
    intended: dict[str, int] = defaultdict(int)

    if list(frame.columns) != OUTPUT_COLUMNS:
        missing = [name for name in OUTPUT_COLUMNS if name not in frame.columns]
        extra = [name for name in frame.columns if name not in OUTPUT_COLUMNS]
        if missing or extra:
            issues.append(
                ValidationIssue(
                    "column_mismatch",
                    f"Column mismatch missing={missing} extra={extra}",
                )
            )

    total = len(frame)
    synthetic_ids = frame["synthetic_record_id"].map(_text) if "synthetic_record_id" in frame.columns else pd.Series(dtype=str)
    internal_ids = frame["internal_project_id"].map(_text) if "internal_project_id" in frame.columns else pd.Series(dtype=str)
    unique_synthetic = int(synthetic_ids[synthetic_ids != ""].nunique()) if len(synthetic_ids) else 0
    unique_internal = int(internal_ids[internal_ids != ""].nunique()) if len(internal_ids) else 0
    duplicate_synthetic = int(len(synthetic_ids) - unique_synthetic)

    if expected_n is not None and total != expected_n:
        issues.append(
            ValidationIssue(
                "record_count",
                f"Expected {expected_n} records, found {total}",
            )
        )
    if unique_internal != total:
        issues.append(
            ValidationIssue(
                "duplicate_internal_project_id",
                f"Expected 1:1 real links; unique internal_project_id={unique_internal} of {total}",
                count=total - unique_internal,
            )
        )
    if duplicate_synthetic:
        issues.append(
            ValidationIssue(
                "duplicate_synthetic_record_id",
                f"{duplicate_synthetic} duplicate synthetic_record_id value(s)",
                count=duplicate_synthetic,
            )
        )

    if "record_mode" in frame.columns:
        bad_mode = int((frame["record_mode"].map(_text) != RECORD_MODE).sum())
        if bad_mode:
            issues.append(ValidationIssue("record_mode", f"{bad_mode} rows not {RECORD_MODE}", bad_mode))
    if "enrichment_source" in frame.columns:
        bad_src = int((frame["enrichment_source"].map(_text) != ENRICHMENT_SOURCE).sum())
        if bad_src:
            issues.append(
                ValidationIssue(
                    "enrichment_source",
                    f"{bad_src} rows not {ENRICHMENT_SOURCE}",
                    bad_src,
                )
            )

    if real_ids is not None and "internal_project_id" in frame.columns:
        unknown = [pid for pid in internal_ids if pid and pid not in real_ids]
        if unknown:
            issues.append(
                ValidationIssue(
                    "unknown_internal_project_id",
                    f"{len(unknown)} synthetic rows do not link to the real extract",
                    count=len(unknown),
                )
            )

    official_like = 0
    for value in synthetic_ids:
        text = value.lower()
        if not value.startswith(SYNTHETIC_ID_PREFIX) or "mplads" in text:
            official_like += 1
    if official_like:
        issues.append(
            ValidationIssue(
                "synthetic_id_shape",
                f"{official_like} synthetic_record_id values are not clearly synthetic",
                official_like,
            )
        )

    for column in ("implementing_district", "implementing_agency", "vendor_name"):
        if column not in frame.columns:
            continue
        unmarked = int(
            frame[column].map(lambda v: _has(v) and "SYNTHETIC" not in str(v).upper()).sum()
        )
        if unmarked:
            issues.append(
                ValidationIssue(
                    "unlabelled_synthetic_geo",
                    f"{unmarked} {column} values are not marked SYNTHETIC",
                    unmarked,
                )
            )

    date_violations = 0
    for left, right in HARD_DATE_PAIRS:
        if left not in frame.columns or right not in frame.columns:
            continue
        for _, row in frame.iterrows():
            left_d = parse_iso_date(row.get(left))
            right_d = parse_iso_date(row.get(right))
            if left_d and right_d and left_d > right_d:
                date_violations += 1
    if date_violations:
        issues.append(
            ValidationIssue(
                "date_order",
                f"{date_violations} date-order violations (recommended/sanction/planned/actual)",
                date_violations,
            )
        )

    progress_bad = 0
    completed_missing_end = 0
    ongoing_has_end = 0
    normal_overspend = 0
    normal_milestone_over = 0
    for _, row in frame.iterrows():
        progress = _progress(row.get("physical_progress_percent"))
        if progress is not None and not (0 <= progress <= 100):
            progress_bad += 1
        status = _text(row.get("real_status"))
        scenario = _text(row.get("scenario_type"))
        if status == "Completed" and _scenario_is_normal(row) and not _has(row.get("actual_completion_date")):
            completed_missing_end += 1
        if status == "Ongoing" and _scenario_is_normal(row) and _has(row.get("actual_completion_date")):
            ongoing_has_end += 1
        if scenario == "DEMO_STUCK" and _has(row.get("actual_completion_date")):
            ongoing_has_end += 1
        sanctioned = parse_int(row.get("sanctioned_amount"))
        expenditure = parse_int(row.get("expenditure_amount"))
        milestone_total = parse_int(row.get("milestone_total_amount"))
        if expenditure is not None and sanctioned is not None and expenditure > sanctioned:
            if _scenario_is_normal(row):
                normal_overspend += 1
            else:
                intended["expenditure_gt_sanctioned"] += 1
        if (
            milestone_total is not None
            and sanctioned is not None
            and milestone_total > sanctioned
        ):
            if _scenario_is_normal(row):
                normal_milestone_over += 1
            else:
                intended["milestone_total_gt_sanctioned"] += 1
        if _scenario_has_cost(row) and not (
            expenditure is not None and sanctioned is not None and expenditure > sanctioned
        ):
            intended["cost_signal_without_overspend"] += 1
        if _scenario_has_ghost(row) and _has(row.get("latitude")):
            lat = row.get("latitude")
            lon = row.get("longitude")
            try:
                lat_f = float(lat)
                lon_f = float(lon)
            except (TypeError, ValueError):
                lat_f = None
                lon_f = None
            if lat_f is not None and lon_f is not None and lon_f < 72:
                intended["ghost_implausible_gps"] += 1
        elif _scenario_has_ghost(row):
            intended["ghost_missing_gps"] += 1
        if _scenario_has_time(row):
            intended["time_anomaly_rows"] += 1

    if progress_bad:
        issues.append(
            ValidationIssue(
                "progress_range",
                f"{progress_bad} physical_progress_percent values outside 0-100",
                progress_bad,
            )
        )
    if completed_missing_end:
        issues.append(
            ValidationIssue(
                "completed_without_completion_date",
                f"{completed_missing_end} NORMAL completed rows lack actual_completion_date",
                completed_missing_end,
            )
        )
    if ongoing_has_end:
        issues.append(
            ValidationIssue(
                "ongoing_with_completion_date",
                f"{ongoing_has_end} NORMAL/DEMO_STUCK ongoing-style rows have actual_completion_date",
                ongoing_has_end,
            )
        )
    if normal_overspend:
        issues.append(
            ValidationIssue(
                "normal_overspend",
                f"{normal_overspend} NORMAL/DEMO_CLEAN rows have expenditure > sanctioned",
                normal_overspend,
            )
        )
    if normal_milestone_over:
        issues.append(
            ValidationIssue(
                "normal_milestone_over_sanction",
                f"{normal_milestone_over} NORMAL/DEMO_CLEAN rows have milestone total > sanctioned",
                normal_milestone_over,
            )
        )

    scenario_counts = dict(Counter(frame["scenario_type"].map(_text))) if "scenario_type" in frame.columns else {}
    demo_cases = {}
    if "demo_case_id" in frame.columns:
        for _, row in frame.iterrows():
            demo_id = _text(row.get("demo_case_id"))
            if demo_id:
                demo_cases[demo_id] = _text(row.get("internal_project_id"))
    for required in ("GHOST", "OVERBILL", "STUCK", "CLEAN"):
        if expected_n and expected_n >= 4 and required not in demo_cases:
            issues.append(
                ValidationIssue(
                    "missing_demo_case",
                    f"Controlled demo case {required} is missing",
                )
            )

    report = ValidationReport(
        ok=not issues,
        total_records=total,
        unique_internal_project_ids=unique_internal,
        unique_synthetic_record_ids=unique_synthetic,
        duplicate_synthetic_ids=duplicate_synthetic,
        scenario_counts=dict(sorted(scenario_counts.items())),
        missing_counts=missing_counts(frame),
        hard_violations=issues,
        intended_anomaly_counts=dict(sorted(intended.items())),
        demo_cases=demo_cases,
        samples=sample_rows(frame),
    )
    return report


def load_and_validate(
    csv_path: Path = DEFAULT_OUTPUT_CSV,
    real_csv: Path = DEFAULT_CLEANED_CSV,
    expected_n: int | None = TARGET_RECORD_COUNT,
) -> ValidationReport:
    frame = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    real_ids = set(read_real_projects(real_csv)["internal_project_id"])
    return validate_enrichment(frame, real_ids=real_ids, expected_n=expected_n)


def format_report(report: ValidationReport) -> str:
    lines = [
        "# SARVSAKSHI synthetic enrichment validation",
        "",
        "This report is for the SYNTHETIC HYBRID prototype layer. It is not a government dataset.",
        "",
        f"- ok: `{report.ok}`",
        f"- total synthetic records: **{report.total_records}**",
        f"- unique real internal_project_id values: **{report.unique_internal_project_ids}**",
        f"- unique synthetic_record_id values: **{report.unique_synthetic_record_ids}**",
        f"- duplicate synthetic IDs: **{report.duplicate_synthetic_ids}**",
        "",
        "## Scenario distribution",
        "",
    ]
    for name, count in report.scenario_counts.items():
        pct = (100.0 * count / report.total_records) if report.total_records else 0.0
        lines.append(f"- `{name}`: {count} ({pct:.2f}%)")
    lines.extend(["", "## Controlled demo cases", ""])
    if report.demo_cases:
        for key in ("GHOST", "OVERBILL", "STUCK", "CLEAN"):
            pid = report.demo_cases.get(key, "")
            lines.append(f"- `{key}`: `{pid}`")
    else:
        lines.append("- (none)")
    lines.extend(["", "## Missing values", ""])
    for column, count in report.missing_counts.items():
        if count:
            pct = 100.0 * count / report.total_records if report.total_records else 0.0
            lines.append(f"- `{column}`: {count} ({pct:.2f}%)")
    lines.extend(["", "## Hard constraint violations (generator bugs)", ""])
    if not report.hard_violations:
        lines.append("- none")
    else:
        for issue in report.hard_violations:
            lines.append(f"- `{issue.code}` ({issue.severity}): {issue.message}")
    lines.extend(
        [
            "",
            "## Intended prototype anomaly signals (not generator bugs)",
            "",
        ]
    )
    if not report.intended_anomaly_counts:
        lines.append("- none")
    else:
        for name, count in report.intended_anomaly_counts.items():
            lines.append(f"- `{name}`: {count}")
    lines.extend(["", "## Sample REAL + SYNTHETIC/HYBRID records", ""])
    for index, sample in enumerate(report.samples, start=1):
        lines.append(f"### Sample {index}: `{sample.get('scenario_type', '')}`")
        lines.append("")
        lines.append("```")
        lines.append(json.dumps(sample, indent=2, default=str))
        lines.append("```")
        lines.append("")
    return "\n".join(lines) + "\n"


def write_validation_report(report: ValidationReport, path: Path) -> None:
    from app.pipeline.synthetic import assert_synthetic_output_dir

    assert_synthetic_output_dir(path.parent)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(format_report(report), encoding="utf-8")
