"""Local evidence-confidence for satellite findings.

This is not fused Evidence Confidence and does not raise Investigation Priority.
"""

from __future__ import annotations

from app.domain.enums import DataMode
from app.engines.satellite.constants import (
    HYBRID_CONFIDENCE_CAP,
    REAL_CONFIDENCE_CAP,
    SATELLITE_UNAVAILABLE,
    SYNTHETIC_CONFIDENCE_CAP,
    UNAVAILABLE_CONFIDENCE,
)


def mode_cap(data_mode: DataMode) -> float:
    if data_mode == DataMode.SYNTHETIC:
        return SYNTHETIC_CONFIDENCE_CAP
    if data_mode == DataMode.HYBRID:
        return HYBRID_CONFIDENCE_CAP
    return REAL_CONFIDENCE_CAP


def confidence_label(value: float) -> str:
    if value >= 0.40:
        return "MEDIUM"
    return "LOW"


def satellite_confidence(
    *,
    data_mode: DataMode,
    overall: str,
    imagery_available: bool,
    resolution_sufficient: bool | None,
    labelled_synthetic: bool,
    official_imagery: bool,
) -> float:
    if overall == SATELLITE_UNAVAILABLE or not imagery_available:
        return UNAVAILABLE_CONFIDENCE
    score = 0.28
    if resolution_sufficient is True:
        score += 0.10
    if official_imagery and not labelled_synthetic:
        score += 0.08
    if labelled_synthetic:
        score -= 0.04
    if resolution_sufficient is False:
        score = min(score, 0.22)
    return round(min(mode_cap(data_mode), max(UNAVAILABLE_CONFIDENCE, score)), 3)
