"""Prototype work-scale grouping from observed title/category tokens.

This is an internal resolution-awareness helper, not an official MPLADS
taxonomy and not a claim about actual built area.
"""

from __future__ import annotations

from app.engines.cost.work_type import strip_observed_work_prefixes
from app.engines.satellite.constants import (
    MAX_USEFUL_GSD_M,
    SCALE_LARGE_AREA,
    SCALE_LARGE_LINEAR,
    SCALE_SMALL_STRUCTURE,
    SCALE_UNKNOWN,
)

_LINEAR = (
    "road",
    "roads",
    "highway",
    "drain",
    "drainage",
    "canal",
    "culvert",
    "street",
    "approach",
    "pathway",
    "lane",
)
_LARGE_AREA = (
    "park",
    "playground",
    "stadium",
    "ground",
    "pond",
    "tank",
    "community hall",
    "school",
    "hospital",
    "campus",
    "market",
)
_SMALL = (
    "toilet",
    "latrine",
    "borewell",
    "bore well",
    "waiting shed",
    "bus shelter",
    "hand pump",
    "dustbin",
    "gym",
    "classroom",
    "urinal",
    "shed",
)


def classify_work_scale(work_description: str | None, category: str | None = None) -> str:
    text = f"{strip_observed_work_prefixes(work_description)} {category or ''}".casefold()
    if any(token in text for token in _SMALL):
        return SCALE_SMALL_STRUCTURE
    if any(token in text for token in _LINEAR):
        return SCALE_LARGE_LINEAR
    if any(token in text for token in _LARGE_AREA):
        return SCALE_LARGE_AREA
    return SCALE_UNKNOWN


def useful_gsd_limit_m(work_scale: str) -> float:
    return MAX_USEFUL_GSD_M.get(work_scale, MAX_USEFUL_GSD_M[SCALE_UNKNOWN])
