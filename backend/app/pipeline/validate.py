"""Read-only validation of profiled extracts. Does not modify raw files."""

from __future__ import annotations

from dataclasses import dataclass

from app.pipeline.types import DatasetInventory, DatasetProfile


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    dataset_id: str | None = None
    severity: str = "warning"


def validate_dataset(dataset: DatasetProfile) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if dataset.n_rows == 0:
        issues.append(
            ValidationIssue("empty_rows", "Dataset has zero data rows.", dataset.dataset_id)
        )
    if dataset.n_columns == 0:
        issues.append(
            ValidationIssue("empty_columns", "Dataset has zero columns.", dataset.dataset_id, "error")
        )
    seen: set[str] = set()
    for name in dataset.columns:
        if name in seen:
            issues.append(
                ValidationIssue(
                    "duplicate_column_name",
                    f"Column name appears more than once: {name}",
                    dataset.dataset_id,
                    "error",
                )
            )
        seen.add(name)
    if dataset.provenance.missing_fields:
        issues.append(
            ValidationIssue(
                "incomplete_provenance",
                "Missing " + ", ".join(dataset.provenance.missing_fields),
                dataset.dataset_id,
            )
        )
    if dataset.duplicate_extra_row_count:
        issues.append(
            ValidationIssue(
                "duplicate_rows",
                f"{dataset.duplicate_extra_row_count} extra full-row duplicate(s) observed.",
                dataset.dataset_id,
            )
        )
    for col, extra in dataset.duplicate_id_extra_counts.items():
        if extra:
            issues.append(
                ValidationIssue(
                    "duplicate_ids",
                    f"{extra} extra duplicate value(s) in likely ID column `{col}`.",
                    dataset.dataset_id,
                )
            )
    return issues


def validate_inventory(inventory: DatasetInventory) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if inventory.empty_reason:
        issues.append(ValidationIssue("empty_raw", inventory.empty_reason, severity="info"))
    for dataset in inventory.datasets:
        issues.extend(validate_dataset(dataset))
    return issues
