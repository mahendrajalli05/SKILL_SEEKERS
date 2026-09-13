"""Text normalization for Overlap Intelligence V1.

Preserves the original source work text. Normalization is for embeddings,
blocking tokens, and place comparison only. Observed categories are not
replaced with an invented official list.
"""

from __future__ import annotations

import re
import unicodedata

from app.engines.cost.geography import classify_constituency
from app.engines.cost.work_type import (
    derive_work_type,
    normalize_observed_text,
    strip_observed_work_prefixes,
    work_type_tokens,
)
from app.engines.overlap.constants import WEAK_BLOCK_TOKENS

_PUNCT = re.compile(r"[^\w\s]+", re.UNICODE)
_WS = re.compile(r"\s+")


def preserve_source_text(value: str | None) -> str:
    """Keep the original recorded cell, only mapping None to empty."""
    if value is None:
        return ""
    return str(value)


def normalize_work_text(value: str | None) -> str:
    """Whitespace/Unicode normalisation. Does not invent wording."""
    return normalize_observed_text(value)


def embedding_text(work_description: str | None) -> str:
    """Prefix-stripped, casefolded title used for embeddings.

    Observed source prefixes such as ``NA - `` are removed so identical
    titles share a vector. The original source string is stored separately.
    """
    title = strip_observed_work_prefixes(work_description)
    if not title:
        return ""
    text = unicodedata.normalize("NFKC", title).replace("\u00a0", " ")
    text = _PUNCT.sub(" ", text)
    text = _WS.sub(" ", text).strip().casefold()
    return text


def compact_embedding_text(work_description: str | None) -> str:
    """Embedding text without spaces, for character n-grams."""
    text = embedding_text(work_description)
    return text.replace(" ", "")


def overlap_tokens(work_description: str | None) -> frozenset[str]:
    """Content tokens from the observed title. Deterministic."""
    return work_type_tokens(work_description)


def rare_block_tokens(work_description: str | None) -> frozenset[str]:
    """Tokens used for blocking. Generic title words are excluded.

    The excluded set is observed English/title filler, not a government
    category list. Titles that only contain weak tokens fall back to the
    exact embedding text as a block key.
    """
    tokens = overlap_tokens(work_description)
    rare = frozenset(token for token in tokens if token not in WEAK_BLOCK_TOKENS)
    return rare


def exact_title_key(work_description: str | None) -> str:
    return derive_work_type(work_description)


def combine_place_text(
    *,
    city: str | None = None,
    ward: str | None = None,
    block: str | None = None,
    village: str | None = None,
) -> str:
    parts = [
        normalize_observed_text(city),
        normalize_observed_text(ward),
        normalize_observed_text(block),
        normalize_observed_text(village),
    ]
    return " | ".join(part for part in parts if part)


def place_tokens(place: str | None) -> frozenset[str]:
    text = normalize_observed_text(place).casefold()
    if not text:
        return frozenset()
    tokens: set[str] = set()
    for raw in re.split(r"[^a-z0-9]+", text):
        if raw and len(raw) >= 2:
            tokens.add(raw)
    return frozenset(tokens)


def description_is_usable(work_description: str | None) -> bool:
    return bool(embedding_text(work_description))


def constituency_fields(value: str | None) -> tuple[str, bool, str, str | None]:
    classification = classify_constituency(value)
    exclusion = None if classification.usable_as_geography else classification.reason
    return (
        classification.value,
        classification.usable_as_geography,
        classification.kind.value,
        exclusion,
    )
