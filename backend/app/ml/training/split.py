"""Deterministic temporal split. No random row shuffle."""

from __future__ import annotations

from datetime import date
from typing import Sequence

from app.ml.constants import TEST_FRACTION, TRAIN_FRACTION, VAL_FRACTION
from app.ml.types import CostRow, SplitAssignment


def temporal_split(
    rows: Sequence[CostRow],
    *,
    train_fraction: float = TRAIN_FRACTION,
    val_fraction: float = VAL_FRACTION,
    test_fraction: float = TEST_FRACTION,
) -> SplitAssignment:
    """Sort by recommended_date then internal_project_id. Earlier records train."""
    if abs(train_fraction + val_fraction + test_fraction - 1.0) > 1e-9:
        raise ValueError("Split fractions must sum to 1.")
    ordered = sorted(
        rows,
        key=lambda row: (
            row.recommended_date or date.min,
            row.internal_project_id,
        ),
    )
    n = len(ordered)
    n_train = int(n * train_fraction)
    n_val = int(n * val_fraction)
    if n >= 3:
        n_train = max(1, n_train)
        n_val = max(1, n_val)
        if n_train + n_val >= n:
            n_train = max(1, n - 2)
            n_val = 1
    n_test = n - n_train - n_val
    train = ordered[:n_train]
    val = ordered[n_train : n_train + n_val]
    test = ordered[n_train + n_val :]
    return SplitAssignment(
        train_ids=tuple(row.internal_project_id for row in train),
        validation_ids=tuple(row.internal_project_id for row in val),
        test_ids=tuple(row.internal_project_id for row in test),
        method="temporal_recommended_date_then_internal_project_id",
        train_count=len(train),
        validation_count=len(val),
        test_count=len(test),
    )
