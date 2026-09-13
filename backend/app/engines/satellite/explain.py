"""Officer-facing explanations. No fraud or false-certainty wording."""

from __future__ import annotations

from app.engines.satellite.constants import (
    SATELLITE_CONSISTENT,
    SATELLITE_INCONCLUSIVE,
    SATELLITE_INCONSISTENT,
    SATELLITE_UNAVAILABLE,
)
from app.engines.satellite.types import (
    ChangeAnalysis,
    LocationAnalysis,
    ResolutionAnalysis,
    TemporalAnalysis,
)


def overall_finding(overall: str) -> str:
    if overall == SATELLITE_CONSISTENT:
        return "Consistent with available imagery"
    if overall == SATELLITE_INCONSISTENT:
        return "Inconsistent with available imagery"
    if overall == SATELLITE_UNAVAILABLE:
        return "Satellite imagery is unavailable"
    return "Insufficient imagery evidence"


def build_explanation(
    *,
    overall: str,
    unavailable_reason: str | None,
    location: LocationAnalysis | None,
    resolution: ResolutionAnalysis | None,
    temporal: TemporalAnalysis | None,
    change: ChangeAnalysis | None,
    labelled_synthetic: bool,
) -> str:
    parts: list[str] = [overall_finding(overall) + "."]
    if unavailable_reason:
        parts.append(unavailable_reason)
    if location is not None:
        parts.append(location.explanation)
    if resolution is not None:
        parts.append(resolution.explanation)
    if temporal is not None:
        parts.append(temporal.explanation)
    if change is not None:
        parts.append(change.explanation)
    parts.append(
        "This layer does not determine legal wrongdoing or independently verified physical completion."
    )
    if labelled_synthetic:
        parts.append(
            "TEST/SYNTHETIC mocked imagery metadata is not official satellite imagery."
        )
    return " ".join(part.strip() for part in parts if part and part.strip())
