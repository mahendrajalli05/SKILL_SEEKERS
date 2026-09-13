"""Node identity helpers for Relationship Graph V1.

Entity keys use observed text only. Chamber/house constituency labels
are not geographic nodes.
"""

from __future__ import annotations

from app.engines.cost.work_type import normalize_observed_text
from app.engines.graph.types import GraphNode, GraphRecord, NodeType


def _key(value: str | None) -> str:
    return normalize_observed_text(value).casefold()


def project_node_id(project_id: int) -> str:
    return f"{NodeType.PROJECT.value}:{project_id}"


def entity_node_id(node_type: NodeType, label: str) -> str | None:
    key = _key(label)
    if not key:
        return None
    return f"{node_type.value}:{key}"


def make_project_node(record: GraphRecord) -> GraphNode:
    return GraphNode(
        node_id=project_node_id(record.project_id),
        node_type=NodeType.PROJECT,
        label=record.source_work or record.work_description or record.internal_project_id,
        project_id=record.project_id,
        internal_project_id=record.internal_project_id,
        attributes={
            "mp_name": record.mp_name,
            "category": record.category,
            "constituency": record.constituency,
            "constituency_usable": record.constituency_usable,
            "ida": record.ida,
            "state": record.state,
            "allocation_amount": record.allocation_amount,
            "recommended_date": (
                record.recommended_date.isoformat() if record.recommended_date else None
            ),
        },
    )


def make_entity_node(node_type: NodeType, label: str) -> GraphNode | None:
    text = normalize_observed_text(label)
    node_id = entity_node_id(node_type, text)
    if node_id is None:
        return None
    return GraphNode(
        node_id=node_id,
        node_type=node_type,
        label=text,
        attributes={"key": _key(text)},
    )


def constituency_node(record: GraphRecord) -> GraphNode | None:
    if not record.constituency_usable:
        return None
    return make_entity_node(NodeType.CONSTITUENCY, record.constituency)


def entity_nodes_for(record: GraphRecord) -> list[GraphNode]:
    nodes: list[GraphNode] = []
    for node_type, label, allowed in (
        (NodeType.MP, record.mp_name, True),
        (NodeType.CONSTITUENCY, record.constituency, record.constituency_usable),
        (NodeType.CATEGORY, record.category, True),
        (NodeType.IDA, record.ida, True),
        (NodeType.STATE, record.state, True),
    ):
        if not allowed:
            continue
        node = make_entity_node(node_type, label)
        if node is not None:
            nodes.append(node)
    return nodes
