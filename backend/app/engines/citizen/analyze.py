"""Structured citizen-feedback analysis.

Deterministic, text-grounded. Not a chatbot. Sentiment is not proof of quality.
"""

from __future__ import annotations

import re

from app.engines.citizen.constants import (
    ALLOWED_ISSUE_CATEGORIES,
    DELAY_TOKENS,
    INCOMPLETE_TOKENS,
    ISSUE_DELAYED_WORK,
    ISSUE_INCOMPLETE_WORK,
    ISSUE_LOCATION_CONCERN,
    ISSUE_OTHER,
    ISSUE_SAFETY,
    ISSUE_WORK_QUALITY,
    LOCATION_TOKENS,
    MIN_TEXT_CHARS,
    MIN_TEXT_WORDS,
    NEGATIVE_TOKENS,
    POSITIVE_TOKENS,
    QUALITY_TOKENS,
    SAFETY_TOKENS,
    SENTIMENT_INCONCLUSIVE,
    SENTIMENT_MIXED,
    SENTIMENT_NEGATIVE,
    SENTIMENT_NEUTRAL,
    SENTIMENT_POSITIVE,
    SEVERITY_HIGH,
    SEVERITY_INCONCLUSIVE,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    SINGLE_REPORT_CONFIDENCE,
)
from app.engines.citizen.types import FeedbackAnalysis

_WORD_RE = re.compile(r"[a-z0-9]+(?:'[a-z]+)?", re.IGNORECASE)


def normalize_issue_category(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip().casefold().replace(" ", "_").replace("-", "_")
    aliases = {
        "quality": ISSUE_WORK_QUALITY,
        "workquality": ISSUE_WORK_QUALITY,
        "incomplete": ISSUE_INCOMPLETE_WORK,
        "delayed": ISSUE_DELAYED_WORK,
        "location": ISSUE_LOCATION_CONCERN,
        "other": ISSUE_OTHER,
    }
    text = aliases.get(text, text)
    if text in ALLOWED_ISSUE_CATEGORIES:
        return text
    return None


def _folded(text: str) -> str:
    return " ".join(text.casefold().split())


def text_is_insufficient(text: str | None) -> bool:
    raw = (text or "").strip()
    if len(raw) < MIN_TEXT_CHARS:
        return True
    words = _WORD_RE.findall(raw)
    return len(words) < MIN_TEXT_WORDS


def _count_hits(text: str, tokens: tuple[str, ...]) -> int:
    count = 0
    for token in tokens:
        if " " in token:
            if token in text:
                count += 1
        elif re.search(rf"\b{re.escape(token)}\b", text):
            count += 1
    return count


def infer_issue_category(text: str, supplied: str | None) -> tuple[str | None, list[str]]:
    supplied_norm = normalize_issue_category(supplied)
    extracted: list[str] = []
    mapping = (
        (INCOMPLETE_TOKENS, ISSUE_INCOMPLETE_WORK),
        (DELAY_TOKENS, ISSUE_DELAYED_WORK),
        (QUALITY_TOKENS, ISSUE_WORK_QUALITY),
        (LOCATION_TOKENS, ISSUE_LOCATION_CONCERN),
        (SAFETY_TOKENS, ISSUE_SAFETY),
    )
    for tokens, category in mapping:
        if _count_hits(text, tokens):
            extracted.append(category)
    if supplied_norm and supplied_norm not in extracted:
        extracted.insert(0, supplied_norm)
    if supplied_norm:
        return supplied_norm, extracted
    if extracted:
        return extracted[0], extracted
    if text:
        return ISSUE_OTHER, extracted
    return None, extracted


def analyze_feedback(
    observation_text: str | None,
    *,
    issue_category: str | None = None,
    satisfaction_rating: int | None = None,
) -> FeedbackAnalysis:
    raw = (observation_text or "").strip()
    if text_is_insufficient(raw):
        category = normalize_issue_category(issue_category)
        rating_note = ""
        if satisfaction_rating is not None:
            rating_note = f" A satisfaction rating of {satisfaction_rating} was recorded without enough observation text."
        return FeedbackAnalysis(
            sentiment=SENTIMENT_INCONCLUSIVE,
            issue_category=category,
            extracted_issues=[category] if category else [],
            complaint_severity=SEVERITY_INCONCLUSIVE,
            evidence_confidence=SINGLE_REPORT_CONFIDENCE,
            grounded_in_text=False,
            insufficient_text=True,
            explanation=(
                "INCONCLUSIVE. There is not enough observation text to extract sentiment "
                "or complaint themes. No complaint was fabricated."
                + rating_note
            ),
        )

    folded = _folded(raw)
    positive = _count_hits(folded, POSITIVE_TOKENS)
    negative = _count_hits(folded, NEGATIVE_TOKENS)
    if positive and negative:
        sentiment = SENTIMENT_MIXED
    elif negative > positive:
        sentiment = SENTIMENT_NEGATIVE
    elif positive > negative:
        sentiment = SENTIMENT_POSITIVE
    else:
        sentiment = SENTIMENT_NEUTRAL

    category, extracted = infer_issue_category(folded, issue_category)
    if satisfaction_rating is not None and satisfaction_rating <= 2:
        severity = SEVERITY_HIGH if negative >= 2 or category in {ISSUE_SAFETY, ISSUE_INCOMPLETE_WORK} else SEVERITY_MEDIUM
        if sentiment == SENTIMENT_NEUTRAL:
            sentiment = SENTIMENT_NEGATIVE
    elif sentiment == SENTIMENT_NEGATIVE:
        severity = SEVERITY_HIGH if negative >= 2 or category == ISSUE_SAFETY else SEVERITY_MEDIUM
    elif sentiment == SENTIMENT_MIXED:
        severity = SEVERITY_MEDIUM
    else:
        severity = SEVERITY_LOW

    confidence = 0.28
    if len(raw) >= 40:
        confidence = 0.34
    if extracted:
        confidence += 0.04
    confidence = min(0.42, confidence)

    return FeedbackAnalysis(
        sentiment=sentiment,
        issue_category=category,
        extracted_issues=extracted,
        complaint_severity=severity,
        evidence_confidence=round(confidence, 4),
        grounded_in_text=True,
        insufficient_text=False,
        explanation=(
            f"Structured analysis grounded in the submitted text. Sentiment is {sentiment}. "
            "Sentiment is not proof of project quality. No complaint was fabricated."
        ),
    )
