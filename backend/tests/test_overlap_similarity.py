from __future__ import annotations

from app.engines.overlap.similarity import (
    amount_similarity,
    cosine_similarity,
    date_proximity,
    gps_similarity,
    haversine_m,
    location_similarity,
)
from datetime import date


def test_cosine_identical_orthogonal_and_clipped() -> None:
    assert cosine_similarity((1.0, 0.0), (1.0, 0.0)) == 1.0
    assert cosine_similarity((1.0, 0.0), (0.0, 1.0)) == 0.0
    assert cosine_similarity((1.0, 0.0), (-1.0, 0.0)) == 0.0
    assert cosine_similarity((1.0, 0.0), None) is None


def test_amount_similarity_equal_and_double() -> None:
    assert amount_similarity(500_000, 500_000) == 1.0
    assert amount_similarity(500_000, 1_000_000) == 0.5
    assert amount_similarity(None, 500_000) is None
    assert amount_similarity(0, 500_000) is None


def test_date_proximity_same_day_and_decay() -> None:
    same, gap = date_proximity(date(2023, 6, 1), date(2023, 6, 1))
    assert gap == 0
    assert same == 1.0
    half, days = date_proximity(date(2023, 6, 1), date(2023, 7, 16))
    assert days == 45
    assert half == 0.5
    assert date_proximity(None, date(2023, 6, 1)) == (None, None)


def test_location_similarity_unavailable_when_sparse() -> None:
    assert location_similarity("", "Pedakakani") is None
    assert location_similarity("Pedakakani", "Pedakakani") == 1.0


def test_gps_similarity_500m_threshold() -> None:
    # ~111 m north of the first point
    sim, dist = gps_similarity(15.8281, 78.0373, 15.8291, 78.0373)
    assert dist is not None
    assert 90 < dist < 150
    assert sim is not None
    assert sim > 0.7
    far = haversine_m(15.8281, 78.0373, 16.3067, 80.4365)
    assert far > 50_000
    assert gps_similarity(15.8281, 78.0373, None, 78.0) == (None, None)
