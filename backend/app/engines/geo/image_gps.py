"""Read reported image GPS from Image Evidence V1. Do not infer from pixels."""

from __future__ import annotations

import json
from typing import Any

from app.domain.enums import DataMode
from app.engines.geo.constants import (
    GPS_METADATA_UNAVAILABLE,
    IMAGE_GPS_SOURCE_LABEL,
    REPORTED_METADATA_CONFIDENCE,
    UNAVAILABLE_CONFIDENCE,
)
from app.engines.geo.types import ImageLocation
from app.models.artifacts import Photo


def _load_analysis(photo: Photo) -> dict[str, Any]:
    if not photo.analysis_json:
        return {}
    try:
        loaded = json.loads(photo.analysis_json)
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _photo_mode(photo: Photo) -> DataMode:
    text = str(photo.data_mode or DataMode.REAL.value).upper()
    if text == DataMode.HYBRID.value:
        return DataMode.HYBRID
    if text == DataMode.SYNTHETIC.value:
        return DataMode.SYNTHETIC
    return DataMode.REAL


def image_location_from_photo(photo: Photo) -> ImageLocation:
    analysis = _load_analysis(photo)
    lat = photo.exif_lat
    lon = photo.exif_lon
    if lat is None:
        raw_lat = analysis.get("latitude")
        lat = float(raw_lat) if raw_lat is not None else None
    if lon is None:
        raw_lon = analysis.get("longitude")
        lon = float(raw_lon) if raw_lon is not None else None
    method = "unavailable"
    confidence = UNAVAILABLE_CONFIDENCE
    for field in analysis.get("metadata_fields") or []:
        if not isinstance(field, dict):
            continue
        if field.get("field") in {"latitude", "longitude"} and field.get("available"):
            method = str(field.get("extraction_method") or "exif")
            try:
                confidence = float(field.get("confidence") or REPORTED_METADATA_CONFIDENCE)
            except (TypeError, ValueError):
                confidence = REPORTED_METADATA_CONFIDENCE
            break
    gps_available = lat is not None and lon is not None
    if gps_available and method == "unavailable":
        method = "exif"
        confidence = REPORTED_METADATA_CONFIDENCE
    return ImageLocation(
        image_id=photo.id,
        latitude=lat if gps_available else None,
        longitude=lon if gps_available else None,
        source=IMAGE_GPS_SOURCE_LABEL,
        extraction_method=method if gps_available else "unavailable",
        confidence=confidence if gps_available else UNAVAILABLE_CONFIDENCE,
        data_mode=_photo_mode(photo),
        gps_status="GPS_METADATA_PRESENT" if gps_available else GPS_METADATA_UNAVAILABLE,
        gps_available=gps_available,
        unavailable_reason=None if gps_available else GPS_METADATA_UNAVAILABLE,
    )
