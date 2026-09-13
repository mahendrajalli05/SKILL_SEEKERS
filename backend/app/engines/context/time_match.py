"""Reference-period matching for time-dependent external datasets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.engines.context.constants import NEAREST_YEAR_MAX_GAP, PROJECTION_YEARS


@dataclass
class TimeMatch:
    method: str
    selected_year: int | None
    project_year: int | None
    gap_years: int | None
    contemporaneous: bool
    conclusive: bool
    note: str


def project_year(recommended_date: date | str | None) -> int | None:
    if recommended_date is None:
        return None
    if isinstance(recommended_date, date):
        return recommended_date.year
    text = str(recommended_date).strip()
    if len(text) >= 4 and text[:4].isdigit():
        return int(text[:4])
    return None


def nearest_projection_year(year: int, years: tuple[int, ...] = PROJECTION_YEARS) -> tuple[int, int]:
    chosen = min(years, key=lambda item: (abs(item - year), item))
    return chosen, abs(chosen - year)


def match_reference_period(
    recommended_date: date | str | None,
    *,
    available_years: tuple[int, ...] = PROJECTION_YEARS,
    max_gap: int = NEAREST_YEAR_MAX_GAP,
) -> TimeMatch:
    year = project_year(recommended_date)
    if year is None:
        return TimeMatch(
            method="none",
            selected_year=None,
            project_year=None,
            gap_years=None,
            contemporaneous=False,
            conclusive=False,
            note=(
                "Project recommendation date is unavailable. A time-dependent external "
                "indicator cannot be treated as contemporaneous. The observation may still "
                "be shown with its own reference year."
            ),
        )
    chosen, gap = nearest_projection_year(year, available_years)
    if gap == 0:
        return TimeMatch(
            method="exact_year",
            selected_year=chosen,
            project_year=year,
            gap_years=0,
            contemporaneous=True,
            conclusive=True,
            note=f"External reference year {chosen} matches the project recommendation year.",
        )
    if gap <= max_gap:
        return TimeMatch(
            method="nearest_published_year",
            selected_year=chosen,
            project_year=year,
            gap_years=gap,
            contemporaneous=False,
            conclusive=True,
            note=(
                f"Nearest published projection year {chosen} was selected for project year "
                f"{year} (gap {gap} year(s)). This is an explicit documented approximation, "
                "not exact contemporaneous equivalence."
            ),
        )
    return TimeMatch(
        method="gap_exceeds_threshold",
        selected_year=chosen,
        project_year=year,
        gap_years=gap,
        contemporaneous=False,
        conclusive=False,
        note=(
            f"Nearest published year {chosen} is {gap} years from project year {year}, "
            f"which exceeds the documented maximum gap of {max_gap}. Time matching is INCONCLUSIVE. "
            "The observed series value is not treated as contemporaneous with the project."
        ),
    )
