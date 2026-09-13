"""Entity edge construction for Relationship Graph V1.

Only relationships supported by observed fields are created.
Non-geographic constituency labels do not produce LOCATED_IN_CONSTITUENCY.
"""

from __future__ import annotations

from app.engines.graph.nodes import constituency_node, entity_node_id, make_entity_node, project_node_id
from app.engines.graph.types import EdgeType, GraphRecord, GraphRelationship, NodeType


ENTITY_EDGE_SPECS: tuple[tuple[EdgeType, NodeType, str], ...] = (
    (EdgeType.RECOMMENDED_BY, NodeType.MP, "mp_name"),
    (EdgeType.HAS_CATEGORY, NodeType.CATEGORY, "category"),
    (EdgeType.ASSOCIATED_WITH_IDA, NodeType.IDA, "ida"),
    (EdgeType.IN_STATE, NodeType.STATE, "state"),
)


def entity_relationships_for(record: GraphRecord) -> list[GraphRelationship]:
    edges: list[GraphRelationship] = []
    source = project_node_id(record.project_id)
    for edge_type, node_type, field_name in ENTITY_EDGE_SPECS:
        label = getattr(record, field_name)
        node = make_entity_node(node_type, label)
        if node is None:
            continue
        edges.append(
            GraphRelationship(
                from_node_id=source,
                to_node_id=node.node_id,
                edge_type=edge_type,
                strength=1.0,
                from_project_id=record.project_id,
                attributes={"observed_field": field_name},
            )
        )
    constituency = constituency_node(record)
    if constituency is not None:
        edges.append(
            GraphRelationship(
                from_node_id=source,
                to_node_id=constituency.node_id,
                edge_type=EdgeType.LOCATED_IN_CONSTITUENCY,
                strength=1.0,
                from_project_id=record.project_id,
                attributes={"observed_field": "constituency", "geographic": True},
            )
        )
    return edges


def similar_relationship(
    subject: GraphRecord,
    other: GraphRecord,
    *,
    similarity_score: float,
    semantic_similarity: float | None,
    same_constituency: bool | None,
    same_category: bool | None,
    same_ida: bool,
    similar_allocation: bool | None,
    close_recommendation_dates: bool,
    date_gap_days: int | None,
    overlap_outcome: str,
    gps_distance_m: float | None,
) -> GraphRelationship:
    left_id, right_id = subject.project_id, other.project_id
    if left_id <= right_id:
        from_record, to_record = subject, other
    else:
        from_record, to_record = other, subject
    strength = max(0.0, min(1.0, float(similarity_score) / 100.0))
    return GraphRelationship(
        from_node_id=project_node_id(from_record.project_id),
        to_node_id=project_node_id(to_record.project_id),
        edge_type=EdgeType.SIMILAR_TO,
        strength=round(strength, 4),
        from_project_id=from_record.project_id,
        to_project_id=to_record.project_id,
        same_constituency=same_constituency,
        same_category=same_category,
        same_ida=same_ida,
        similar_allocation=similar_allocation,
        close_recommendation_dates=close_recommendation_dates,
        semantic_similarity=semantic_similarity,
        similarity_score=similarity_score,
        date_gap_days=date_gap_days,
        overlap_outcome=overlap_outcome,
        gps_distance_m=gps_distance_m,
        attributes={
            "observed_field": "overlap_intelligence",
            "engine": "overlap-multi-v1",
        },
    )


def ida_node_id(ida: str) -> str | None:
    return entity_node_id(NodeType.IDA, ida)
