"""Similarity primitives for Overlap Intelligence V1."""

from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import date

from app.engines.overlap.constants import DATE_DECAY_DAYS, GPS_PROXIMITY_M
from app.engines.overlap.text import place_tokens


def cosine_similarity(left: Sequence[float] | None, right: Sequence[float] | None) -> float | None:
    """Cosine similarity clipped to [0, 1]. None if either vector is missing."""
    if left is None or right is None:
        return None
    if len(left) == 0 or len(right) == 0 or len(left) != len(right):
        return None
    dot = 0.0
    left_norm_sq = 0.0
    right_norm_sq = 0.0
    for a, b in zip(left, right, strict=True):
        av = float(a)
        bv = float(b)
        dot += av * bv
        left_norm_sq += av * av
        right_norm_sq += bv * bv
    if left_norm_sq <= 0.0 or right_norm_sq <= 0.0:
        return 0.0
    value = dot / (math.sqrt(left_norm_sq) * math.sqrt(right_norm_sq))
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def amount_similarity(left: int | None, right: int | None) -> float | None:
    """1 - relative absolute difference. Unavailable when either amount is not positive."""
    if left is None or right is None:
        return None
    if left <= 0 or right <= 0:
        return None
    return max(0.0, 1.0 - abs(left - right) / max(left, right))


def date_proximity(left: date | None, right: date | None) -> tuple[float | None, int | None]:
    """Linear decay over DATE_DECAY_DAYS. Returns (similarity, gap_days)."""
    if left is None or right is None:
        return None, None
    gap = abs((left - right).days)
    similarity = max(0.0, 1.0 - gap / float(DATE_DECAY_DAYS))
    return similarity, gap


def token_jaccard(left: frozenset[str], right: frozenset[str]) -> float | None:
    if not left or not right:
        return None
    union = left | right
    if not union:
        return None
    return len(left & right) / len(union)


def location_similarity(left_place: str | None, right_place: str | None) -> float | None:
    """Jaccard of observed place tokens. Unavailable if either side has no place text."""
    return token_jaccard(place_tokens(left_place), place_tokens(right_place))


def haversine_m(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Great-circle distance in metres. Not a surveyed measurement."""
    radius = 6_371_000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    hav = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * radius * math.asin(min(1.0, math.sqrt(hav)))


def gps_similarity(
    lat1: float | None,
    lon1: float | None,
    lat2: float | None,
    lon2: float | None,
) -> tuple[float | None, float | None]:
    """Returns (similarity, distance_m). Unavailable when either coordinate is missing."""
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return None, None
    distance = haversine_m(lat1, lon1, lat2, lon2)
    similarity = max(0.0, 1.0 - distance / GPS_PROXIMITY_M)
    return similarity, distance
