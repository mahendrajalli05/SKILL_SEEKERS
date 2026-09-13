from __future__ import annotations

from app.engines.graph.constants import FABRICATED_GRAPH_FIELDS, FORBIDDEN_MODEL_INPUT_COLUMNS
from app.engines.graph.evaluate import GraphEvaluationRow, format_evaluation_rows
from app.engines.graph.types import GraphRecord


def test_forbidden_columns_are_not_graph_features() -> None:
    fields = set(GraphRecord.__dataclass_fields__)
    assert fields.isdisjoint(FORBIDDEN_MODEL_INPUT_COLUMNS)
    assert fields.isdisjoint(FABRICATED_GRAPH_FIELDS)
    for name in (
        "scenario_type",
        "demo_case_id",
        "mixed_signals",
        "anomaly_notes",
        "overlap_group_id",
        "coordinate_source",
        "latitude",
        "longitude",
        "vendor",
        "district",
    ):
        assert name not in fields


def test_evaluation_formatter_marks_real_and_hybrid() -> None:
    real = GraphEvaluationRow(
        dataset="REAL",
        case_id="real_ap_water_tanks",
        project_id=1,
        internal_project_id="internal:abc",
        graph_mode="REAL",
        data_mode="REAL",
        connected_project_count=4,
        same_constituency_count=3,
        same_category_count=4,
        same_ida_count=2,
        similar_project_count=2,
        strongest_relationship="SIMILAR_TO project 2 (POTENTIAL_OVERLAP)",
        graph_finding="NORMAL_CONNECTIVITY",
        evidence_confidence=54,
        graph_score=18,
        independent_signal_count=2,
        ida_associated_project_count=12,
        cluster_size=6,
        explanation="Graph finding: Normal Connectivity.",
    )
    hybrid = GraphEvaluationRow(
        dataset="HYBRID",
        case_id="hybrid_demo_clean",
        project_id=2,
        internal_project_id="internal:ghi",
        graph_mode="HYBRID_TEST",
        data_mode="HYBRID",
        connected_project_count=1,
        same_constituency_count=1,
        same_category_count=1,
        same_ida_count=0,
        similar_project_count=0,
        strongest_relationship="ASSOCIATED_WITH_IDA IDA:eluru_ida",
        graph_finding="NORMAL_CONNECTIVITY",
        evidence_confidence=58,
        graph_score=12,
        independent_signal_count=0,
        ida_associated_project_count=9,
        cluster_size=2,
        explanation="Graph finding: Normal Connectivity.",
        held_out_scenario_type="DEMO_CLEAN",
        held_out_demo_case_id="CLEAN",
    )
    text = format_evaluation_rows([real, hybrid])
    assert "REAL / real_ap_water_tanks" in text
    assert "HYBRID / hybrid_demo_clean" in text
    assert "data_mode=REAL" in text
    assert "data_mode=HYBRID" in text
    assert "held_out_label=" in text
    assert "fraud" not in text.casefold()
