"""Query helpers for Relationship Graph V1 neighborhood stats."""

from __future__ import annotations

from collections.abc import Sequence

from app.engines.graph.index import GraphIndex
from app.engines.graph.types import (
    EdgeType,
    GraphRecord,
    GraphRelationship,
    GraphStats,
    SimilarRelation,
)


def _same_const(subject: GraphRecord, other: GraphRecord) -> bool:
    if not subject.constituency_usable or not other.constituency_usable:
        return False
    a = subject.constituency.strip().casefold()
    b = other.constituency.strip().casefold()
    return bool(a and a == b)


def _same_cat(subject: GraphRecord, other: GraphRecord) -> bool:
    a = subject.category.strip().casefold()
    b = other.category.strip().casefold()
    return bool(a and a == b)


def _same_ida(subject: GraphRecord, other: GraphRecord) -> bool:
    a = subject.ida.strip().casefold()
    b = other.ida.strip().casefold()
    return bool(a and a == b)


def cluster_density(
    subject: GraphRecord,
    cluster_members: Sequence[GraphRecord],
    similar_ids: set[int],
) -> float | None:
    members = [subject, *cluster_members]
    n = len(members)
    if n < 2:
        return None
    possible = n * (n - 1) // 2
    if possible <= 0:
        return None
    ids = {item.project_id for item in members}
    linked = 0
    for item in cluster_members:
        if item.project_id in similar_ids:
            linked += 1
    # Density among subject–peer similar edges vs possible undirected pairs.
    return round(linked / possible, 4)


def strongest_relationship(
    relationships: Sequence[GraphRelationship],
    similar: Sequence[SimilarRelation],
) -> tuple[str | None, float | None]:
    if similar:
        top = similar[0]
        return (
            f"SIMILAR_TO project {top.linked_project_id} ({top.overlap_outcome})",
            round(top.similarity_score / 100.0, 4),
        )
    entity = [rel for rel in relationships if rel.edge_type != EdgeType.SIMILAR_TO]
    if not entity:
        return None, None
    priority = {
        EdgeType.ASSOCIATED_WITH_IDA: 5,
        EdgeType.LOCATED_IN_CONSTITUENCY: 4,
        EdgeType.HAS_CATEGORY: 3,
        EdgeType.RECOMMENDED_BY: 2,
        EdgeType.IN_STATE: 1,
    }
    best = max(entity, key=lambda rel: (priority.get(rel.edge_type, 0), rel.to_node_id))
    return f"{best.edge_type.value} {best.to_node_id}", 1.0


def build_stats(
    subject: GraphRecord,
    *,
    index: GraphIndex,
    connected: Sequence[GraphRecord],
    similar: Sequence[SimilarRelation],
    cluster_peers: Sequence[GraphRecord],
    relationships: Sequence[GraphRelationship],
    independent_signals: tuple[str, ...],
) -> GraphStats:
    similar_ids = {item.linked_project_id for item in similar}
    same_const = sum(1 for item in connected if _same_const(subject, item))
    same_cat = sum(1 for item in connected if _same_cat(subject, item))
    same_ida = sum(1 for item in connected if _same_ida(subject, item))
    cluster_size = index.cluster_size(subject)
    combo_members = cluster_size
    similar_in_cluster = sum(
        1 for item in cluster_peers if item.project_id in similar_ids
    )
    strongest, strength = strongest_relationship(relationships, similar)
    entity_count = sum(1 for rel in relationships if rel.edge_type != EdgeType.SIMILAR_TO)
    similar_edge_count = sum(
        1
        for rel in relationships
        if rel.edge_type == EdgeType.SIMILAR_TO
        and (rel.from_project_id or 0) < (rel.to_project_id or 0)
    )
    if similar_edge_count == 0:
        similar_edge_count = len(similar)
    return GraphStats(
        connected_project_count=len(connected),
        similar_project_count=len(similar),
        same_constituency_count=same_const,
        same_category_count=same_cat,
        same_ida_count=same_ida,
        same_constituency_similar=sum(1 for item in similar if item.same_constituency),
        same_category_similar=sum(1 for item in similar if item.same_category),
        same_ida_similar=sum(1 for item in similar if item.same_ida),
        close_dates_similar=sum(1 for item in similar if item.close_recommendation_dates),
        similar_allocation_similar=sum(1 for item in similar if item.similar_allocation),
        cluster_size=cluster_size,
        ida_associated_project_count=index.ida_count(subject),
        constituency_associated_project_count=index.constituency_count(subject),
        repeated_combo_count=combo_members if similar_in_cluster or combo_members >= 2 else 0,
        cluster_density=cluster_density(subject, cluster_peers, similar_ids),
        independent_signal_count=len(independent_signals),
        independent_signals=independent_signals,
        strongest_relationship=strongest,
        strongest_strength=strength,
        entity_edge_count=entity_count,
        similar_edge_count=similar_edge_count,
    )
