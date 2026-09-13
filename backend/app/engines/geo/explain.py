"""Human-readable geospatial explanations. Never claims fraud or authenticity."""

from __future__ import annotations

from app.engines.geo.constants import (
    CLAIM_AT_SITE,
    GOVERNANCE_NOTE,
    GPS_METADATA_UNAVAILABLE,
    INCONCLUSIVE,
    LOCATION_CONSISTENT,
    LOCATION_MISMATCH,
    LOCATION_UNAVAILABLE,
    MISSING_GPS_NOT_MISMATCH,
    MIXED_IMAGES_NOTE,
    PCE_CONTENT_NOTE,
    REAL_LOCATION_UNAVAILABLE,
    THRESHOLD_NOTE,
)
from app.engines.geo.types import (
    ImageConsistency,
    ImageLocation,
    PlanClaimEvidenceFraming,
    ProjectLocation,
)


def _meters_text(distance_meters: float | None) -> str:
    if distance_meters is None:
        return "unavailable"
    if abs(distance_meters - round(distance_meters)) < 0.05:
        return f"{int(round(distance_meters))} meters"
    return f"{distance_meters:.1f} meters"


def image_finding(
    *,
    result: str,
    distance_meters: float | None,
    threshold_meters: float,
    project_available: bool,
    image_gps_available: bool,
) -> str:
    if not project_available:
        return f"{INCONCLUSIVE} / {LOCATION_UNAVAILABLE}"
    if not image_gps_available:
        return GPS_METADATA_UNAVAILABLE
    if result == LOCATION_CONSISTENT:
        return LOCATION_CONSISTENT
    if result == LOCATION_MISMATCH:
        return LOCATION_MISMATCH
    return INCONCLUSIVE


def image_explanation(
    *,
    result: str,
    distance_meters: float | None,
    threshold_meters: float,
    project_available: bool,
    image_gps_available: bool,
    synthetic_project: bool,
) -> str:
    parts: list[str] = []
    if not project_available:
        parts.append(REAL_LOCATION_UNAVAILABLE if not synthetic_project else (
            "Project coordinates are unavailable. " + MISSING_GPS_NOT_MISMATCH
        ))
    elif not image_gps_available:
        parts.append(
            "GPS metadata unavailable. Image GPS was not inferred from image content. "
            + MISSING_GPS_NOT_MISMATCH
        )
    elif result == LOCATION_CONSISTENT:
        parts.append(
            f"Uploaded image GPS is {_meters_text(distance_meters)} from the supplied "
            f"project location, within the configured {int(threshold_meters)} meter "
            "prototype threshold."
        )
        parts.append(
            "This is a location consistency check and does not prove authenticity "
            "or that the photograph depicts the claimed work."
        )
    elif result == LOCATION_MISMATCH:
        parts.append(
            f"Uploaded image GPS is {_meters_text(distance_meters)} from the supplied "
            f"project location, outside the configured {int(threshold_meters)} meter "
            "prototype threshold."
        )
        parts.append(
            "This is a location consistency mismatch for review. It is not a legal "
            "finding and does not prove that the work is inauthentic."
        )
    else:
        parts.append(MISSING_GPS_NOT_MISMATCH)
    if synthetic_project:
        parts.append("Project coordinates are SYNTHETIC hybrid enrichment, not official MPLADS GPS.")
    parts.append(THRESHOLD_NOTE)
    return " ".join(parts)


def overall_explanation(
    *,
    overall: str,
    project_location: ProjectLocation,
    images: list[ImageConsistency],
    mixed: bool,
) -> str:
    parts: list[str] = []
    if not project_location.available:
        parts.append(REAL_LOCATION_UNAVAILABLE if not project_location.synthetic else (
            "Project coordinates are unavailable from SYNTHETIC enrichment. "
            + MISSING_GPS_NOT_MISMATCH
        ))
    elif not images:
        parts.append(
            "No uploaded images were available to compare against the project location. "
            "The result is INCONCLUSIVE."
        )
    elif overall == LOCATION_CONSISTENT:
        first = next((item for item in images if item.distance_meters is not None), None)
        if first is not None:
            parts.append(
                f"Uploaded image GPS is {_meters_text(first.distance_meters)} from the "
                f"supplied project location, within the configured "
                f"{int(first.threshold_meters)} meter prototype threshold."
            )
        else:
            parts.append("Available image GPS coordinates are within the prototype threshold.")
        parts.append(
            "This does not prove the photograph depicts the claimed work or that work was completed."
        )
    elif overall == LOCATION_MISMATCH:
        far = next((item for item in images if item.result == LOCATION_MISMATCH), None)
        if far is not None:
            parts.append(
                f"At least one uploaded image GPS is {_meters_text(far.distance_meters)} "
                f"from the supplied project location, outside the configured "
                f"{int(far.threshold_meters)} meter prototype threshold."
            )
        if mixed:
            parts.append(MIXED_IMAGES_NOTE)
        parts.append(
            "This is a location consistency mismatch for review, not a legal finding."
        )
    else:
        if any(item.location.gps_available is False for item in images):
            parts.append("GPS metadata unavailable for one or more images.")
        parts.append(MISSING_GPS_NOT_MISMATCH)
        if mixed:
            parts.append(MIXED_IMAGES_NOTE)
    if project_location.synthetic:
        parts.append("Project coordinates are SYNTHETIC and are not official MPLADS GPS.")
    parts.append(GOVERNANCE_NOTE)
    seen: set[str] = set()
    unique: list[str] = []
    for sentence in parts:
        if sentence not in seen:
            seen.add(sentence)
            unique.append(sentence)
    return " ".join(unique)


def pce_framing(
    *,
    overall: str,
    images: list[ImageConsistency],
    project_location: ProjectLocation,
) -> PlanClaimEvidenceFraming:
    claim = CLAIM_AT_SITE if images else None
    if not project_location.available:
        evidence = "Project location unavailable."
    elif not images:
        evidence = "No image GPS evidence was attached."
    else:
        bits: list[str] = []
        for item in images:
            if item.distance_meters is None:
                bits.append(f"image {item.image_id} GPS unavailable")
            else:
                bits.append(
                    f"image {item.image_id} GPS = {_meters_text(item.distance_meters)} from project location"
                )
        evidence = "; ".join(bits)
    return PlanClaimEvidenceFraming(
        claim=claim,
        evidence=evidence,
        result=overall,
        note=PCE_CONTENT_NOTE,
    )


def image_gps_unavailable_finding(location: ImageLocation) -> str:
    _ = location
    return GPS_METADATA_UNAVAILABLE
