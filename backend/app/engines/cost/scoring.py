"""Allocation Cost Anomaly score (0–100) from log-robust peer statistics.

Mapping (documented in COST_V1_1_REPORT.md):

1. Display baseline stays the original-scale peer median.
2. Scoring uses natural logs of positive allocations.
3. If log-MAD > 0:
     z = 0.6745 * (ln(actual) - median(ln(peers))) / MAD(ln(peers))
     score = min(100, round(100 * |z| / 3.5))
   The 3.5 is the Iglewicz-Hoaglin modified-z reference. Score 60 is |z|≈2.1.
4. If log-MAD = 0 (identical peer amounts):
     score = min(100, round(100 * |ln(actual/median)| / ln(4)))
   A 4× (or ¼×) ratio maps to 100. Equal amounts map to 0.
5. The score is monotonic in |ln(actual/median)| for a fixed peer set.

This is not a fused Investigation Priority and not an expenditure finding.
"""

from __future__ import annotations

import math

from app.engines.cost.constants import (
    FLAG_SCORE_THRESHOLD,
    IDENTICAL_PEER_RATIO_FOR_MAX,
    LOOSE_WORK_TYPE_SIMILARITY,
    MODIFIED_Z_REFERENCE,
    SCOPE_CONFIDENCE_BASE,
)
from app.engines.cost.types import PeerStatistics

_Z_CONSTANT = 0.6745


def deviation_percentage(actual: float, baseline: float) -> float:
    """Signed percent difference from median. Rounded to one decimal."""
    if baseline <= 0:
        raise ValueError("baseline must be positive to compute deviation.")
    raw = (actual - baseline) / baseline * 100.0
    return round(raw, 1)


def modified_z_score(actual: float, median: float, mad: float) -> float | None:
    """Iglewicz-Hoaglin modified z-score. None when MAD is zero."""
    if mad <= 0:
        return None
    return _Z_CONSTANT * (actual - median) / mad


def _clip_score(value: float) -> int:
    return int(round(min(100.0, max(0.0, value))))


def cost_anomaly_score(
    actual: float,
    stats: PeerStatistics,
    *,
    median_work_type_similarity: float = 1.0,
) -> tuple[int, float, float | None, str]:
    """Return (score 0–100, signed deviation %, modified z or None, method).

    Log-MAD modified z is used only when the peer titles are similar enough
    that a tight amount cluster is meaningful. Loose category mixes fall back
    to a multiplicative log-ratio so round-number clustering cannot force 100.
    """
    if actual <= 0:
        raise ValueError("actual allocation must be positive.")
    if stats.median <= 0:
        raise ValueError("peer median must be positive.")
    dev = deviation_percentage(actual, stats.median)
    log_actual = math.log(actual)
    use_modified_z = (
        stats.log_mad > 0 and median_work_type_similarity >= LOOSE_WORK_TYPE_SIMILARITY
    )
    if use_modified_z:
        z = _Z_CONSTANT * (log_actual - stats.log_median) / stats.log_mad
        score = _clip_score(100.0 * abs(z) / MODIFIED_Z_REFERENCE)
        return score, dev, z, "log_modified_z"
    if actual == stats.median:
        return 0, 0.0, 0.0, "equal_to_median"
    log_ratio = abs(log_actual - math.log(stats.median))
    denom = math.log(IDENTICAL_PEER_RATIO_FOR_MAX)
    score = _clip_score(100.0 * log_ratio / denom)
    method = (
        "log_ratio_identical_peers"
        if stats.log_mad <= 0
        else "log_ratio_loose_work_type"
    )
    return score, dev, None, method


def is_cost_anomaly(score: int) -> bool:
    return score >= FLAG_SCORE_THRESHOLD


def evidence_confidence(
    *,
    scope_id: str | None,
    peer_count: int,
    mad: float | None,
    valid_amount: bool,
    peer_quality: int = 0,
    constituency_usable: bool = True,
) -> int:
    """Evidence Confidence is separate from Cost Anomaly.

    Large loose peer groups do not inflate confidence. Peer quality is the
    main driver after a valid amount and a usable scope.
    """
    if not valid_amount:
        return 0
    if scope_id is None:
        return int(min(15, max(5, peer_quality // 5 or max(5, peer_count * 2))))
    base = SCOPE_CONFIDENCE_BASE[scope_id]
    quality = max(0, min(100, peer_quality))
    raw = 0.40 * base + 0.60 * quality
    if scope_id == "constituency_category":
        raw = min(raw, 52)
    if scope_id == "state_broader_work_type":
        raw = min(raw, 58)
    if not constituency_usable:
        raw = min(raw, 60)
    if mad is not None and mad == 0 and quality < 50:
        raw = min(raw, 45)
    return int(min(90, max(5, round(raw))))
