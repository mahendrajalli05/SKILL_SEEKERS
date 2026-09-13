"""Geospatial Consistency V1 constants.

Location consistency check only. Does not prove authenticity, completion,
or that a photograph depicts the claimed work. Does not download satellite imagery.
"""

from __future__ import annotations

ENGINE_NAME = "geo"
ENGINE_VERSION = "geospatial-consistency-v1"

EARTH_RADIUS_M = 6_371_000.0
DEFAULT_THRESHOLD_METERS = 500.0

LOCATION_CONSISTENT = "LOCATION_CONSISTENT"
LOCATION_MISMATCH = "LOCATION_MISMATCH"
INCONCLUSIVE = "INCONCLUSIVE"

LOCATION_UNAVAILABLE = "LOCATION_UNAVAILABLE"
GPS_METADATA_UNAVAILABLE = "GPS_METADATA_UNAVAILABLE"
SATELLITE_VERIFICATION_NOT_AVAILABLE = "SATELLITE_VERIFICATION_NOT_AVAILABLE"

IMAGE_GPS_SOURCE_LABEL = "Reported GPS metadata from uploaded file"
PROJECT_GPS_SYNTHETIC_SOURCE = (
    "SYNTHETIC hybrid enrichment coordinates. Not official MPLADS GPS."
)
PROJECT_GPS_UNAVAILABLE_SOURCE = (
    "Project coordinates are unavailable in the current public MPLADS extract."
)

THRESHOLD_NOTE = (
    "Prototype/business-rule setting only. This is not a claim that MPLADS "
    "officially uses a 500 metre verification radius."
)

GOVERNANCE_NOTE = (
    "Geospatial Consistency V1 is a location consistency check. It is not proof "
    "of project authenticity, physical completion, or that a photograph depicts "
    "the claimed work. Image GPS is reported metadata from the uploaded file. "
    "SYNTHETIC hybrid coordinates are not official MPLADS GPS. Missing GPS is "
    "not treated as a location mismatch. AI recommends. Authorized officers decide."
)

SATELLITE_EXPLANATION = (
    "Satellite verification is not available in Geospatial Consistency V1. "
    "No satellite imagery was downloaded or processed. The capability result is "
    "SATELLITE_VERIFICATION_NOT_AVAILABLE. No satellite measurement was fabricated."
)

CLAIM_AT_SITE = "Progress photograph was taken at the project site."

PCE_CONTENT_NOTE = (
    "Location consistency does not prove the photograph depicts the claimed work. "
    "Later image/content verification is required for that question."
)

MIXED_IMAGES_NOTE = (
    "One matching image does not make every other image trustworthy."
)

MISSING_GPS_NOT_MISMATCH = (
    "Missing GPS is not treated as a location mismatch. The result is INCONCLUSIVE."
)

REAL_LOCATION_UNAVAILABLE = (
    "INCONCLUSIVE / LOCATION UNAVAILABLE. The current real MPLADS work-level "
    "extract does not contain verified project latitude/longitude. "
    "Project coordinates were not invented. Missing GPS is not a location mismatch."
)

HYBRID_SYNTHETIC_LABEL = "SYNTHETIC"

LIMITATIONS = (
    "This is a location consistency check, not proof of project authenticity.",
    "GPS consistency does not prove physical completion.",
    "GPS consistency does not prove the photograph depicts the claimed work.",
    "Image GPS is reported metadata from the uploaded file, not independently verified truth.",
    "The current real MPLADS extract does not contain verified project coordinates.",
    "SYNTHETIC hybrid coordinates are not official MPLADS GPS.",
    "Satellite verification is not available in V1.",
    "Missing GPS is not treated as a location mismatch.",
    "One matching image does not make other images trustworthy.",
)

# Local Evidence Confidence caps. Matching GPS does not raise overall project confidence.
REAL_CONFIDENCE_CAP = 0.50
HYBRID_CONFIDENCE_CAP = 0.40
SYNTHETIC_CONFIDENCE_CAP = 0.35
UNAVAILABLE_CONFIDENCE = 0.18
REPORTED_METADATA_CONFIDENCE = 0.45
SYNTHETIC_PROJECT_LOCATION_CONFIDENCE = 0.35

