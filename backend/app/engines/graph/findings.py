"""Classify Relationship Graph V1 findings.

High connectivity is not automatically a pattern of interest and is
never described as fraud.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.domain.enums import EvidenceSeverity, EvidenceStatus
from app.engines.graph.constants import (
    HIGH_CONNECTIVITY_MIN_CLUSTER,
    HIGH_CONNECTIVITY_MIN_SIMILAR,
    HYBRID_CONFIDENCE_CAP,
    INSUFFICIENT_CONFIDENCE,
    ISOLATED_CONFIDENCE,
    PATTERN_EXAMPLE_SAME_CONSTITUENCY,
    PATTERN_EXAMPLE_SAME_IDA,
    PATTERN_EXAMPLE_SIMILAR,
    PATTERN_MIN_CLOSE_DATES,
    PATTERN_MIN_SAME_CONSTITUENCY,
    PATTERN_MIN_SAME_IDA,
    PATTERN_MIN_SIMILAR,
    REAL_CONFIDENCE_CAP,
)
from app.engines.graph.types import (
    GraphFindingKind,
    GraphMode,
    GraphRecord,
    SimilarRelation,
)


def has_entity_support(record: GraphRecord) -> bool:
    return bool(
        record.mp_name.strip()
        or (record.constituency_usable and record.constituency.strip())
        or record.category.strip()
        or record.ida.strip()
        or record.state.strip()
    )


def independent_signals(
    subject: GraphRecord,
    similar: Sequence[SimilarRelation],
) -> tuple[str, ...]:
    flags: list[str] = []
    if similar:
        flags.append("semantic_similarity")
    if any(item.same_constituency for item in similar):
        flags.append("same_constituency")
    if any(item.same_category for item in similar):
        flags.append("same_category")
    if any(item.same_ida for item in similar):
        flags.append("same_ida")
    if any(item.similar_allocation for item in similar):
        flags.append("similar_allocation")
    if any(item.close_recommendation_dates for item in similar):
        flags.append("close_recommendation_dates")
    return tuple(flags)


def classify_finding(
    subject: GraphRecord,
    *,
    similar: Sequence[SimilarRelation],
    cluster_size: int,
    entity_edge_count: int,
) -> GraphFindingKind:
    similar_count = len(similar)
    same_const = sum(1 for item in similar if item.same_constituency)
    same_ida = sum(1 for item in similar if item.same_ida)
    close_dates = sum(1 for item in similar if item.close_recommendation_dates)

    if similar_count == 0 and entity_edge_count == 0 and not has_entity_support(subject):
        return GraphFindingKind.INSUFFICIENT_EVIDENCE

    example_pattern = (
        similar_count >= PATTERN_EXAMPLE_SIMILAR
        and same_const >= PATTERN_EXAMPLE_SAME_CONSTITUENCY
        and same_ida >= PATTERN_EXAMPLE_SAME_IDA
    )
    multi_signal_pattern = (
        similar_count >= PATTERN_MIN_SIMILAR
        and same_const >= PATTERN_MIN_SAME_CONSTITUENCY
        and same_ida >= PATTERN_MIN_SAME_IDA
        and close_dates >= PATTERN_MIN_CLOSE_DATES
    )
    if example_pattern or multi_signal_pattern:
        return GraphFindingKind.POTENTIAL_PATTERN_OF_INTEREST

    if similar_count >= HIGH_CONNECTIVITY_MIN_SIMILAR:
        return GraphFindingKind.HIGH_CONNECTIVITY
    if cluster_size >= HIGH_CONNECTIVITY_MIN_CLUSTER and similar_count >= 1:
        return GraphFindingKind.HIGH_CONNECTIVITY
    return GraphFindingKind.NORMAL_CONNECTIVITY


def graph_score(
    kind: GraphFindingKind,
    *,
    similar_count: int,
    same_constituency_similar: int,
    same_ida_similar: int,
    close_dates_similar: int,
    independent_signal_count: int,
) -> int | None:
    if kind == GraphFindingKind.INSUFFICIENT_EVIDENCE:
        return None
    score = 0
    score += min(40, similar_count * 6)
    score += min(20, same_constituency_similar * 4)
    score += min(20, same_ida_similar * 4)
    score += min(15, close_dates_similar * 3)
    score += min(15, independent_signal_count * 3)
    if kind == GraphFindingKind.NORMAL_CONNECTIVITY:
        score = min(score, 34)
    return int(max(0, min(100, score)))


def evidence_confidence(
    subject: GraphRecord,
    *,
    kind: GraphFindingKind,
    similar_count: int,
    mode: GraphMode,
    gps_used: bool,
) -> int:
    if kind == GraphFindingKind.INSUFFICIENT_EVIDENCE:
        return INSUFFICIENT_CONFIDENCE
    points = 18
    if subject.mp_name.strip():
        points += 6
    if subject.constituency_usable and subject.constituency.strip():
        points += 12
    if subject.category.strip():
        points += 8
    if subject.ida.strip():
        points += 10
    if subject.state.strip():
        points += 6
    if subject.recommended_date is not None:
        points += 6
    if similar_count:
        points += 10
    if similar_count == 0 and entity_edge_count_hint(subject):
        points = min(points, ISOLATED_CONFIDENCE + 8)
    cap = REAL_CONFIDENCE_CAP
    if mode == GraphMode.HYBRID_TEST:
        cap = HYBRID_CONFIDENCE_CAP
        if not gps_used:
            cap = min(cap, REAL_CONFIDENCE_CAP + 2)
    return max(0, min(cap, points))


def entity_edge_count_hint(subject: GraphRecord) -> bool:
    return has_entity_support(subject)


def status_for(kind: GraphFindingKind) -> tuple[EvidenceStatus, EvidenceSeverity, bool]:
    if kind == GraphFindingKind.POTENTIAL_PATTERN_OF_INTEREST:
        return EvidenceStatus.INCONCLUSIVE, EvidenceSeverity.ATTENTION, True
    if kind == GraphFindingKind.HIGH_CONNECTIVITY:
        return EvidenceStatus.CONSISTENT, EvidenceSeverity.WATCH, False
    if kind == GraphFindingKind.INSUFFICIENT_EVIDENCE:
        return EvidenceStatus.INCONCLUSIVE, EvidenceSeverity.INFO, False
    return EvidenceStatus.CONSISTENT, EvidenceSeverity.INFO, False
