from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import EvidenceSeverity, EvidenceStatus
from app.engines.graph.constants import ENGINE_NAME, ENGINE_VERSION, EVIDENCE_TYPE
from app.engines.graph.types import (
    EdgeType,
    GraphFindingKind,
    GraphIntelligenceResult,
    GraphMode,
    NodeType,
)


class GraphNodeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    node_id: str
    node_type: NodeType
    label: str
    project_id: int | None = None
    internal_project_id: str | None = None
    attributes: dict[str, object] = Field(default_factory=dict)


class GraphRelationshipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    from_node_id: str
    to_node_id: str
    edge_type: EdgeType
    strength: float
    from_project_id: int | None = None
    to_project_id: int | None = None
    same_constituency: bool | None = None
    same_category: bool | None = None
    same_ida: bool | None = None
    similar_allocation: bool | None = None
    close_recommendation_dates: bool | None = None
    semantic_similarity: float | None = None
    similarity_score: float | None = None
    date_gap_days: int | None = None
    overlap_outcome: str | None = None
    gps_distance_m: float | None = None


class GraphFindingRead(BaseModel):
    kind: GraphFindingKind
    summary: str
    details: str
    score: int | None = None
    confidence: int
    independent_signal_count: int
    independent_signals: list[str] = Field(default_factory=list)


class GraphStatsRead(BaseModel):
    connected_project_count: int
    similar_project_count: int
    same_constituency_count: int
    same_category_count: int
    same_ida_count: int
    same_constituency_similar: int
    same_category_similar: int
    same_ida_similar: int
    close_dates_similar: int
    similar_allocation_similar: int
    cluster_size: int
    ida_associated_project_count: int
    constituency_associated_project_count: int
    repeated_combo_count: int
    cluster_density: float | None = None
    independent_signal_count: int
    independent_signals: list[str] = Field(default_factory=list)
    strongest_relationship: str | None = None
    strongest_strength: float | None = None
    entity_edge_count: int
    similar_edge_count: int


class GraphIntelligenceResponse(BaseModel):
    """Relationship Graph neighborhood for one work. Investigation Priority is not assigned here."""

    project_id: int
    internal_project_id: str
    engine: str = ENGINE_NAME
    engine_version: str = ENGINE_VERSION
    evidence_type: str = EVIDENCE_TYPE
    dataset_type: str
    graph_mode: GraphMode
    finding_kind: GraphFindingKind
    flagged: bool
    status: EvidenceStatus
    severity: EvidenceSeverity
    signal_kind: str
    graph_score: int | None = None
    evidence_confidence: int
    explanation: str
    why_flagged: str | None = None
    why_not_flagged: str | None = None
    project_node: GraphNodeRead
    connected_nodes: list[GraphNodeRead] = Field(default_factory=list)
    relationships: list[GraphRelationshipRead] = Field(default_factory=list)
    relationship_strengths: list[dict[str, object]] = Field(default_factory=list)
    graph_findings: list[GraphFindingRead] = Field(default_factory=list)
    graph_evidence: GraphFindingRead
    stats: GraphStatsRead
    mp_name: str = ""
    category: str = ""
    constituency: str = ""
    constituency_kind: str = ""
    constituency_usable: bool = False
    ida: str = ""
    state: str = ""
    candidate_strategy: str = ""
    gps_used: bool = False

    @classmethod
    def from_result(cls, result: GraphIntelligenceResult) -> GraphIntelligenceResponse:
        finding = GraphFindingRead(
            kind=result.finding.kind,
            summary=result.finding.summary,
            details=result.finding.details,
            score=result.finding.score,
            confidence=result.finding.confidence,
            independent_signal_count=result.finding.independent_signal_count,
            independent_signals=list(result.finding.independent_signals),
        )
        relationships = [
            GraphRelationshipRead.model_validate(item, from_attributes=True)
            for item in result.relationships
            if not (
                item.edge_type.value == "SIMILAR_TO"
                and item.from_project_id is not None
                and item.to_project_id is not None
                and item.from_project_id > item.to_project_id
            )
        ]
        if result.graph_mode != GraphMode.HYBRID_TEST:
            relationships = [
                item.model_copy(update={"gps_distance_m": None}) for item in relationships
            ]
        strengths = [
            {
                "from_node_id": item.from_node_id,
                "to_node_id": item.to_node_id,
                "edge_type": item.edge_type.value,
                "strength": item.strength,
            }
            for item in relationships
        ]
        return cls(
            project_id=result.project_id,
            internal_project_id=result.internal_project_id,
            engine=result.engine,
            engine_version=result.engine_version,
            evidence_type=result.evidence_type,
            dataset_type=result.dataset_type,
            graph_mode=result.graph_mode,
            finding_kind=result.finding_kind,
            flagged=result.flagged,
            status=result.status,
            severity=result.severity,
            signal_kind=result.signal_kind,
            graph_score=result.graph_score,
            evidence_confidence=result.evidence_confidence,
            explanation=result.explanation,
            why_flagged=result.why_flagged,
            why_not_flagged=result.why_not_flagged,
            project_node=GraphNodeRead.model_validate(
                result.project_node, from_attributes=True
            ),
            connected_nodes=[
                GraphNodeRead.model_validate(item, from_attributes=True)
                for item in result.connected_nodes
            ],
            relationships=relationships,
            relationship_strengths=strengths,
            graph_findings=[finding],
            graph_evidence=finding,
            stats=GraphStatsRead(
                connected_project_count=result.stats.connected_project_count,
                similar_project_count=result.stats.similar_project_count,
                same_constituency_count=result.stats.same_constituency_count,
                same_category_count=result.stats.same_category_count,
                same_ida_count=result.stats.same_ida_count,
                same_constituency_similar=result.stats.same_constituency_similar,
                same_category_similar=result.stats.same_category_similar,
                same_ida_similar=result.stats.same_ida_similar,
                close_dates_similar=result.stats.close_dates_similar,
                similar_allocation_similar=result.stats.similar_allocation_similar,
                cluster_size=result.stats.cluster_size,
                ida_associated_project_count=result.stats.ida_associated_project_count,
                constituency_associated_project_count=(
                    result.stats.constituency_associated_project_count
                ),
                repeated_combo_count=result.stats.repeated_combo_count,
                cluster_density=result.stats.cluster_density,
                independent_signal_count=result.stats.independent_signal_count,
                independent_signals=list(result.stats.independent_signals),
                strongest_relationship=result.stats.strongest_relationship,
                strongest_strength=result.stats.strongest_strength,
                entity_edge_count=result.stats.entity_edge_count,
                similar_edge_count=result.stats.similar_edge_count,
            ),
            mp_name=result.mp_name,
            category=result.category,
            constituency=result.constituency,
            constituency_kind=result.constituency_kind,
            constituency_usable=result.constituency_usable,
            ida=result.ida,
            state=result.state,
            candidate_strategy=result.candidate_strategy,
            gps_used=result.gps_used,
        )
