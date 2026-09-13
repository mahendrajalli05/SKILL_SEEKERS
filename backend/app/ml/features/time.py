"""HYBRID_TEST time features. Not trained on fabricated REAL execution dates."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Sequence

import numpy as np
from sklearn.preprocessing import StandardScaler

from app.ml.features.forbidden import assert_no_label_leakage

TIME_NUMERIC = (
    "planned_duration_days",
    "physical_progress_percent",
    "log_allocation",
    "rec_year",
)


@dataclass
class TimeRow:
    internal_project_id: str
    planned_duration_days: float | None
    physical_progress_percent: float | None
    allocation_amount: int | None
    recommended_date: date | None


@dataclass
class TimeFeaturePipeline:
    scaler_: StandardScaler | None = None
    medians_: dict[str, float] = field(default_factory=dict)
    feature_names_: list[str] = field(default_factory=list)

    def fit(self, rows: Sequence[TimeRow]) -> TimeFeaturePipeline:
        usable = [row for row in rows if _usable(row)]
        if len(usable) < 5:
            raise ValueError("HYBRID_TEST time training needs at least 5 rows with planned duration.")
        matrix = np.vstack([self._raw(row) for row in usable])
        self.medians_ = {
            TIME_NUMERIC[i]: float(np.median(matrix[:, i])) for i in range(len(TIME_NUMERIC))
        }
        self.scaler_ = StandardScaler()
        self.scaler_.fit(matrix)
        self.feature_names_ = list(TIME_NUMERIC)
        return self

    def transform(self, rows: Sequence[TimeRow]) -> np.ndarray:
        if self.scaler_ is None:
            raise RuntimeError("Time feature pipeline has not been fit.")
        raw = np.vstack([self._raw(row) for row in rows])
        return self.scaler_.transform(raw)

    def _raw(self, row: TimeRow) -> np.ndarray:
        duration = row.planned_duration_days
        progress = row.physical_progress_percent
        amount = float(row.allocation_amount or 0)
        year = float(row.recommended_date.year) if row.recommended_date else self.medians_.get("rec_year", 2023.0)
        if duration is None:
            duration = self.medians_.get("planned_duration_days", 0.0)
        if progress is None:
            progress = self.medians_.get("physical_progress_percent", 0.0)
        return np.asarray(
            [float(duration), float(progress), math.log1p(max(amount, 0.0)), year],
            dtype=float,
        )


def _usable(row: TimeRow) -> bool:
    return (
        row.planned_duration_days is not None
        and row.planned_duration_days > 0
        and row.allocation_amount is not None
    )


def time_row_from_payload(payload: dict[str, Any]) -> TimeRow:
    assert_no_label_leakage(payload)
    start = payload.get("planned_start_date")
    end = payload.get("planned_completion_date")
    duration = payload.get("planned_duration_days")
    if duration is None and isinstance(start, date) and isinstance(end, date):
        duration = float((end - start).days)
    rec = payload.get("recommendation_date") or payload.get("recommended_date")
    rec_date = rec if isinstance(rec, date) else None
    if isinstance(rec, str) and rec.strip():
        rec_date = date.fromisoformat(rec.strip()[:10])
    amount = payload.get("allocation_amount")
    return TimeRow(
        internal_project_id=str(payload.get("internal_project_id") or "new-project"),
        planned_duration_days=float(duration) if duration is not None else None,
        physical_progress_percent=(
            float(payload["physical_progress_percent"])
            if payload.get("physical_progress_percent") is not None
            else None
        ),
        allocation_amount=int(amount) if amount is not None else None,
        recommended_date=rec_date,
    )
