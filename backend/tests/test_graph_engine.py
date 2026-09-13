from __future__ import annotations

from datetime import date

from app.engines.graph.constants import FABRICATED_GRAPH_FIELDS, FORBIDDEN_MODEL_INPUT_COLUMNS
from app.engines.graph.nodes import constituency_node, entity_nodes_for, make_project_node
from app.engines.graph.service import assess_graph
from app.engines.graph.types import EdgeType, GraphFindingKind, GraphMode, GraphRecord, NodeType
from app.engines.overlap.embeddings import HashedTokenEmbedder
from app.engines.overlap.enrichment import HybridGps
from app.engines.overlap.text import constituency_fields

TANKS = "NA - Construction of water tanks"
ROADS = "NA - Construction of roads, approach roads, link roads and pathways"
HALLS = "NA - Construction of community centers and community halls"
AMBULANCE = "NA - Purchase of ambulance"
SYNTHETIC_LABEL = "SYNTHETIC: relationship-graph unit test (not a government project)"


def _record(
    project_id: int,
    *,
    work: str = TANKS,
    category: str = "Normal/Others",
    constituency: str = "KURNOOL",
    state: str = "Andhra Pradesh",
    mp_name: str = "Test MP",
    ida: str = "Kurnool_IDA",
    amount: int | None = 500_000,
    rec_date: date | None = date(2023, 6, 1),
    village: str = "",
) -> GraphRecord:
    value, usable, kind, _reason = constituency_fields(constituency)
    return GraphRecord(
        project_id=project_id,
        internal_project_id=f"internal:synthetic:graph:{project_id}",
        mp_name=mp_name,
        work_description=work,
        source_work=work,
        category=category,
        state=state,
        constituency=value,
        constituency_usable=usable,
        constituency_kind=kind,
        ida=ida,
        allocation_amount=amount,
        recommended_date=rec_date,
        village=village,
        is_synthetic=True,
    )


def _assess(subject: GraphRecord, corpus: list[GraphRecord], **kwargs):
    return assess_graph(subject, corpus, embedder=HashedTokenEmbedder(), **kwargs)


def _edge_types(result) -> set[str]:
    return {rel.edge_type.value for rel in result.relationships}


def _node_types(result) -> set[str]:
    types = {result.project_node.node_type.value}
    types.update(node.node_type.value for node in result.connected_nodes)
    return types


def test_basic_project_node_creation() -> None:
    subject = _record(1)
    node = make_project_node(subject)
    assert node.node_type == NodeType.PROJECT
    assert node.project_id == 1
    assert node.internal_project_id == subject.internal_project_id
    assert "latitude" not in node.attributes
    assert "vendor" not in node.attributes
    result = _assess(subject, [subject])
    assert result.project_node.node_type == NodeType.PROJECT
    assert result.project_id == 1


def test_mp_relationships() -> None:
    subject = _record(1, mp_name="Shri Example")
    result = _assess(subject, [subject])
    assert EdgeType.RECOMMENDED_BY.value in _edge_types(result)
    assert NodeType.MP.value in _node_types(result)
    mp_nodes = [n for n in result.connected_nodes if n.node_type == NodeType.MP]
    assert mp_nodes
    assert mp_nodes[0].label == "Shri Example"


def test_constituency_relationships() -> None:
    subject = _record(1, constituency="KURNOOL")
    result = _assess(subject, [subject])
    assert EdgeType.LOCATED_IN_CONSTITUENCY.value in _edge_types(result)
    assert NodeType.CONSTITUENCY.value in _node_types(result)


def test_category_relationships() -> None:
    subject = _record(1)
    result = _assess(subject, [subject])
    assert EdgeType.HAS_CATEGORY.value in _edge_types(result)
    assert NodeType.CATEGORY.value in _node_types(result)


def test_ida_relationships() -> None:
    subject = _record(1, ida="Eluru_IDA")
    result = _assess(subject, [subject])
    assert EdgeType.ASSOCIATED_WITH_IDA.value in _edge_types(result)
    assert NodeType.IDA.value in _node_types(result)
    assert result.stats.ida_associated_project_count == 1


def test_state_relationships() -> None:
    subject = _record(1, state="Andhra Pradesh")
    result = _assess(subject, [subject])
    assert EdgeType.IN_STATE.value in _edge_types(result)
    assert NodeType.STATE.value in _node_types(result)


def test_project_to_project_similarity_relationships() -> None:
    subject = _record(1, village="Pedakakani")
    other = _record(2, amount=500_000, rec_date=date(2023, 6, 8), village="Pedakakani")
    result = _assess(subject, [subject, other])
    assert result.stats.similar_project_count >= 1
    assert EdgeType.SIMILAR_TO.value in _edge_types(result)
    similar = [rel for rel in result.relationships if rel.edge_type == EdgeType.SIMILAR_TO]
    assert similar
    assert similar[0].semantic_similarity is not None
    assert similar[0].same_constituency is True
    assert similar[0].same_category is True
    assert similar[0].same_ida is True
    assert similar[0].overlap_outcome in {"POTENTIAL_DUPLICATE", "POTENTIAL_OVERLAP"}
    assert similar[0].gps_distance_m is None


def test_graph_determinism() -> None:
    subject = _record(1)
    corpus = [subject, _record(2), _record(3, work=ROADS), _record(4, work=HALLS)]
    first = _assess(subject, corpus)
    second = _assess(subject, corpus)
    assert first.finding_kind == second.finding_kind
    assert first.graph_score == second.graph_score
    assert first.explanation == second.explanation
    assert [n.node_id for n in first.connected_nodes] == [n.node_id for n in second.connected_nodes]
    assert [(r.from_node_id, r.to_node_id, r.edge_type.value) for r in first.relationships] == [
        (r.from_node_id, r.to_node_id, r.edge_type.value) for r in second.relationships
    ]


def test_no_fabricated_fields() -> None:
    fields = set(GraphRecord.__dataclass_fields__)
    assert fields.isdisjoint(FABRICATED_GRAPH_FIELDS)
    assert fields.isdisjoint(FORBIDDEN_MODEL_INPUT_COLUMNS)
    assert "latitude" not in fields
    assert "vendor" not in fields
    assert "district" not in fields
    subject = _record(1)
    result = _assess(subject, [subject, _record(2)])
    blob = (result.explanation + str(result.project_node.attributes)).casefold()
    assert "latitude" not in result.project_node.attributes
    assert "longitude" not in result.project_node.attributes
    for token in ("vendor_name", "sanction_date", "official_work_id"):
        assert token not in blob


def test_no_invalid_geography_relationships() -> None:
    subject = _record(1, constituency="Sitting Rajya Sabha")
    other = _record(2, constituency="Sitting Rajya Sabha", work=ROADS)
    result = _assess(subject, [subject, other])
    assert EdgeType.LOCATED_IN_CONSTITUENCY.value not in _edge_types(result)
    assert constituency_node(subject) is None
    assert NodeType.CONSTITUENCY.value not in _node_types(result)
    assert result.constituency_usable is False
    entities = entity_nodes_for(subject)
    assert all(node.node_type != NodeType.CONSTITUENCY for node in entities)


def test_missing_field_handling() -> None:
    subject = _record(
        1,
        mp_name="",
        ida="",
        category="",
        state="",
        constituency="",
        work="",
        amount=None,
        rec_date=None,
    )
    result = _assess(subject, [subject])
    assert EdgeType.RECOMMENDED_BY.value not in _edge_types(result)
    assert EdgeType.LOCATED_IN_CONSTITUENCY.value not in _edge_types(result)
    assert EdgeType.HAS_CATEGORY.value not in _edge_types(result)
    assert EdgeType.ASSOCIATED_WITH_IDA.value not in _edge_types(result)
    assert EdgeType.IN_STATE.value not in _edge_types(result)
    assert result.finding_kind == GraphFindingKind.INSUFFICIENT_EVIDENCE
    assert result.stats.similar_project_count == 0
    assert "insufficient evidence" in result.explanation.casefold()


def test_isolated_project() -> None:
    subject = _record(
        1,
        work="NA - Unique solar drying yard at Isolatedpur",
        constituency="ISOLATEDPUR",
        ida="Isolatedpur_IDA",
        mp_name="Isolated MP",
    )
    other = _record(
        2,
        work=ROADS,
        constituency="KURNOOL",
        ida="Kurnool_IDA",
        mp_name="Other MP",
    )
    result = _assess(subject, [subject, other])
    assert result.stats.similar_project_count == 0
    assert result.stats.connected_project_count == 0
    assert result.finding_kind == GraphFindingKind.NORMAL_CONNECTIVITY
    assert result.flagged is False
    assert "fraud" not in result.explanation.casefold()


def test_highly_connected_project() -> None:
    subject = _record(1, ida="IDA-0", rec_date=date(2023, 1, 1))
    corpus = [subject]
    for index in range(2, 8):
        corpus.append(
            _record(
                index,
                ida=f"IDA-{index}",
                rec_date=date(2023, 4, 1),
                village="",
            )
        )
    result = _assess(subject, corpus)
    assert result.stats.similar_project_count >= 5
    assert result.finding_kind == GraphFindingKind.HIGH_CONNECTIVITY
    assert result.flagged is False
    assert "not automatically" in result.explanation.casefold()
    assert "pattern of interest" in result.explanation.casefold()
    assert "fraud" not in result.explanation.casefold()


def test_multiple_independent_relationship_signals() -> None:
    subject = _record(1, village="Pedakakani")
    corpus = [subject]
    for index in range(2, 8):
        corpus.append(
            _record(
                index,
                amount=500_000 + index,
                rec_date=date(2023, 6, index),
                village="Pedakakani",
            )
        )
    result = _assess(subject, corpus)
    assert result.finding_kind == GraphFindingKind.POTENTIAL_PATTERN_OF_INTEREST
    assert result.flagged is True
    assert result.stats.independent_signal_count >= 3
    assert "same_constituency" in result.stats.independent_signals
    assert "same_ida" in result.stats.independent_signals
    assert "Potential Pattern of Interest" in result.finding.summary
    assert "fraud" not in result.explanation.casefold()
    assert result.why_flagged is not None


def test_false_positive_connectivity() -> None:
    subject = _record(1, work=TANKS)
    other = _record(2, work=ROADS, amount=500_000)
    third = _record(3, work=AMBULANCE, amount=500_000)
    result = _assess(subject, [subject, other, third])
    assert result.stats.similar_project_count == 0
    assert result.finding_kind == GraphFindingKind.NORMAL_CONNECTIVITY
    assert result.flagged is False
    assert result.stats.connected_project_count >= 1
    assert EdgeType.SIMILAR_TO.value not in _edge_types(result)


def test_synthetic_label_leakage() -> None:
    fields = set(GraphRecord.__dataclass_fields__)
    for name in (
        "scenario_type",
        "demo_case_id",
        "mixed_signals",
        "anomaly_notes",
        "overlap_group_id",
        "coordinate_source",
    ):
        assert name not in fields
        assert name in FORBIDDEN_MODEL_INPUT_COLUMNS
    subject = _record(1)
    result = _assess(subject, [subject, _record(2)])
    blob = (result.explanation + str(result.connected_nodes)).casefold()
    for token in (
        "scenario_type",
        "demo_case_id",
        "anomaly_notes",
        "overlap_group",
        "coordinate_source",
        "mixed_signals",
    ):
        assert token not in blob
    assert "fraud" not in blob


def test_real_vs_hybrid_separation() -> None:
    subject = _record(1)
    other = _record(2, rec_date=date(2023, 6, 8))
    gps = {
        subject.internal_project_id: HybridGps(
            internal_project_id=subject.internal_project_id,
            latitude=15.83,
            longitude=80.0,
        ),
        other.internal_project_id: HybridGps(
            internal_project_id=other.internal_project_id,
            latitude=15.8305,
            longitude=80.0005,
        ),
    }
    real = assess_graph(
        subject,
        [subject, other],
        mode=GraphMode.REAL,
        embedder=HashedTokenEmbedder(),
        gps_by_id=gps,
    )
    hybrid = assess_graph(
        subject,
        [subject, other],
        mode=GraphMode.HYBRID_TEST,
        embedder=HashedTokenEmbedder(),
        gps_by_id=gps,
    )
    assert real.dataset_type == "REAL"
    assert hybrid.dataset_type == "HYBRID"
    assert real.gps_used is False
    assert hybrid.gps_used is True
    assert all(rel.gps_distance_m is None for rel in real.relationships)
    assert "latitude" not in real.project_node.attributes
    assert "longitude" not in real.project_node.attributes
    assert "GPS is not a REAL graph node" in hybrid.explanation or "HYBRID" in hybrid.explanation
    assert NodeType.PROJECT.value in _node_types(real)
    node_types = {NodeType.PROJECT, NodeType.MP, NodeType.CONSTITUENCY, NodeType.CATEGORY, NodeType.IDA, NodeType.STATE}
    assert _node_types(real).issubset({item.value for item in node_types})


def test_entity_nodes_skip_blank_mp() -> None:
    subject = _record(1, mp_name="")
    nodes = entity_nodes_for(subject)
    assert all(node.node_type != NodeType.MP for node in nodes)
    result = _assess(subject, [subject])
    assert EdgeType.RECOMMENDED_BY.value not in _edge_types(result)
