"""Satellite / Remote-Sensing Consistency V1 constants.

Decision-support imagery evidence only. Does not determine legal wrongdoing,
completion, independently verified physical measurements, or authenticity.
Does not modify Risk Fusion V1.1.
"""

from __future__ import annotations

ENGINE_NAME = "satellite"
ENGINE_VERSION = "satellite-remote-sensing-v1"

SATELLITE_CONSISTENT = "SATELLITE_CONSISTENT"
SATELLITE_INCONSISTENT = "SATELLITE_INCONSISTENT"
SATELLITE_INCONCLUSIVE = "SATELLITE_INCONCLUSIVE"
SATELLITE_UNAVAILABLE = "SATELLITE_UNAVAILABLE"

EVIDENCE_AVAILABILITY = "SATELLITE_AVAILABILITY"
EVIDENCE_LOCATION = "SATELLITE_LOCATION"
EVIDENCE_CHANGE = "SATELLITE_CHANGE"
EVIDENCE_TEMPORAL = "SATELLITE_TEMPORAL"
EVIDENCE_INCONCLUSIVE = "SATELLITE_INCONCLUSIVE"

PROVIDER_UNAVAILABLE = "unavailable"
PROVIDER_MOCK = "mock"

MOCK_PROVIDER_NAME = "test-mock"
MOCK_PROVIDER_LABEL = (
    "TEST/SYNTHETIC mocked provider response. "
    "Not official government or commercial satellite imagery."
)

SCALE_SMALL_STRUCTURE = "SMALL_STRUCTURE"
SCALE_LARGE_AREA = "LARGE_AREA"
SCALE_LARGE_LINEAR = "LARGE_LINEAR"
SCALE_UNKNOWN = "UNKNOWN"

# Prototype useful-GSD ceilings in metres. Not official remote-sensing standards.
MAX_USEFUL_GSD_M = {
    SCALE_SMALL_STRUCTURE: 1.0,
    SCALE_LARGE_AREA: 5.0,
    SCALE_LARGE_LINEAR: 10.0,
    SCALE_UNKNOWN: 2.0,
}

DEFAULT_AOI_RADIUS_M = 500.0
HIGH_CLOUD_COVER_PERCENT = 70.0

RESOLUTION_INSUFFICIENT_TEXT = (
    "Imagery resolution is insufficient for reliable physical verification."
)

UNAVAILABLE_NO_PROVIDER = (
    "No reliable satellite imagery source or API is configured. "
    "The result is SATELLITE_UNAVAILABLE. No satellite imagery was fabricated."
)

UNAVAILABLE_NO_COORDINATES = (
    "Project coordinates are unavailable, so imagery cannot be requested for the claimed site. "
    "Project GPS was not invented. The result is SATELLITE_UNAVAILABLE."
)

UNAVAILABLE_NO_SCENES = (
    "No satellite imagery is available for the requested coordinates and date window. "
    "Unrelated imagery was not substituted. The result is SATELLITE_UNAVAILABLE."
)

GOVERNANCE_NOTE = (
    "Satellite / Remote-Sensing Consistency V1 is a decision-support evidence layer. "
    "It does not determine legal wrongdoing, project completion, exact construction "
    "measurements, or authenticity. Prefer: consistent with available imagery, "
    "inconsistent with available imagery, or insufficient imagery evidence. "
    "AI recommends. Authorized officers decide."
)

PCE_CLAIM_NOT_FALSE_NOTE = (
    "Satellite evidence does not automatically mark the claim false. "
    "An authorized officer decides."
)

DEFAULT_SITE_CLAIM = "The claimed work is present at the recorded project location."

REAL_CONFIDENCE_CAP = 0.45
HYBRID_CONFIDENCE_CAP = 0.35
SYNTHETIC_CONFIDENCE_CAP = 0.30
UNAVAILABLE_CONFIDENCE = 0.12

FORBIDDEN_OVERCLAIM_PATTERN = (
    r"\b(fraudulent|construction definitely completed|building definitely exists|"
    r"definitely exists|exact dimensions verified|exact floor count|"
    r"satellite (proves|proof)|definitely completed)\b"
)

LIMITATIONS = (
    "No live government or commercial satellite API is configured in V1 by default.",
    "Unavailable imagery is reported as SATELLITE_UNAVAILABLE. Imagery is never fabricated.",
    "TEST/SYNTHETIC mocked provider responses are not official satellite imagery.",
    "Spatial resolution may be insufficient for small structures.",
    "Imagery dates that do not match the claim window cannot verify completion.",
    "Visible site-level change is not exact quantity, floor-count, or expenditure proof.",
    "Project GPS, image GPS, and satellite coverage are separate signals.",
    "Satellite evidence is not fused into Investigation Priority (Risk Fusion V1.1).",
)

SCENARIO_UNAVAILABLE = "unavailable"
SCENARIO_AVAILABLE = "available"
SCENARIO_MATCHING_LOCATION = "matching_location"
SCENARIO_WRONG_LOCATION = "wrong_location"
SCENARIO_CHANGE_DETECTED = "change_detected"
SCENARIO_NO_CHANGE = "no_change"
SCENARIO_INSUFFICIENT_RESOLUTION = "insufficient_resolution"
SCENARIO_WRONG_DATE = "wrong_date"

ALLOWED_TEST_SCENARIOS = (
    SCENARIO_UNAVAILABLE,
    SCENARIO_AVAILABLE,
    SCENARIO_MATCHING_LOCATION,
    SCENARIO_WRONG_LOCATION,
    SCENARIO_CHANGE_DETECTED,
    SCENARIO_NO_CHANGE,
    SCENARIO_INSUFFICIENT_RESOLUTION,
    SCENARIO_WRONG_DATE,
)
