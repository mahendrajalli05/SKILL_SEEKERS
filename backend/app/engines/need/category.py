"""Observed work-type essential-service mapping.

Prototype mapping from recorded category and work description.
This is not an official MPLADS sector taxonomy and not a census need measure.
"""

from __future__ import annotations

from app.engines.cost.work_type import normalize_observed_text, work_type_tokens
from app.engines.need.constants import (
    DISASTER_TOKENS,
    ESSENTIAL_HIGH_TOKENS,
    ESSENTIAL_LOW_TOKENS,
    ESSENTIAL_MEDIUM_TOKENS,
    ESSENTIAL_SERVICE_HIGH_SCORE,
    ESSENTIAL_SERVICE_LOW_SCORE,
    ESSENTIAL_SERVICE_MEDIUM_SCORE,
    HIGH_CATEGORY_TOKENS,
    LOW_CATEGORY_TOKENS,
    MEDIUM_CATEGORY_TOKENS,
)


def _category_band(category: str | None) -> str | None:
    text = normalize_observed_text(category).casefold()
    if not text:
        return None
    if any(token in text for token in HIGH_CATEGORY_TOKENS):
        return "high"
    if any(token in text for token in LOW_CATEGORY_TOKENS):
        return "low"
    if any(token in text for token in MEDIUM_CATEGORY_TOKENS):
        return "medium"
    return None


def _token_band(tokens: frozenset[str]) -> str | None:
    if tokens & ESSENTIAL_HIGH_TOKENS:
        return "high"
    if tokens & ESSENTIAL_LOW_TOKENS:
        return "low"
    if tokens & ESSENTIAL_MEDIUM_TOKENS:
        return "medium"
    return None


def essential_service_relevance(
    category: str | None,
    work_description: str | None,
) -> tuple[float | None, str, str]:
    """Return (score, band, explanation) from observed text only.

    Missing/unmatched category and description → unavailable, not a default score.
    """
    category_band = _category_band(category)
    tokens = work_type_tokens(work_description)
    token_band = _token_band(tokens)
    band = category_band or token_band
    if category_band == "high" or token_band == "high":
        band = "high"
    elif category_band == "low" and token_band != "medium" and token_band != "high":
        band = "low"
    elif category_band == "medium" or token_band == "medium":
        band = "medium"
    if band == "high":
        return (
            ESSENTIAL_SERVICE_HIGH_SCORE,
            "high",
            "Observed category/description matches a prototype essential-service "
            "group (water, health, education, or sanitation). This is work-type "
            "relevance, not a census community-need measure.",
        )
    if band == "medium":
        return (
            ESSENTIAL_SERVICE_MEDIUM_SCORE,
            "medium",
            "Observed category/description matches a prototype general public-facility "
            "group. This is work-type relevance, not a census community-need measure.",
        )
    if band == "low":
        return (
            ESSENTIAL_SERVICE_LOW_SCORE,
            "low",
            "Observed category/description matches a prototype low essential-service "
            "group (for example beautification or commemorative works). This is "
            "work-type relevance, not a census community-need measure.",
        )
    return (
        None,
        "unavailable",
        "Essential-service relevance is unavailable: observed category and work "
        "description do not match the documented prototype mapping. No default "
        "was invented.",
    )


def disaster_text_flag(work_description: str | None, category: str | None = None) -> bool:
    tokens = work_type_tokens(work_description) | work_type_tokens(category)
    return bool(tokens & DISASTER_TOKENS)
