"""Date-window comparison for satellite evidence.

Does not claim temporal proof when acquisition dates do not match the claim.
"""

from __future__ import annotations

import calendar
import re
from datetime import date, datetime

from app.engines.satellite.constants import SATELLITE_INCONCLUSIVE, SATELLITE_CONSISTENT
from app.engines.satellite.types import ImageryScene, TemporalAnalysis

_ISO = re.compile(r"\b(20\d{2})-(\d{2})(?:-(\d{2}))?\b")
_MONTH_YEAR = re.compile(
    r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|"
    r"dec(?:ember)?)[.,]?\s+(20\d{2})\b",
    re.IGNORECASE,
)
_MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


def parse_iso_date(value: date | datetime | str | None) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        try:
            return date.fromisoformat(text[:10])
        except ValueError:
            return None
    match = _ISO.search(text)
    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3) or "1")
        try:
            return date(year, month, day)
        except ValueError:
            return None
    return None


def parse_claim_completion_date(*texts: object) -> date | None:
    blob = " ".join("" if item is None else str(item) for item in texts)
    iso = parse_iso_date(blob)
    if iso is not None and _ISO.search(blob):
        return iso
    match = _MONTH_YEAR.search(blob)
    if match:
        month = _MONTHS.get(match.group(1).casefold().rstrip("."))
        year = int(match.group(2))
        if month:
            last = calendar.monthrange(year, month)[1]
            return date(year, month, last)
    return parse_iso_date(blob)


def _scene_date(scene: ImageryScene) -> date | None:
    return parse_iso_date(scene.acquisition_date)


def analyze_temporal(
    scenes: list[ImageryScene],
    *,
    planned_date: date | None,
    claimed_completion: date | None,
    milestone_date: date | None,
) -> TemporalAnalysis:
    imagery_dates = [item.isoformat() for item in (_scene_date(scene) for scene in scenes) if item]
    parsed = [_scene_date(scene) for scene in scenes]
    parsed = [item for item in parsed if item is not None]
    claim_date = claimed_completion or milestone_date
    if not scenes:
        return TemporalAnalysis(
            result=SATELLITE_INCONCLUSIVE,
            finding="No imagery dates are available for temporal comparison.",
            explanation=(
                "Insufficient imagery evidence for temporal comparison. "
                "No acquisition dates were available."
            ),
            planned_date=planned_date.isoformat() if planned_date else None,
            claimed_completion_date=claimed_completion.isoformat() if claimed_completion else None,
            milestone_date=milestone_date.isoformat() if milestone_date else None,
            imagery_dates=imagery_dates,
            window_matches_claim=None,
        )
    if claim_date is None and planned_date is None:
        return TemporalAnalysis(
            result=SATELLITE_INCONCLUSIVE,
            finding="No planned, claimed, or milestone date is available to compare with imagery.",
            explanation=(
                "Insufficient imagery evidence for completion-date verification. "
                "Imagery dates were recorded but no claim/plan date was available."
            ),
            planned_date=None,
            claimed_completion_date=None,
            milestone_date=milestone_date.isoformat() if milestone_date else None,
            imagery_dates=imagery_dates,
            window_matches_claim=None,
        )
    reference = claim_date or planned_date
    after_or_on = [item for item in parsed if item >= reference] if reference else parsed
    if reference is not None and not after_or_on:
        latest = max(parsed)
        return TemporalAnalysis(
            result=SATELLITE_INCONCLUSIVE,
            finding=(
                f"Available imagery ({latest.isoformat()}) is earlier than the claimed/planned "
                f"date ({reference.isoformat()})."
            ),
            explanation=(
                f"INCONCLUSIVE for completion verification. Claimed or planned date: "
                f"{reference.isoformat()}. Available imagery: {latest.isoformat()}. "
                "The imagery acquisition window does not match the project claim. "
                "This is not temporal proof of completion or non-completion."
            ),
            planned_date=planned_date.isoformat() if planned_date else None,
            claimed_completion_date=claimed_completion.isoformat() if claimed_completion else None,
            milestone_date=milestone_date.isoformat() if milestone_date else None,
            imagery_dates=imagery_dates,
            window_matches_claim=False,
        )
    return TemporalAnalysis(
        result=SATELLITE_CONSISTENT,
        finding="Imagery acquisition dates are compatible with the claimed or planned window.",
        explanation=(
            "Imagery dates are on or after the claimed/planned date window. "
            "This is not proof that construction was completed."
        ),
        planned_date=planned_date.isoformat() if planned_date else None,
        claimed_completion_date=claimed_completion.isoformat() if claimed_completion else None,
        milestone_date=milestone_date.isoformat() if milestone_date else None,
        imagery_dates=imagery_dates,
        window_matches_claim=True,
    )
