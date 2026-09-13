"""Evidence Confidence for Risk Fusion V2.

Separate from Investigation Priority. Not an average of source scores.
"""

from __future__ import annotations

from app.domain.enums import DataMode
from app.engines.fusion_v2.constants import (
    EC_COMPLETENESS_WEIGHT,
    EC_CONFLICT_PENALTY,
    EC_COVERAGE_WEIGHT,
    EC_EXTRACTION_WEIGHT,
    EC_HYBRID_CAP,
    EC_INDEPENDENCE_WEIGHT,
    EC_NONE_ASSESSABLE_CAP,
    EC_QUALITY_WEIGHT,
    EC_REAL_CAP,
    EC_RELIABILITY_WEIGHT,
    EC_SYNTHETIC_CAP,
    GROUP_CORRELATION_FAMILY,
    GROUP_NEED,
    GROUP_ORDER,
    RELIABILITY_HYBRID,
    RELIABILITY_REAL,
    RELIABILITY_SYNTHETIC,
)
from app.engines.fusion_v2.scoring import bounded_score, evidence_coverage, is_scored_state
from app.engines.fusion_v2.types import ConflictRecord, GroupContribution, V2EvidenceState


def _reliability(data_mode: DataMode) -> float:
    if data_mode == DataMode.HYBRID:
        return RELIABILITY_HYBRID
    if data_mode == DataMode.SYNTHETIC:
        return RELIABILITY_SYNTHETIC
    return RELIABILITY_REAL


def evidence_confidence(
    groups: list[GroupContribution],
    *,
    data_mode: DataMode,
    conflicts: list[ConflictRecord],
) -> int:
    """EC considers coverage, quality, independence, extraction, reliability.

    Unresolved contradictions lower confidence. Missing groups lower coverage.
    They do not invent risk.
    """
    scored = [
        item
        for item in groups
        if item.group_id != GROUP_NEED and is_scored_state(item.state)
    ]
    not_assessable = [
        item
        for item in groups
        if item.group_id != GROUP_NEED
        and item.state in {V2EvidenceState.NOT_ASSESSABLE, V2EvidenceState.INCONCLUSIVE}
        and item.confidence is not None
    ]
    catalog_n = len([group for group in GROUP_ORDER if group != GROUP_NEED])
    if not scored:
        if not not_assessable:
            return 0
        mean_c = sum(item.confidence or 0.0 for item in not_assessable) / len(not_assessable)
        return min(EC_NONE_ASSESSABLE_CAP, bounded_score(100 * 0.25 * mean_c))

    coverage = len(scored) / float(catalog_n)
    quality_num = 0.0
    quality_den = 0.0
    extraction_values: list[float] = []
    peer_values: list[float] = []
    for item in scored:
        conf = 0.0 if item.confidence is None else max(0.0, min(1.0, item.confidence))
        quality_num += item.weight * conf
        quality_den += item.weight
        extraction_values.append(conf)
        if item.peer_quality is not None:
            peer_values.append(max(0.0, min(100.0, float(item.peer_quality))) / 100.0)
    quality = (quality_num / quality_den) if quality_den else 0.0
    extraction = sum(extraction_values) / len(extraction_values) if extraction_values else 0.0
    if peer_values:
        extraction = 0.7 * extraction + 0.3 * (sum(peer_values) / len(peer_values))

    families: set[str] = set()
    for item in scored:
        families.add(GROUP_CORRELATION_FAMILY.get(item.group_id, item.group_id))
    independent_flagged = [
        item
        for item in scored
        if item.independent and item.flagged
    ]
    independence = len(families) / float(catalog_n)
    if len(independent_flagged) >= 2:
        independence = min(1.0, independence + 0.08)

    completeness = evidence_coverage(groups)
    reliability = _reliability(data_mode)
    raw = 100.0 * (
        EC_COVERAGE_WEIGHT * coverage
        + EC_QUALITY_WEIGHT * quality
        + EC_INDEPENDENCE_WEIGHT * independence
        + EC_EXTRACTION_WEIGHT * extraction
        + EC_RELIABILITY_WEIGHT * reliability
        + EC_COMPLETENESS_WEIGHT * completeness
    )
    # Low extraction/source confidence cannot produce high Evidence Confidence.
    raw *= 0.25 + 0.75 * quality
    if conflicts:
        raw *= 1.0 - min(0.45, EC_CONFLICT_PENALTY * len(conflicts))
    score = bounded_score(raw)
    if data_mode == DataMode.HYBRID:
        return min(score, EC_HYBRID_CAP)
    if data_mode == DataMode.SYNTHETIC:
        return min(score, EC_SYNTHETIC_CAP)
    return min(score, EC_REAL_CAP)
