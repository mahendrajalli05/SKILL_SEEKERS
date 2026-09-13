"""Unsupervised diagnostics. No accuracy/F1/AUC without genuine labels."""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np


def score_distribution(values: Sequence[float]) -> dict[str, float]:
    array = np.asarray(list(values), dtype=float)
    if array.size == 0:
        return {}
    return {
        "n": int(array.size),
        "min": float(np.min(array)),
        "p25": float(np.percentile(array, 25)),
        "median": float(np.median(array)),
        "p75": float(np.percentile(array, 75)),
        "p95": float(np.percentile(array, 95)),
        "max": float(np.max(array)),
        "mean": float(np.mean(array)),
        "std": float(np.std(array)),
    }


def group_medians(scores: dict[str, list[float]]) -> dict[str, Any]:
    return {key: score_distribution(values) for key, values in scores.items()}
