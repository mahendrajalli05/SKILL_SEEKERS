"""Independent forensic-signal confidence mapping.

Evidence Confidence (0–1) is separate from the signal result.
"""

from __future__ import annotations

from app.domain.enums import DataMode
from app.engines.forensics.constants import (
    CONFIDENCE_HIGH,
    CONFIDENCE_HYBRID_CAP,
    CONFIDENCE_LOW,
    CONFIDENCE_MEDIUM,
    CONFIDENCE_REAL_CAP,
    CONFIDENCE_SYNTHETIC_CAP,
    INCONCLUSIVE,
)


def mode_cap(data_mode: DataMode) -> float:
    if data_mode == DataMode.SYNTHETIC:
        return CONFIDENCE_SYNTHETIC_CAP
    if data_mode == DataMode.HYBRID:
        return CONFIDENCE_HYBRID_CAP
    return CONFIDENCE_REAL_CAP


def confidence_label(value: float, *, assessable: bool) -> str:
    if not assessable:
        return INCONCLUSIVE
    if value >= 0.75:
        return CONFIDENCE_HIGH
    if value >= 0.50:
        return CONFIDENCE_MEDIUM
    if value >= 0.25:
        return CONFIDENCE_LOW
    return INCONCLUSIVE


def capped(value: float, data_mode: DataMode) -> float:
    return round(max(0.0, min(mode_cap(data_mode), value)), 4)
