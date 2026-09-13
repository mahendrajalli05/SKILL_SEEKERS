"""Image Evidence & Authenticity V1 constants.

Technical image signals only. Does not conclude fraud, does not compare
satellite imagery, and does not run advanced AI-image detection.
"""

from __future__ import annotations

ENGINE_NAME = "image"
ENGINE_VERSION = "image-evidence-v1"

MAX_FILE_BYTES = 10 * 1024 * 1024
THUMBNAIL_MAX_PX = 160
NEAR_DUPLICATE_MAX_DISTANCE = 10
LOW_RESOLUTION_MIN_PX = 64
LOW_RESOLUTION_PIXELS = 10_000
BLUR_VARIANCE_THRESHOLD = 50.0
METADATA_CONFIDENCE = 0.45
EXACT_DUPLICATE_CONFIDENCE = 0.95
QUALITY_CONFIDENCE = 0.7
UNAVAILABLE_CONFIDENCE = 0.2

ALLOWED_MIME_TYPES = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
    }
)
ALLOWED_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp"})
FORBIDDEN_EXTENSIONS = frozenset(
    {
        ".exe",
        ".bat",
        ".cmd",
        ".com",
        ".msi",
        ".dll",
        ".sh",
        ".ps1",
        ".js",
        ".jar",
        ".py",
        ".html",
        ".htm",
        ".svg",
        ".gif",
        ".tif",
        ".tiff",
        ".zip",
        ".rar",
        ".7z",
        ".scr",
        ".vbs",
        ".wsf",
    }
)

MIME_TO_EXTENSION = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

INTEGRITY_UNIQUE = "UNIQUE"
INTEGRITY_EXACT_DUPLICATE = "EXACT_DUPLICATE"
INTEGRITY_POTENTIAL_REUSE = "POTENTIAL_IMAGE_REUSE"
INTEGRITY_UNREADABLE = "UNREADABLE"

ANALYSIS_COMPLETE = "ANALYZED"
ANALYSIS_UNREADABLE = "UNREADABLE"
ANALYSIS_NOT_RUN = "NOT_RUN"

AUTHENTICITY_CAPABILITY = "NOT_IMPLEMENTED"
AUTHENTICITY_RESULT = "INCONCLUSIVE"

METADATA_SOURCE_LABEL = "reported metadata from uploaded file"
GPS_UNAVAILABLE_MESSAGE = "GPS metadata unavailable."
METADATA_UNAVAILABLE = "METADATA_UNAVAILABLE"
EXACT_DUPLICATE = "EXACT_DUPLICATE"
POTENTIAL_IMAGE_REUSE = "POTENTIAL_IMAGE_REUSE"

TEST_WATERMARK = "TEST DATA — SYNTHETIC image fixture. Not an official government photograph."

GOVERNANCE_NOTE = (
    "Image Evidence records officer-uploaded photographs as supporting evidence. "
    "Exact duplicate and potential reuse are technical file/visual-similarity signals "
    "for review. They are not a legal finding. EXIF GPS and timestamps are reported "
    "metadata from the uploaded file and are not independently verified. "
    "An image does not prove physical completion. Advanced authenticity analysis is "
    "INCONCLUSIVE in V1. AI recommends. Authorized officers decide."
)

AUTHENTICITY_EXPLANATION = (
    "Advanced AI-generated or manipulated-image detection is not implemented "
    "in Image Evidence V1. The capability state is NOT_IMPLEMENTED and the "
    "result is INCONCLUSIVE. No manipulation score was produced."
)

SUPPORTING_ONLY_NOTE = (
    "This photograph is supporting evidence only. It does not prove that "
    "physical work was completed."
)

EXIF_TRUST_NOTE = (
    "EXIF and GPS values are reported metadata from the uploaded file. "
    "They can be missing, edited, or incorrect and are not treated as verified location."
)
