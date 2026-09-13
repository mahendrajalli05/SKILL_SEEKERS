"""Whether an observed constituency value can be used as geography.

This is not an official Election Commission constituency master list.
Values that cannot confidently be treated as a geographic constituency are
excluded from geographic filters. The original source value is preserved
on the project record and is never replaced.
"""

from __future__ import annotations

from app.engines.cost.geography import (
    ConstituencyClassification,
    ConstituencyKind,
    classify_constituency,
)

__all__ = [
    "ConstituencyClassification",
    "ConstituencyKind",
    "classify_constituency",
    "is_geographic_constituency",
    "geographic_constituency_reason",
]


def is_geographic_constituency(value: str | None) -> bool:
    """True only when the observed value can be used as a geographic filter."""
    return classify_constituency(value).usable_as_geography


def geographic_constituency_reason(value: str | None) -> str:
    return classify_constituency(value).reason
