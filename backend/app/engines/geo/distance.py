"""Deterministic geodesic distance for Geospatial Consistency V1.

Haversine great-circle distance. Not a surveyed cadastral measurement.
"""

from __future__ import annotations

import math

from app.engines.geo.constants import EARTH_RADIUS_M


def haversine_m(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Great-circle distance in metres between two WGS-84 points."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    hav = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * EARTH_RADIUS_M * math.asin(min(1.0, math.sqrt(hav)))


def distance_pair(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> tuple[float, float]:
    meters = haversine_m(lat1, lon1, lat2, lon2)
    return meters, meters / 1000.0


def offset_north_meters(lat: float, lon: float, meters: float) -> tuple[float, float]:
    """Return a point displaced due north by ``meters``. Test/helper only."""
    dlat = (meters / EARTH_RADIUS_M) * (180.0 / math.pi)
    return lat + dlat, lon
