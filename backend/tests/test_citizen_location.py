from __future__ import annotations

from app.engines.citizen.constants import DEFAULT_RADIUS_METERS, LOCATION_REJECTED, LOCATION_VERIFIED
from app.engines.citizen.location import classify_citizen_distance
from app.engines.geo.distance import distance_pair, offset_north_meters


def test_500m_boundary_is_verified() -> None:
    assert classify_citizen_distance(180.0, DEFAULT_RADIUS_METERS) == LOCATION_VERIFIED
    assert classify_citizen_distance(500.0, DEFAULT_RADIUS_METERS) == LOCATION_VERIFIED
    assert classify_citizen_distance(500.0001, DEFAULT_RADIUS_METERS) == LOCATION_REJECTED
    assert classify_citizen_distance(1800.0, DEFAULT_RADIUS_METERS) == LOCATION_REJECTED


def test_offset_180m_and_1800m_are_deterministic() -> None:
    lat2, lon2 = offset_north_meters(18.1167, 83.4, 180.0)
    meters, _ = distance_pair(18.1167, 83.4, lat2, lon2)
    assert abs(meters - 180.0) < 0.05
    assert classify_citizen_distance(meters, DEFAULT_RADIUS_METERS) == LOCATION_VERIFIED
    lat3, lon3 = offset_north_meters(18.1167, 83.4, 1800.0)
    far, _ = distance_pair(18.1167, 83.4, lat3, lon3)
    assert abs(far - 1800.0) < 0.2
    assert classify_citizen_distance(far, DEFAULT_RADIUS_METERS) == LOCATION_REJECTED
