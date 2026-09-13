"""Officer-facing Image Evidence explanations. Never a legal conclusion."""

from __future__ import annotations

from app.engines.image.constants import (
    EXACT_DUPLICATE,
    GPS_UNAVAILABLE_MESSAGE,
    METADATA_UNAVAILABLE,
    POTENTIAL_IMAGE_REUSE,
    SUPPORTING_ONLY_NOTE,
)
from app.engines.image.types import ImageAnalysis


def duplicate_finding(analysis: ImageAnalysis) -> str:
    if analysis.exact_duplicate:
        return f"{EXACT_DUPLICATE}: SHA-256 matches a previously stored image"
    if analysis.potential_reuse:
        return f"{POTENTIAL_IMAGE_REUSE}: perceptual hash is visually similar to another stored image"
    return "No exact duplicate or potential image reuse was detected"


def duplicate_explanation(analysis: ImageAnalysis) -> str:
    if analysis.exact_duplicate:
        matched = analysis.duplicate_of_id
        return (
            f"{EXACT_DUPLICATE}: this file has the same SHA-256 as image {matched}. "
            "This is a technical file-identity notice for review. It is not a legal finding. "
            f"{SUPPORTING_ONLY_NOTE}"
        )
    if analysis.potential_reuse and analysis.reuse_matches:
        first = analysis.reuse_matches[0]
        return (
            f"{POTENTIAL_IMAGE_REUSE}: {first.explanation} {SUPPORTING_ONLY_NOTE}"
        )
    return (
        "No exact duplicate file and no near-duplicate perceptual-hash match was found "
        "among stored images in the same data mode. This is not a finding of authenticity."
    )


def metadata_finding(analysis: ImageAnalysis) -> str:
    if analysis.gps_available or analysis.capture_timestamp:
        parts = []
        if analysis.capture_timestamp:
            parts.append("capture timestamp")
        if analysis.gps_available:
            parts.append("GPS")
        return "Reported image metadata present: " + " and ".join(parts)
    return METADATA_UNAVAILABLE


def metadata_explanation(analysis: ImageAnalysis) -> str:
    if analysis.gps_available or analysis.capture_timestamp:
        return (
            "Reported metadata from the uploaded file was extracted where present. "
            "EXIF GPS and timestamps are not independently verified and were not compared "
            "to satellite imagery. Missing fields were not inferred."
        )
    gps = analysis.gps_message or GPS_UNAVAILABLE_MESSAGE
    return (
        f"{METADATA_UNAVAILABLE}. {gps} Capture timestamp and camera fields were not "
        "present. Values were not inferred from the pixels."
    )


def quality_finding(analysis: ImageAnalysis) -> str:
    quality = analysis.quality or {}
    if not quality.get("readable"):
        return "Image file is unreadable"
    warnings = quality.get("warnings") or []
    if warnings:
        return "Image quality warning recorded"
    return "Image is readable with no technical quality warning"


def quality_explanation(analysis: ImageAnalysis) -> str:
    quality = analysis.quality or {}
    if not quality.get("readable"):
        return (
            "The uploaded bytes could not be decoded as an image. This is a technical "
            "readability issue, not a legal finding."
        )
    warnings = quality.get("warnings") or []
    size = ""
    if quality.get("width") and quality.get("height"):
        size = f" Dimensions {quality['width']}×{quality['height']}."
    extra = " ".join(str(item) for item in warnings)
    return (
        f"Basic technical quality checks ran.{size} {extra} "
        "Poor image quality is not treated as wrongdoing. "
        f"{analysis.authenticity.explanation}"
    ).strip()
