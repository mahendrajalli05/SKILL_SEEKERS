"""Citizen location verification using Geospatial Consistency V1 distance.

500 m is a prototype rule. Project coordinates are never invented.
"""

from __future__ import annotations

from app.engines.citizen.constants import (
    DEFAULT_RADIUS_METERS,
    INCONCLUSIVE,
    LOCATION_REJECTED,
    LOCATION_UNAVAILABLE,
    LOCATION_VERIFIED,
    THRESHOLD_NOTE,
)
from app.engines.citizen.types import LocationVerification
from app.engines.geo.distance import haversine_m
from app.engines.geo.types import ProjectLocation


def classify_citizen_distance(distance_meters: float, threshold_meters: float) -> str:
    if distance_meters <= threshold_meters:
        return LOCATION_VERIFIED
    return LOCATION_REJECTED


def distance_band(distance_meters: float | None, threshold_meters: float) -> str | None:
    if distance_meters is None:
        return None
    if distance_meters <= threshold_meters:
        return "WITHIN_THRESHOLD"
    return "OUTSIDE_THRESHOLD"


def verify_location(
    *,
    project_location: ProjectLocation,
    citizen_latitude: float | None,
    citizen_longitude: float | None,
    threshold_meters: float = DEFAULT_RADIUS_METERS,
) -> LocationVerification:
    project_ok = (
        project_location.available
        and project_location.latitude is not None
        and project_location.longitude is not None
    )
    citizen_ok = citizen_latitude is not None and citizen_longitude is not None
    if not project_ok:
        return LocationVerification(
            result=INCONCLUSIVE,
            project_gps_available=False,
            citizen_gps_available=bool(citizen_ok),
            distance_meters=None,
            threshold_meters=threshold_meters,
            distance_band=None,
            reason=(
                "INCONCLUSIVE / LOCATION_UNAVAILABLE. Project coordinates are not "
                "available. Coordinates were not invented. A location decision was not forced."
            ),
            prototype_rule_note=THRESHOLD_NOTE,
            project_location_synthetic=bool(project_location.synthetic),
        )
    if not citizen_ok:
        return LocationVerification(
            result=INCONCLUSIVE,
            project_gps_available=True,
            citizen_gps_available=False,
            distance_meters=None,
            threshold_meters=threshold_meters,
            distance_band=None,
            reason=(
                "INCONCLUSIVE / LOCATION_UNAVAILABLE. Citizen GPS was not supplied. "
                "Missing GPS is not treated as a location rejection."
            ),
            prototype_rule_note=THRESHOLD_NOTE,
            project_location_synthetic=bool(project_location.synthetic),
        )
    meters = haversine_m(
        float(project_location.latitude),
        float(project_location.longitude),
        float(citizen_latitude),
        float(citizen_longitude),
    )
    result = classify_citizen_distance(meters, threshold_meters)
    if result == LOCATION_VERIFIED:
        reason = (
            f"Citizen GPS is {round(meters, 1)} metres from the supplied project location, "
            f"within the configured {threshold_meters:g} metre prototype threshold."
        )
    else:
        reason = (
            f"Citizen GPS is {round(meters, 1)} metres from the supplied project location, "
            f"outside the configured {threshold_meters:g} metre prototype threshold."
        )
    return LocationVerification(
        result=result,
        project_gps_available=True,
        citizen_gps_available=True,
        distance_meters=round(meters, 3),
        threshold_meters=threshold_meters,
        distance_band=distance_band(meters, threshold_meters),
        reason=reason,
        prototype_rule_note=THRESHOLD_NOTE,
        project_location_synthetic=bool(project_location.synthetic),
    )


def unavailable_alias(result: str) -> str:
    if result == INCONCLUSIVE:
        return LOCATION_UNAVAILABLE
    return result
