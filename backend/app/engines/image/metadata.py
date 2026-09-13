"""Extract reported EXIF metadata. Values are not verified or inferred."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any

from PIL import Image, ExifTags, UnidentifiedImageError

from app.engines.image.constants import (
    GPS_UNAVAILABLE_MESSAGE,
    METADATA_CONFIDENCE,
    METADATA_SOURCE_LABEL,
    METADATA_UNAVAILABLE,
)
from app.engines.image.types import MetadataField

_UNAVAILABLE_METHOD = "unavailable"
_EXIF_METHOD = "exif"

_GPS_IFD = getattr(ExifTags.IFD, "GPSInfo", 0x8825)
_EXIF_IFD = getattr(ExifTags.IFD, "Exif", 0x8769)

_GPS_LAT_REF = 1
_GPS_LAT = 2
_GPS_LON_REF = 3
_GPS_LON = 4
try:
    _GPS_LAT_REF = int(ExifTags.GPS.GPSLatitudeRef)
    _GPS_LAT = int(ExifTags.GPS.GPSLatitude)
    _GPS_LON_REF = int(ExifTags.GPS.GPSLongitudeRef)
    _GPS_LON = int(ExifTags.GPS.GPSLongitude)
except Exception:  # pragma: no cover - Pillow tag layout fallback
    pass


def _ratio_to_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if hasattr(value, "numerator") and hasattr(value, "denominator"):
        denom = float(value.denominator)
        if denom == 0:
            return None
        return float(value.numerator) / denom
    if isinstance(value, tuple) and len(value) == 2:
        try:
            num = float(value[0])
            den = float(value[1])
        except (TypeError, ValueError):
            return None
        if den == 0:
            return None
        return num / den
    if isinstance(value, tuple) and len(value) == 3:
        degrees = _ratio_to_float(value[0]) or 0.0
        minutes = _ratio_to_float(value[1]) or 0.0
        seconds = _ratio_to_float(value[2]) or 0.0
        return degrees + (minutes / 60.0) + (seconds / 3600.0)
    return None


def _decode_text(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        text = value.decode("utf-8", errors="replace").strip("\x00").strip()
        return text or None
    text = str(value).strip()
    return text or None


def _signed_gps(magnitude: float | None, ref: str | None, negative_tokens: tuple[str, ...]) -> float | None:
    if magnitude is None:
        return None
    token = (ref or "").strip().upper()
    if token in negative_tokens:
        return -abs(magnitude)
    return magnitude


def _parse_timestamp(value: str | None) -> str | None:
    if not value:
        return None
    text = value.strip().replace("-", ":")
    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y:%m:%d %H:%M:%S%z", "%Y:%m:%d"):
        try:
            parsed = datetime.strptime(text[:19] if "T" not in text else text.replace("T", " ")[:19], fmt)
            return parsed.isoformat()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
    except ValueError:
        return value


def _field(
    name: str,
    value: object,
    *,
    available: bool,
    reason: str | None = None,
    confidence: float | None = None,
    method: str | None = None,
) -> MetadataField:
    return MetadataField(
        field=name,
        value=value,
        source=METADATA_SOURCE_LABEL,
        extraction_method=method or (_EXIF_METHOD if available else _UNAVAILABLE_METHOD),
        confidence=METADATA_CONFIDENCE if available else 0.0,
        available=available,
        unavailable_reason=reason,
    )


def extract_metadata(payload: bytes) -> dict[str, Any]:
    fields: list[MetadataField] = []
    try:
        with Image.open(BytesIO(payload)) as image:
            image.load()
            exif = image.getexif()
    except (UnidentifiedImageError, OSError, ValueError):
        reason = METADATA_UNAVAILABLE
        names = ("capture_timestamp", "latitude", "longitude", "camera_make", "camera_model")
        fields = [
            _field(name, None, available=False, reason=reason)
            for name in names
        ]
        return {
            "status": METADATA_UNAVAILABLE,
            "fields": fields,
            "gps_available": False,
            "gps_message": GPS_UNAVAILABLE_MESSAGE,
            "capture_timestamp": None,
            "latitude": None,
            "longitude": None,
            "camera_make": None,
            "camera_model": None,
        }

    gps_ifd: dict[int, Any] = {}
    exif_ifd: dict[int, Any] = {}
    try:
        gps_ifd = dict(exif.get_ifd(_GPS_IFD) or {})
    except Exception:
        gps_ifd = {}
    try:
        exif_ifd = dict(exif.get_ifd(_EXIF_IFD) or {})
    except Exception:
        exif_ifd = {}

    make = _decode_text(exif.get(271))
    model = _decode_text(exif.get(272))
    datetime_original = _decode_text(exif_ifd.get(36867) or exif.get(36867))
    datetime_digitized = _decode_text(exif_ifd.get(36868) or exif.get(36868))
    datetime_generic = _decode_text(exif.get(306))
    timestamp_raw = datetime_original or datetime_digitized or datetime_generic
    timestamp = _parse_timestamp(timestamp_raw)

    lat_mag = _ratio_to_float(gps_ifd.get(_GPS_LAT))
    lon_mag = _ratio_to_float(gps_ifd.get(_GPS_LON))
    lat_ref = _decode_text(gps_ifd.get(_GPS_LAT_REF))
    lon_ref = _decode_text(gps_ifd.get(_GPS_LON_REF))
    latitude = _signed_gps(lat_mag, lat_ref, ("S", "SOUTH"))
    longitude = _signed_gps(lon_mag, lon_ref, ("W", "WEST"))
    gps_available = latitude is not None and longitude is not None

    missing = METADATA_UNAVAILABLE
    fields = [
        _field(
            "capture_timestamp",
            timestamp,
            available=timestamp is not None,
            reason=None if timestamp else missing,
        ),
        _field(
            "latitude",
            latitude,
            available=gps_available,
            reason=None if gps_available else GPS_UNAVAILABLE_MESSAGE,
        ),
        _field(
            "longitude",
            longitude,
            available=gps_available,
            reason=None if gps_available else GPS_UNAVAILABLE_MESSAGE,
        ),
        _field("camera_make", make, available=make is not None, reason=None if make else missing),
        _field("camera_model", model, available=model is not None, reason=None if model else missing),
    ]
    any_available = any(item.available for item in fields)
    return {
        "status": "METADATA_PRESENT" if any_available else METADATA_UNAVAILABLE,
        "fields": fields,
        "gps_available": gps_available,
        "gps_message": None if gps_available else GPS_UNAVAILABLE_MESSAGE,
        "capture_timestamp": timestamp,
        "latitude": latitude,
        "longitude": longitude,
        "camera_make": make,
        "camera_model": model,
    }
