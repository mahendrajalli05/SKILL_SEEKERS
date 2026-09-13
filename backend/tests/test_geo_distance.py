from __future__ import annotations

import math

from app.engines.geo.constants import DEFAULT_THRESHOLD_METERS, EARTH_RADIUS_M
from app.engines.geo.distance import distance_pair, haversine_m, offset_north_meters
from app.engines.geo.evaluate import classify_distance


def test_same_coordinates_are_zero() -> None:
    meters, km = distance_pair(15.9129, 79.7400, 15.9129, 79.7400)
    assert meters == 0.0
    assert km == 0.0
    assert classify_distance(meters, DEFAULT_THRESHOLD_METERS) == "LOCATION_CONSISTENT"


def test_one_degree_longitude_at_equator() -> None:
    expected = 2 * EARTH_RADIUS_M * math.asin(math.sin(math.radians(0.5)))
    actual = haversine_m(0.0, 0.0, 0.0, 1.0)
    assert abs(actual - expected) < 1e-6
    assert actual > 100_000


def test_offset_north_is_deterministic() -> None:
    lat2, lon2 = offset_north_meters(17.0, 82.0, 148.0)
    meters, km = distance_pair(17.0, 82.0, lat2, lon2)
    assert abs(meters - 148.0) < 0.05
    assert abs(km - 0.148) < 0.0001
    assert classify_distance(meters, DEFAULT_THRESHOLD_METERS) == "LOCATION_CONSISTENT"


def test_boundary_is_consistent() -> None:
    lat2, lon2 = offset_north_meters(16.0, 81.0, 500.0)
    meters, _ = distance_pair(16.0, 81.0, lat2, lon2)
    assert abs(meters - 500.0) < 0.05
    assert classify_distance(500.0, DEFAULT_THRESHOLD_METERS) == "LOCATION_CONSISTENT"
    assert classify_distance(500.0001, DEFAULT_THRESHOLD_METERS) == "LOCATION_MISMATCH"


def test_just_outside_and_far_away() -> None:
    assert classify_distance(501.0, DEFAULT_THRESHOLD_METERS) == "LOCATION_MISMATCH"
    far = haversine_m(18.1167, 83.4, 10.05, 68.4)
    assert far > 1_000_000
    assert classify_distance(far, DEFAULT_THRESHOLD_METERS) == "LOCATION_MISMATCH"


def test_threshold_is_configurable() -> None:
    assert classify_distance(200.0, 100.0) == "LOCATION_MISMATCH"
    assert classify_distance(200.0, 250.0) == "LOCATION_CONSISTENT"
