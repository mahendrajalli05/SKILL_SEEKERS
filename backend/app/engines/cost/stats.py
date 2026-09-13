"""Robust peer statistics for Cost Intelligence V1.1.

Original-scale median / percentiles / MAD for display.
Log-scale median / MAD for scoring so multiplicative skew and extreme
peer amounts do not dominate the baseline.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from app.engines.cost.types import PeerStatistics


def percentile(sorted_values: Sequence[float], p: float) -> float:
    """Linear-interpolated percentile. ``p`` is in 0–100. Deterministic."""
    if not sorted_values:
        raise ValueError("percentile requires at least one value.")
    if p < 0 or p > 100:
        raise ValueError("percentile p must be between 0 and 100.")
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    rank = (len(sorted_values) - 1) * (p / 100.0)
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return float(sorted_values[int(rank)])
    weight = rank - low
    return float(sorted_values[low]) * (1.0 - weight) + float(sorted_values[high]) * weight


def median(values: Sequence[float]) -> float:
    ordered = sorted(float(item) for item in values)
    if not ordered:
        raise ValueError("median requires at least one value.")
    return percentile(ordered, 50.0)


def median_absolute_deviation(values: Sequence[float], centre: float | None = None) -> float:
    ordered = [float(item) for item in values]
    if not ordered:
        raise ValueError("MAD requires at least one value.")
    if centre is None:
        centre = median(ordered)
    deviations = [abs(item - centre) for item in ordered]
    return median(deviations)


def compute_peer_statistics(amounts: Sequence[int | float]) -> PeerStatistics:
    if not amounts:
        raise ValueError("peer statistics require at least one amount.")
    ordered = sorted(float(item) for item in amounts)
    if any(item <= 0 for item in ordered):
        raise ValueError("peer statistics require positive amounts.")
    centre = percentile(ordered, 50.0)
    p25 = percentile(ordered, 25.0)
    p75 = percentile(ordered, 75.0)
    p10 = percentile(ordered, 10.0) if len(ordered) >= 10 else None
    p90 = percentile(ordered, 90.0) if len(ordered) >= 10 else None
    mad = median_absolute_deviation(ordered, centre)
    log_values = [math.log(item) for item in ordered]
    log_centre = percentile(log_values, 50.0)
    log_mad = median_absolute_deviation(log_values, log_centre)
    return PeerStatistics(
        peer_count=len(ordered),
        median=centre,
        percentile_25=p25,
        percentile_75=p75,
        percentile_10=p10,
        percentile_90=p90,
        mad=mad,
        log_median=log_centre,
        log_mad=log_mad,
    )
