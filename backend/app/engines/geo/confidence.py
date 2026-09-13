"""Local geospatial Evidence Confidence. Separate from Location Consistency."""

from __future__ import annotations

from app.domain.enums import DataMode
from app.engines.geo.constants import (
    HYBRID_CONFIDENCE_CAP,
    REAL_CONFIDENCE_CAP,
    REPORTED_METADATA_CONFIDENCE,
    SYNTHETIC_CONFIDENCE_CAP,
    SYNTHETIC_PROJECT_LOCATION_CONFIDENCE,
    UNAVAILABLE_CONFIDENCE,
)
from app.engines.geo.types import ImageConsistency, ProjectLocation


def _mode_cap(data_mode: DataMode) -> float:
    if data_mode == DataMode.SYNTHETIC:
        return SYNTHETIC_CONFIDENCE_CAP
    if data_mode == DataMode.HYBRID:
        return HYBRID_CONFIDENCE_CAP
    return REAL_CONFIDENCE_CAP


def image_check_confidence(
    *,
    project_location: ProjectLocation,
    image_gps_available: bool,
    metadata_confidence: float,
    data_mode: DataMode,
) -> float:
    """Local confidence for one image check. Matching GPS does not mean high project confidence."""
    if not project_location.available or not image_gps_available:
        return min(UNAVAILABLE_CONFIDENCE, _mode_cap(data_mode))
    reported = min(max(metadata_confidence, 0.0), REPORTED_METADATA_CONFIDENCE)
    source = (
        SYNTHETIC_PROJECT_LOCATION_CONFIDENCE
        if project_location.synthetic
        else project_location.confidence
    )
    combined = min(reported, source)
    return round(min(combined, _mode_cap(data_mode)), 4)


def overall_confidence(project_location: ProjectLocation, images: list[ImageConsistency], data_mode: DataMode) -> float:
    if not images:
        return min(UNAVAILABLE_CONFIDENCE, _mode_cap(data_mode))
    values = [item.confidence for item in images]
    return round(min(sum(values) / len(values), _mode_cap(data_mode)), 4)
