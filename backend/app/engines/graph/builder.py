"""NetworkX ego-graph builder for Relationship Graph V1.

Constructs a neighborhood around one project. Does not build a fully
connected 56,138-node graph.
"""

from __future__ import annotations

from collections.abc import Sequence

import networkx as nx

from app.engines.graph.constants import MAX_DISPLAY_NODES, MAX_DISPLAY_RELATIONSHIPS
from app.engines.graph.edges import entity_relationships_for, similar_relationship
from app.engines.graph.nodes import entity_nodes_for, make_project_node
from app.engines.graph.types import (
    EdgeType,
    GraphNode,
    GraphRecord,
    GraphRelationship,
    NodeType,
    SimilarRelation,
)


def _node_payload(node: GraphNode) -> dict[str, object]:
    payload: dict[str, object] = {
        "node_id": node.node_id,
        "node_type": node.node_type.value,
        "label": node.label,
        "project_id": node.project_id,
        "internal_project_id": node.internal_project_id,
    }
    payload.update(node.attributes)
    return payload


def _add_node(graph: nx.MultiDiGraph, node: GraphNode) -> None:
    if node.node_id in graph:
        return
    graph.add_node(node.node_id, **_node_payload(node))


def _add_edge(graph: nx.MultiDiGraph, rel: GraphRelationship) -> None:
    key = rel.edge_type.value
    graph.add_edge(
        rel.from_node_id,
        rel.to_node_id,
        key=key,
        edge_type=rel.edge_type.value,
        strength=rel.strength,
        from_project_id=rel.from_project_id,
        to_project_id=rel.to_project_id,
        same_constituency=rel.same_constituency,
        same_category=rel.same_category,
        same_ida=rel.same_ida,
        similar_allocation=rel.similar_allocation,
        close_recommendation_dates=rel.close_recommendation_dates,
        semantic_similarity=rel.semantic_similarity,
        similarity_score=rel.similarity_score,
        date_gap_days=rel.date_gap_days,
        overlap_outcome=rel.overlap_outcome,
        gps_distance_m=rel.gps_distance_m,
    )


def build_ego_graph(
    subject: GraphRecord,
    *,
    similar: Sequence[tuple[GraphRecord, SimilarRelation]],
    cluster_peers: Sequence[GraphRecord],
) -> tuple[nx.MultiDiGraph, GraphNode, list[GraphNode], list[GraphRelationship]]:
    graph: nx.MultiDiGraph = nx.MultiDiGraph()
    project_node = make_project_node(subject)
    _add_node(graph, project_node)
    relationships: list[GraphRelationship] = []
    nodes: dict[str, GraphNode] = {project_node.node_id: project_node}

    def include_record(record: GraphRecord) -> None:
        node = make_project_node(record)
        _add_node(graph, node)
        nodes[node.node_id] = node
        for entity in entity_nodes_for(record):
            _add_node(graph, entity)
            nodes[entity.node_id] = entity
        for rel in entity_relationships_for(record):
            if rel.from_node_id in graph and rel.to_node_id in graph:
                _add_edge(graph, rel)
                relationships.append(rel)

    include_record(subject)
    seen_peers: set[int] = {subject.project_id}
    for peer, relation in similar:
        if peer.project_id in seen_peers:
            continue
        seen_peers.add(peer.project_id)
        include_record(peer)
        rel = similar_relationship(
            subject,
            peer,
            similarity_score=relation.similarity_score,
            semantic_similarity=relation.semantic_similarity,
            same_constituency=relation.same_constituency,
            same_category=relation.same_category,
            same_ida=relation.same_ida,
            similar_allocation=relation.similar_allocation,
            close_recommendation_dates=relation.close_recommendation_dates,
            date_gap_days=relation.date_gap_days,
            overlap_outcome=relation.overlap_outcome,
            gps_distance_m=relation.gps_distance_m,
        )
        _add_edge(graph, rel)
        relationships.append(rel)
        reverse = GraphRelationship(
            from_node_id=rel.to_node_id,
            to_node_id=rel.from_node_id,
            edge_type=EdgeType.SIMILAR_TO,
            strength=rel.strength,
            from_project_id=rel.to_project_id,
            to_project_id=rel.from_project_id,
            same_constituency=rel.same_constituency,
            same_category=rel.same_category,
            same_ida=rel.same_ida,
            similar_allocation=rel.similar_allocation,
            close_recommendation_dates=rel.close_recommendation_dates,
            semantic_similarity=rel.semantic_similarity,
            similarity_score=rel.similarity_score,
            date_gap_days=rel.date_gap_days,
            overlap_outcome=rel.overlap_outcome,
            gps_distance_m=rel.gps_distance_m,
            attributes=rel.attributes,
        )
        _add_edge(graph, reverse)

    for peer in cluster_peers:
        if peer.project_id in seen_peers:
            continue
        seen_peers.add(peer.project_id)
        include_record(peer)

    connected = sorted(
        (node for node in nodes.values() if node.node_id != project_node.node_id),
        key=lambda item: (item.node_type.value, item.node_id),
    )
    relationships.sort(
        key=lambda item: (item.edge_type.value, item.from_node_id, item.to_node_id)
    )
    display_nodes = connected[: MAX_DISPLAY_NODES - 1]
    display_rels = [
        rel
        for rel in relationships
        if not (
            rel.edge_type == EdgeType.SIMILAR_TO
            and rel.from_project_id is not None
            and rel.to_project_id is not None
            and rel.from_project_id > rel.to_project_id
        )
    ]
    display_rels = display_rels[:MAX_DISPLAY_RELATIONSHIPS]
    return graph, project_node, display_nodes, display_rels


def connected_project_records(
    nodes: Sequence[GraphNode],
    records_by_id: dict[int, GraphRecord],
    subject_id: int,
) -> list[GraphRecord]:
    projects: list[GraphRecord] = []
    for node in nodes:
        if node.node_type != NodeType.PROJECT or node.project_id is None:
            continue
        if node.project_id == subject_id:
            continue
        record = records_by_id.get(node.project_id)
        if record is not None:
            projects.append(record)
    projects.sort(key=lambda item: item.project_id)
    return projects
