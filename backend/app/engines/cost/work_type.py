"""Derived work-type keys from observed MPLADS work/category fields.

This is an internal grouping key, not an official government category list.
Prefixes such as ``NA - `` and ``WS/MP…/YYYY-YYYY/n - `` are source-text
patterns observed in the cleaned extract; they are stripped so identical
titles group together. No new sector taxonomy is invented.
"""

from __future__ import annotations

import re
import unicodedata

# Observed source prefixes on WORK text. Not official work IDs.
_SOURCE_PREFIX = re.compile(
    r"^(?:NA\s*-\s*|WS/[A-Z0-9]+/\d{4}-\d{4}/\d+\s*-\s*)",
    re.IGNORECASE,
)


def normalize_observed_text(value: str | None) -> str:
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def strip_observed_work_prefixes(work_description: str | None) -> str:
    """Remove observed source prefixes; keep the remaining title text."""
    text = normalize_observed_text(work_description)
    if not text:
        return ""
    while True:
        stripped = _SOURCE_PREFIX.sub("", text, count=1).strip()
        if stripped == text:
            return stripped
        text = stripped


# Deterministic content-token filter. Not an official taxonomy.
_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "of",
        "and",
        "or",
        "for",
        "in",
        "on",
        "to",
        "with",
        "without",
        "any",
        "other",
        "by",
        "from",
        "at",
        "into",
        "over",
        "as",
        "is",
        "are",
    }
)
_TOKEN_SPLIT = re.compile(r"[^a-z0-9]+")


def derive_work_type(work_description: str | None) -> str:
    """Lowercased, prefix-stripped work title used as a peer grouping key."""
    title = strip_observed_work_prefixes(work_description)
    return title.casefold()


def _normalize_token(token: str) -> str:
    """Light plural strip so 'roads' and 'road' share a token. Not stemming ML."""
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def work_type_tokens(work_description: str | None) -> frozenset[str]:
    """Content tokens from the observed title. Deterministic and reproducible."""
    title = derive_work_type(work_description)
    if not title:
        return frozenset()
    tokens: set[str] = set()
    for raw in _TOKEN_SPLIT.split(title):
        if not raw or raw in _STOPWORDS or len(raw) < 2:
            continue
        tokens.add(_normalize_token(raw))
    return frozenset(tokens)


def work_type_similarity(left: str | None, right: str | None) -> float:
    """Jaccard similarity of content tokens. Exact titles score 1.0.

    Empty titles do not match. This is not an official project-type code.
    """
    left_title = derive_work_type(left)
    right_title = derive_work_type(right)
    if not left_title or not right_title:
        return 0.0
    if left_title == right_title:
        return 1.0
    left_tokens = work_type_tokens(left_title)
    right_tokens = work_type_tokens(right_title)
    if not left_tokens or not right_tokens:
        return 0.0
    union = left_tokens | right_tokens
    return len(left_tokens & right_tokens) / len(union)


def work_type_representation(
    *,
    category: str | None,
    work_description: str | None,
) -> str:
    """Reusable observed representation: recorded category plus derived title.

    Does not invent a government code. Empty parts are omitted.
    """
    observed_category = normalize_observed_text(category)
    derived = derive_work_type(work_description)
    parts = [part for part in (observed_category, derived) if part]
    return " | ".join(parts)
