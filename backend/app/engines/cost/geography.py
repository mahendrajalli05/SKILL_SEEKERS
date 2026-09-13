"""Observed-text classification of MPLADS constituency values.

This is not an official Election Commission constituency list.
Values that are clearly chamber/house labels are excluded from geographic
peer grouping. Remaining named values are treated as place-like working
labels only.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.engines.cost.work_type import normalize_observed_text


class ConstituencyKind(str, Enum):
    GEOGRAPHIC = "geographic"
    NON_GEOGRAPHIC = "non_geographic"
    UNUSABLE = "unusable"


# Observed in the cleaned extract. Not an official gazetteer.
_NON_GEOGRAPHIC_SUBSTRINGS = (
    "rajya sabha",
    "lok sabha",
)

_NON_GEOGRAPHIC_EXACT = frozenset(
    {
        "nominated",
        "sitting",
        "nominated rajya sabha",
        "sitting rajya sabha",
    }
)


@dataclass(frozen=True)
class ConstituencyClassification:
    value: str
    kind: ConstituencyKind
    usable_as_geography: bool
    reason: str


def classify_constituency(value: str | None) -> ConstituencyClassification:
    """Classify a recorded CONSTITUENCY cell for peer geography.

    Conservative rule: exclude values that are blank or that name a
    parliamentary house/chamber. Do not invent an official PC list for the rest.
    """
    text = normalize_observed_text(value)
    if not text:
        return ConstituencyClassification(
            value="",
            kind=ConstituencyKind.UNUSABLE,
            usable_as_geography=False,
            reason="Constituency is blank, so it cannot be used as geographic peer scope.",
        )
    folded = text.casefold()
    if folded in _NON_GEOGRAPHIC_EXACT or any(token in folded for token in _NON_GEOGRAPHIC_SUBSTRINGS):
        return ConstituencyClassification(
            value=text,
            kind=ConstituencyKind.NON_GEOGRAPHIC,
            usable_as_geography=False,
            reason=(
                f"'{text}' is a parliamentary house/chamber label in the extract, "
                "not a geographic parliamentary constituency. It is excluded from "
                "constituency-level geography."
            ),
        )
    letters = sum(1 for char in text if char.isalpha())
    if letters < 2:
        return ConstituencyClassification(
            value=text,
            kind=ConstituencyKind.UNUSABLE,
            usable_as_geography=False,
            reason=(
                f"'{text}' does not contain enough alphabetic characters to treat "
                "as a geographic constituency."
            ),
        )
    return ConstituencyClassification(
        value=text,
        kind=ConstituencyKind.GEOGRAPHIC,
        usable_as_geography=True,
        reason=(
            f"'{text}' is treated as a place-like constituency label for peer "
            "geography. It is not validated against an official constituency list."
        ),
    )
