"""Lightweight lexical retrieval over officer-facing text.

Used only for documents, citizen observations, and evidence explanations.
Does not vectorize the whole database.
"""

from __future__ import annotations

import re

from app.copilot.constants import MAX_SEMANTIC_HITS

_TOKEN = re.compile(r"[a-z0-9]{3,}")


def tokenize(text: str) -> set[str]:
    return set(_TOKEN.findall((text or "").casefold()))


def score_overlap(query: str, document: str) -> float:
    left = tokenize(query)
    right = tokenize(document)
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def rank_texts(
    query: str,
    items: list[dict[str, str]],
    *,
    limit: int = MAX_SEMANTIC_HITS,
) -> list[dict[str, str]]:
    scored: list[tuple[float, dict[str, str]]] = []
    for item in items:
        blob = " ".join(str(item.get(key) or "") for key in ("title", "text", "id"))
        score = score_overlap(query, blob)
        if score <= 0:
            continue
        scored.append((score, item))
    scored.sort(key=lambda pair: (-pair[0], pair[1].get("id") or ""))
    return [item for _score, item in scored[:limit]]
