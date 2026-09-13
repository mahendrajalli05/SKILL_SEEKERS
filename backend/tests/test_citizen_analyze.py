from __future__ import annotations

from app.engines.citizen.analyze import analyze_feedback, text_is_insufficient
from app.engines.citizen.constants import (
    ISSUE_INCOMPLETE_WORK,
    SENTIMENT_INCONCLUSIVE,
    SENTIMENT_NEGATIVE,
    SENTIMENT_POSITIVE,
)


def test_insufficient_text_is_inconclusive() -> None:
    assert text_is_insufficient("ok")
    result = analyze_feedback("ok")
    assert result.sentiment == SENTIMENT_INCONCLUSIVE
    assert result.insufficient_text is True
    assert result.grounded_in_text is False
    assert "not enough" in result.explanation.casefold()
    assert "fabricated" in result.explanation.casefold()
    assert "fraud" not in result.explanation.casefold()


def test_positive_and_incomplete_are_grounded_in_text() -> None:
    positive = analyze_feedback("The completed road is useful and in good condition for daily travel.")
    assert positive.sentiment == SENTIMENT_POSITIVE
    assert positive.grounded_in_text is True
    incomplete = analyze_feedback(
        "Road remains incomplete in section X and the surface is unfinished.",
        issue_category="incomplete_work",
        satisfaction_rating=2,
    )
    assert incomplete.issue_category == ISSUE_INCOMPLETE_WORK
    assert incomplete.sentiment == SENTIMENT_NEGATIVE
    assert "not proof of project quality" in incomplete.explanation.casefold()
    assert "fraud" not in incomplete.explanation.casefold()
