"""Peer quality for Time Intelligence V1.

Same construction as Cost V1.1: geography tightness + title Jaccard +
category match. Raw peer count does not inflate quality.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.engines.cost.stats import median
from app.engines.cost.work_type import work_type_similarity
from app.engines.time.constants import (
    SCOPE_CONSTITUENCY_CATEGORY,
    SCOPE_CONSTITUENCY_CATEGORY_WORK_TYPE,
    SCOPE_STATE_BROADER_WORK_TYPE,
    SCOPE_STATE_CATEGORY_WORK_TYPE,
)
from app.engines.time.types import PeerQuality, PeerScope, TimePeerRecord


def compute_peer_quality(
    subject: TimePeerRecord,
    peers: Sequence[TimePeerRecord],
    scope: PeerScope | None,
) -> PeerQuality:
    if not peers or scope is None:
        return PeerQuality(
            score=0,
            rationale="No sufficient peer group was selected, so peer quality is 0.",
            median_work_type_similarity=0.0,
            category_match_rate=0.0,
        )
    sims = [
        work_type_similarity(subject.work_description, peer.work_description)
        for peer in peers
    ]
    median_sim = median(sims) if sims else 0.0
    category_matches = sum(1 for peer in peers if peer.category == subject.category)
    category_rate = category_matches / len(peers)

    if scope.id in {SCOPE_CONSTITUENCY_CATEGORY_WORK_TYPE, SCOPE_CONSTITUENCY_CATEGORY}:
        geo_points = 40
        geo_text = f"geographic constituency '{scope.geography}'"
    elif scope.id in {SCOPE_STATE_CATEGORY_WORK_TYPE, SCOPE_STATE_BROADER_WORK_TYPE}:
        geo_points = 18
        geo_text = f"Andhra Pradesh state fallback ('{scope.geography}')"
    else:
        geo_points = 0
        geo_text = scope.geography

    type_points = int(round(35 * median_sim))
    category_points = 15 if category_rate >= 0.999 else int(round(15 * category_rate))
    size_points = 10 if len(peers) >= 5 else 0
    quality = geo_points + type_points + category_points + size_points
    if median_sim < 0.35:
        quality = min(quality, 48)
    if scope.id == SCOPE_CONSTITUENCY_CATEGORY:
        quality = min(quality, 55)
    quality = int(min(100, max(0, quality)))

    rationale = (
        f"{len(peers)} peers in {geo_text}; "
        f"median work-title token Jaccard {median_sim:.2f}; "
        f"{category_matches}/{len(peers)} share category '{subject.category or '(blank)'}'. "
        f"Peer quality {quality}/100 "
        f"({'precise work-title group' if median_sim >= 0.5 else 'broader/looser work-title mix'})."
    )
    return PeerQuality(
        score=quality,
        rationale=rationale,
        median_work_type_similarity=round(median_sim, 3),
        category_match_rate=round(category_rate, 3),
    )
