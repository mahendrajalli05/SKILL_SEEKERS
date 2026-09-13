"""Dataclasses for Relationship Graph V1."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum

from app.domain.enums import EvidenceSeverity, EvidenceStatus


class GraphMode(str, Enum):
    REAL = "REAL"
    HYBRID_TEST = "HYBRID_TEST"


class NodeType(str, Enum):
    PROJECT = "PROJECT"
    MP = "MP"
    CONSTITUENCY = "CONSTITUENCY"
    CATEGORY = "CATEGORY"
    IDA = "IDA"
    STATE = "STATE"


class EdgeType(str, Enum):
    RECOMMENDED_BY = "RECOMMENDED_BY"
    LOCATED_IN_CONSTITUENCY = "LOCATED_IN_CONSTITUENCY"
    HAS_CATEGORY = "HAS_CATEGORY"
    ASSOCIATED_WITH_IDA = "ASSOCIATED_WITH_IDA"
    IN_STATE = "IN_STATE"
    SIMILAR_TO = "SIMILAR_TO"


class GraphFindingKind(str, Enum):
    NORMAL_CONNECTIVITY = "NORMAL_CONNECTIVITY"
    HIGH_CONNECTIVITY = "HIGH_CONNECTIVITY"
    POTENTIAL_PATTERN_OF_INTEREST = "POTENTIAL_PATTERN_OF_INTEREST"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True)
class GraphRecord:
    """One work for graph construction.

    Observed MPLADS fields only. Scenario labels and GPS are never stored
    here. GPS may be passed separately to Overlap scoring in HYBRID_TEST.
    """

    project_id: int
    internal_project_id: str
    mp_name: str
    work_description: str
    source_work: str
    category: str
    state: str
    constituency: str
    constituency_usable: bool
    constituency_kind: str
    ida: str
    allocation_amount: int | None
    recommended_date: date | None
    city: str = ""
    ward: str = ""
    block: str = ""
    village: str = ""
    is_synthetic: bool = False


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    node_type: NodeType
    label: str
    project_id: int | None = None
    internal_project_id: str | None = None
    attributes: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class GraphRelationship:
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
    attributes: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class SimilarRelation:
    linked_project_id: int
    linked_internal_project_id: str
    similarity_score: float
    semantic_similarity: float | None
    same_constituency: bool | None
    same_category: bool | None
    same_ida: bool
    similar_allocation: bool | None
    close_recommendation_dates: bool
    date_gap_days: int | None
    overlap_outcome: str
    gps_distance_m: float | None = None


@dataclass(frozen=True)
class GraphFinding:
    kind: GraphFindingKind
    summary: str
    details: str
    score: int | None
    confidence: int
    independent_signal_count: int
    independent_signals: tuple[str, ...]


@dataclass(frozen=True)
class GraphStats:
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
    cluster_density: float | None
    independent_signal_count: int
    independent_signals: tuple[str, ...]
    strongest_relationship: str | None
    strongest_strength: float | None
    entity_edge_count: int
    similar_edge_count: int


@dataclass
class GraphIntelligenceResult:
    project_id: int
    internal_project_id: str
    engine: str
    engine_version: str
    evidence_type: str
    dataset_type: str
    graph_mode: GraphMode
    finding_kind: GraphFindingKind
    flagged: bool
    status: EvidenceStatus
    severity: EvidenceSeverity
    signal_kind: str
    graph_score: int | None
    evidence_confidence: int
    explanation: str
    why_flagged: str | None
    why_not_flagged: str | None
    finding: GraphFinding
    stats: GraphStats
    project_node: GraphNode
    connected_nodes: list[GraphNode] = field(default_factory=list)
    relationships: list[GraphRelationship] = field(default_factory=list)
    mp_name: str = ""
    category: str = ""
    constituency: str = ""
    constituency_kind: str = ""
    constituency_usable: bool = False
    ida: str = ""
    state: str = ""
    candidate_strategy: str = ""
    gps_used: bool = False
