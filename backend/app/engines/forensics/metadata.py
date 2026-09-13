"""Metadata forensics. Missing EXIF is a signal only, never proof of manipulation."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any

from PIL import Image, ExifTags, UnidentifiedImageError

from app.domain.enums import DataMode
from app.engines.forensics.confidence import capped, confidence_label
from app.engines.forensics.constants import (
    AI_SOFTWARE_TOKENS,
    EDITOR_SOFTWARE_TOKENS,
    EXIF_UNAVAILABLE,
    INCONCLUSIVE,
    METADATA_ANOMALY,
    NO_STRONG_FORENSIC_SIGNAL,
    SIGNAL_METADATA,
    TIMESTAMP_AVAILABLE,
    TIMESTAMP_MISMATCH_SECONDS,
    TIMESTAMP_UNAVAILABLE,
)
from app.engines.forensics.types import ForensicSignal
from app.engines.image.constants import METADATA_SOURCE_LABEL
from app.engines.image.metadata import extract_metadata

_EXIF_IFD = getattr(ExifTags.IFD, "Exif", 0x8769)
_SOFTWARE_TAG = 305
_DATETIME_TAG = 306
_PIXEL_X = 40962
_PIXEL_Y = 40963
_DATETIME_ORIGINAL = 36867
_DATETIME_DIGITIZED = 36868


def _decode_text(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        text = value.decode("utf-8", errors="replace").strip("\x00").strip()
        return text or None
    text = str(value).strip()
    return text or None


def _parse_exif_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip().replace("-", ":").replace("T", " ")
    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y:%m:%d %H:%M:%S%z", "%Y:%m:%d"):
        try:
            return datetime.strptime(text[:19], fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _contains_token(text: str | None, tokens: tuple[str, ...]) -> str | None:
    if not text:
        return None
    folded = text.casefold()
    for token in tokens:
        if token in folded:
            return token
    return None


def _read_extra_exif(payload: bytes) -> dict[str, Any]:
    empty = {
        "software": None,
        "datetime": None,
        "datetime_original": None,
        "datetime_digitized": None,
        "pixel_x": None,
        "pixel_y": None,
        "exif_present": False,
    }
    try:
        with Image.open(BytesIO(payload)) as image:
            image.load()
            exif = image.getexif()
            width, height = image.size
    except (UnidentifiedImageError, OSError, ValueError):
        return {**empty, "actual_width": None, "actual_height": None}

    if not exif:
        return {**empty, "actual_width": width, "actual_height": height}

    exif_ifd: dict[int, Any] = {}
    try:
        exif_ifd = dict(exif.get_ifd(_EXIF_IFD) or {})
    except Exception:
        exif_ifd = {}

    software = _decode_text(exif.get(_SOFTWARE_TAG))
    datetime_generic = _decode_text(exif.get(_DATETIME_TAG))
    datetime_original = _decode_text(exif_ifd.get(_DATETIME_ORIGINAL) or exif.get(_DATETIME_ORIGINAL))
    datetime_digitized = _decode_text(exif_ifd.get(_DATETIME_DIGITIZED) or exif.get(_DATETIME_DIGITIZED))
    pixel_x = exif_ifd.get(_PIXEL_X) or exif.get(_PIXEL_X)
    pixel_y = exif_ifd.get(_PIXEL_Y) or exif.get(_PIXEL_Y)
    try:
        pixel_x = int(pixel_x) if pixel_x is not None else None
    except (TypeError, ValueError):
        pixel_x = None
    try:
        pixel_y = int(pixel_y) if pixel_y is not None else None
    except (TypeError, ValueError):
        pixel_y = None

    any_tag = bool(list(exif.keys()))
    return {
        "software": software,
        "datetime": datetime_generic,
        "datetime_original": datetime_original,
        "datetime_digitized": datetime_digitized,
        "pixel_x": pixel_x,
        "pixel_y": pixel_y,
        "exif_present": any_tag,
        "actual_width": width,
        "actual_height": height,
    }


def analyze_metadata(payload: bytes, *, data_mode: DataMode) -> ForensicSignal:
    reported = extract_metadata(payload)
    extra = _read_extra_exif(payload)
    findings: list[str] = []
    notes = [
        "EXIF values are reported metadata from the uploaded file.",
        "Missing EXIF is not proof of manipulation.",
        METADATA_SOURCE_LABEL,
    ]
    camera_make = reported.get("camera_make")
    camera_model = reported.get("camera_model")
    capture_timestamp = reported.get("capture_timestamp")
    software = extra.get("software")
    editor_token = _contains_token(software, EDITOR_SOFTWARE_TOKENS)
    ai_token = _contains_token(software, AI_SOFTWARE_TOKENS)

    parsed = {
        "datetime": _parse_exif_datetime(extra.get("datetime")),
        "datetime_original": _parse_exif_datetime(extra.get("datetime_original")),
        "datetime_digitized": _parse_exif_datetime(extra.get("datetime_digitized")),
    }
    available_times = [item for item in parsed.values() if item is not None]
    timestamp_mismatch = False
    if len(available_times) >= 2:
        span = max(available_times) - min(available_times)
        if span.total_seconds() > TIMESTAMP_MISMATCH_SECONDS:
            timestamp_mismatch = True
            findings.append(
                "Capture timestamps in EXIF differ by more than one day. "
                "This is a metadata inconsistency signal, not proof of manipulation."
            )

    if editor_token:
        findings.append(
            f"Software tag includes editor-related text ({editor_token}). "
            "Editor tags are common after legitimate saves and are not proof of manipulation."
        )
    if ai_token:
        findings.append(
            f"Software tag includes AI-tool-related text ({ai_token}). "
            "A software tag is not proof that the pixels were AI-generated."
        )

    camera_inconsistent = False
    if camera_make and not camera_model:
        camera_inconsistent = True
        findings.append("Camera make is present without a camera model.")
    if camera_model and not camera_make:
        camera_inconsistent = True
        findings.append("Camera model is present without a camera make.")
    if editor_token and camera_make:
        findings.append(
            "Camera make is present together with an editor software tag. "
            "This combination is a review signal only."
        )

    exif_present = bool(extra.get("exif_present")) or reported.get("status") == "METADATA_PRESENT"
    result = NO_STRONG_FORENSIC_SIGNAL
    assessable = True
    confidence = 0.42
    display = TIMESTAMP_AVAILABLE if capture_timestamp else TIMESTAMP_UNAVAILABLE

    if not exif_present:
        result = INCONCLUSIVE
        assessable = False
        confidence = 0.18
        display = EXIF_UNAVAILABLE
        notes.append("EXIF metadata is unavailable. This is not treated as manipulation.")
    elif timestamp_mismatch or camera_inconsistent or (editor_token and camera_make) or ai_token:
        result = METADATA_ANOMALY
        confidence = 0.48 if timestamp_mismatch or (editor_token and camera_make) else 0.36
        display = METADATA_ANOMALY
    elif capture_timestamp:
        result = NO_STRONG_FORENSIC_SIGNAL
        display = TIMESTAMP_AVAILABLE
        findings.append("A capture timestamp is present in reported EXIF.")
    else:
        result = INCONCLUSIVE
        assessable = False
        confidence = 0.22
        display = TIMESTAMP_UNAVAILABLE
        notes.append("No capture timestamp was present. Absence of a timestamp is not proof of manipulation.")

    details = {
        "exif_present": exif_present,
        "display": display,
        "capture_timestamp": capture_timestamp,
        "camera_make": camera_make,
        "camera_model": camera_model,
        "software": software,
        "datetime": extra.get("datetime"),
        "datetime_original": extra.get("datetime_original"),
        "datetime_digitized": extra.get("datetime_digitized"),
        "pixel_x": extra.get("pixel_x"),
        "pixel_y": extra.get("pixel_y"),
        "actual_width": extra.get("actual_width"),
        "actual_height": extra.get("actual_height"),
        "gps_available": bool(reported.get("gps_available")),
        "editor_software_token": editor_token,
        "ai_software_token": ai_token,
        "timestamp_mismatch": timestamp_mismatch,
        "reported_status": reported.get("status"),
        "source": METADATA_SOURCE_LABEL,
    }
    numeric = capped(confidence, data_mode)
    return ForensicSignal(
        name=SIGNAL_METADATA,
        result=result,
        confidence_label=confidence_label(numeric, assessable=assessable),
        confidence=numeric,
        available=exif_present,
        findings=findings,
        notes=notes,
        details=details,
    )
