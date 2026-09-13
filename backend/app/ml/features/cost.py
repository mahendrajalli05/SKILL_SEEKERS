"""Cost feature engineering for Isolation Forest.

Uses only observed MPLADS fields. Held-out synthetic scenario columns are
rejected. TF-IDF vocabulary and peer percentiles are fit on TRAIN only.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Sequence

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler

from app.engines.overlap.text import embedding_text
from app.ml.constants import RANDOM_SEED, SVD_COMPONENTS, TFIDF_MAX_FEATURES, TFIDF_MIN_DF
from app.ml.features.forbidden import assert_no_label_leakage
from app.ml.types import CostRow, FeatureAvailability

NUMERIC_BASE = (
    "log_allocation",
    "allocation_peer_percentile",
    "rec_year",
    "rec_month",
    "recommendation_age_days",
    "desc_token_count",
    "freq_state",
    "freq_constituency",
    "freq_category",
    "freq_status",
    "freq_house",
)


def _norm(value: str | None) -> str:
    return (value or "").strip()


def _token_count(text: str) -> int:
    return len([part for part in embedding_text(text).split() if part])


def _percentile(sorted_values: list[float], value: float) -> float:
    if not sorted_values:
        return 0.5
    n = len(sorted_values)
    # Mid-rank empirical percentile in [0, 1].
    count = 0
    for item in sorted_values:
        if item <= value:
            count += 1
        else:
            break
    return count / n


@dataclass
class CostFeaturePipeline:
    """Fit on train rows only. Transform is deterministic given the frozen maps."""

    tfidf_max_features: int = TFIDF_MAX_FEATURES
    tfidf_min_df: int = TFIDF_MIN_DF
    svd_components: int = SVD_COMPONENTS
    feature_names_: list[str] = field(default_factory=list)
    freq_maps_: dict[str, dict[str, float]] = field(default_factory=dict)
    group_amounts_: dict[tuple[str, str], list[float]] = field(default_factory=dict)
    state_amounts_: dict[str, list[float]] = field(default_factory=dict)
    global_amounts_: list[float] = field(default_factory=list)
    date_medians_: dict[str, float] = field(default_factory=dict)
    reference_date_: date | None = None
    vectorizer_: TfidfVectorizer | None = None
    svd_: TruncatedSVD | None = None
    scaler_: StandardScaler | None = None
    n_text_components_: int = 0

    def fit(self, rows: Sequence[CostRow]) -> CostFeaturePipeline:
        if not rows:
            raise ValueError("Cost feature pipeline requires at least one training row.")
        n = len(rows)
        self.freq_maps_ = {
            "state": _frequencies(row.state for row in rows),
            "constituency": _frequencies(row.constituency for row in rows),
            "category": _frequencies(row.category for row in rows),
            "status": _frequencies(row.status for row in rows),
            "house": _frequencies(row.house for row in rows),
        }
        groups: dict[tuple[str, str], list[float]] = {}
        states: dict[str, list[float]] = {}
        global_amounts: list[float] = []
        years: list[float] = []
        months: list[float] = []
        ages: list[float] = []
        dated = [row.recommended_date for row in rows if row.recommended_date is not None]
        self.reference_date_ = max(dated) if dated else date(2026, 9, 9)
        for row in rows:
            amount = float(row.allocation_amount or 0)
            global_amounts.append(amount)
            groups.setdefault((row.state, row.category), []).append(amount)
            states.setdefault(row.state, []).append(amount)
            if row.recommended_date is not None:
                years.append(float(row.recommended_date.year))
                months.append(float(row.recommended_date.month))
                ages.append(float((self.reference_date_ - row.recommended_date).days))
        for key in groups:
            groups[key].sort()
        for key in states:
            states[key].sort()
        global_amounts.sort()
        self.group_amounts_ = groups
        self.state_amounts_ = states
        self.global_amounts_ = global_amounts
        self.date_medians_ = {
            "year": float(np.median(years)) if years else 2023.0,
            "month": float(np.median(months)) if months else 6.0,
            "age": float(np.median(ages)) if ages else 0.0,
        }

        texts = [embedding_text(row.work_description) for row in rows]
        usable = sum(1 for text in texts if text)
        min_df = min(self.tfidf_min_df, max(1, n))
        max_features = min(self.tfidf_max_features, max(1, usable))
        self.n_text_components_ = 0
        self.vectorizer_ = None
        self.svd_ = None
        text_matrix = None
        if usable >= 2:
            self.vectorizer_ = TfidfVectorizer(
                lowercase=True,
                ngram_range=(1, 2),
                min_df=min_df,
                max_features=max_features,
                token_pattern=r"(?u)\b\w+\b",
            )
            try:
                tfidf = self.vectorizer_.fit_transform(texts)
            except ValueError:
                self.vectorizer_ = None
                tfidf = None
            if tfidf is not None and tfidf.shape[1] >= 2:
                n_comp = min(self.svd_components, tfidf.shape[1] - 1, n - 1)
                n_comp = max(1, n_comp)
                self.svd_ = TruncatedSVD(n_components=n_comp, random_state=RANDOM_SEED)
                text_matrix = self.svd_.fit_transform(tfidf)
                self.n_text_components_ = n_comp
            else:
                self.vectorizer_ = None

        base = np.vstack([self._base_vector(row) for row in rows])
        if text_matrix is None:
            text_matrix = np.zeros((n, 0), dtype=float)
        combined = np.hstack([base, text_matrix]) if text_matrix.shape[1] else base
        self.scaler_ = StandardScaler()
        self.scaler_.fit(combined)
        text_names = [f"text_svd_{i}" for i in range(self.n_text_components_)]
        self.feature_names_ = list(NUMERIC_BASE) + text_names
        return self

    def transform(self, rows: Sequence[CostRow]) -> np.ndarray:
        if self.scaler_ is None:
            raise RuntimeError("Cost feature pipeline has not been fit.")
        base = np.vstack([self._base_vector(row) for row in rows])
        text_matrix = self._text_matrix(rows)
        combined = np.hstack([base, text_matrix]) if text_matrix.shape[1] else base
        return self.scaler_.transform(combined)

    def feature_values(self, row: CostRow) -> dict[str, Any]:
        vector = self._base_vector(row)
        values: dict[str, Any] = {
            name: float(vector[i]) for i, name in enumerate(NUMERIC_BASE)
        }
        values["allocation_amount"] = row.allocation_amount
        values["category"] = row.category
        values["state"] = row.state
        values["constituency"] = row.constituency
        values["status"] = row.status
        values["house"] = row.house
        values["work_description"] = row.work_description
        values["recommended_date"] = (
            row.recommended_date.isoformat() if row.recommended_date else None
        )
        return values

    def availability(self, row: CostRow, payload: dict[str, Any] | None = None) -> FeatureAvailability:
        if payload:
            assert_no_label_leakage(payload)
        available: list[str] = []
        missing: list[str] = []
        unseen: list[str] = []
        if row.allocation_amount is None:
            missing.append("allocation_amount")
        else:
            available.append("allocation_amount")
        for field, value, key in (
            ("category", row.category, "category"),
            ("state", row.state, "state"),
            ("constituency", row.constituency, "constituency"),
            ("status", row.status, "status"),
            ("house", row.house, "house"),
            ("work_description", row.work_description, "work_description"),
        ):
            if not value:
                missing.append(field)
            else:
                available.append(field)
                mapping = self.freq_maps_.get(key, {})
                if key in self.freq_maps_ and value not in mapping:
                    unseen.append(field)
        if row.recommended_date is None:
            missing.append("recommendation_date")
        else:
            available.append("recommendation_date")
        schema_n = 8
        coverage = round(len(available) / schema_n, 3)
        return FeatureAvailability(
            available=available,
            missing=missing,
            unseen=unseen,
            unsupported=[],
            coverage=min(1.0, coverage),
        )

    def _base_vector(self, row: CostRow) -> np.ndarray:
        amount = float(row.allocation_amount or 0)
        log_allocation = math.log1p(max(amount, 0.0))
        percentile = self._peer_percentile(row.state, row.category, amount)
        if row.recommended_date is None:
            year = self.date_medians_.get("year", 2023.0)
            month = self.date_medians_.get("month", 6.0)
            age = self.date_medians_.get("age", 0.0)
        else:
            year = float(row.recommended_date.year)
            month = float(row.recommended_date.month)
            ref = self.reference_date_ or row.recommended_date
            age = float((ref - row.recommended_date).days)
        values = [
            log_allocation,
            percentile,
            year,
            month,
            age,
            float(_token_count(row.work_description)),
            self.freq_maps_.get("state", {}).get(row.state, 0.0),
            self.freq_maps_.get("constituency", {}).get(row.constituency, 0.0),
            self.freq_maps_.get("category", {}).get(row.category, 0.0),
            self.freq_maps_.get("status", {}).get(row.status, 0.0),
            self.freq_maps_.get("house", {}).get(row.house, 0.0),
        ]
        return np.asarray(values, dtype=float)

    def _text_matrix(self, rows: Sequence[CostRow]) -> np.ndarray:
        n = len(rows)
        if self.vectorizer_ is None or self.svd_ is None or self.n_text_components_ == 0:
            return np.zeros((n, 0), dtype=float)
        texts = [embedding_text(row.work_description) for row in rows]
        tfidf = self.vectorizer_.transform(texts)
        return self.svd_.transform(tfidf)

    def _peer_percentile(self, state: str, category: str, amount: float) -> float:
        group = self.group_amounts_.get((state, category)) or []
        if len(group) >= 5:
            return _percentile(group, amount)
        state_group = self.state_amounts_.get(state) or []
        if len(state_group) >= 5:
            return _percentile(state_group, amount)
        return _percentile(self.global_amounts_, amount)


def _frequencies(values) -> dict[str, float]:
    items = [_norm(item) for item in values]
    n = len(items) or 1
    counts = Counter(items)
    return {key: count / n for key, count in counts.items() if key}


def rows_from_payload(payload: dict[str, Any]) -> CostRow:
    assert_no_label_leakage(payload)
    rec = payload.get("recommendation_date") or payload.get("recommended_date")
    rec_date: date | None
    if isinstance(rec, date):
        rec_date = rec
    elif isinstance(rec, str) and rec.strip():
        rec_date = date.fromisoformat(rec.strip()[:10])
    else:
        rec_date = None
    amount = payload.get("allocation_amount")
    amount_i: int | None
    if amount is None or amount == "":
        amount_i = None
    else:
        amount_i = int(float(amount))
    return CostRow(
        internal_project_id=str(payload.get("internal_project_id") or "new-project"),
        allocation_amount=amount_i,
        category=_norm(payload.get("category")),
        state=_norm(payload.get("state")),
        constituency=_norm(payload.get("constituency")),
        work_description=_norm(payload.get("work_description")),
        recommended_date=rec_date,
        status=_norm(payload.get("status")),
        house=_norm(payload.get("house")),
        is_synthetic=bool(payload.get("is_synthetic", False)),
    )
