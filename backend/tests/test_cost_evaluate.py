from __future__ import annotations

from app.engines.cost.constants import FORBIDDEN_MODEL_INPUT_COLUMNS
from app.engines.cost.evaluate import EvaluationRow, format_evaluation_rows
from app.engines.cost.types import PeerRecord


def test_forbidden_columns_are_not_peer_features() -> None:
    fields = set(PeerRecord.__dataclass_fields__)
    assert fields.isdisjoint(FORBIDDEN_MODEL_INPUT_COLUMNS)
    for name in (
        "scenario_type",
        "demo_case_id",
        "mixed_signals",
        "anomaly_notes",
        "overlap_group_id",
        "coordinate_source",
    ):
        assert name in FORBIDDEN_MODEL_INPUT_COLUMNS


def test_evaluation_formatter_marks_real_and_hybrid() -> None:
    real = EvaluationRow(
        dataset="REAL",
        case_id="real_example",
        project_id=1,
        internal_project_id="internal:abc",
        constituency="KURNOOL",
        category="Normal/Others",
        peer_scope="constituency_category_work_type",
        peer_count=12,
        peer_quality=88,
        similarity_rationale="median work-title token Jaccard 1.00.",
        expected_cost=300_000.0,
        expected_range_low=200_000.0,
        expected_range_high=400_000.0,
        actual_allocation=310_000,
        deviation_percentage=3.3,
        cost_anomaly_score=8,
        evidence_confidence=80,
        flagged=False,
        outcome="WITHIN_PEER_RANGE",
        explanation="Allocation is 3.3% above the median of 12 comparable works.",
    )
    hybrid = EvaluationRow(
        dataset="HYBRID",
        case_id="hybrid_demo_overbill",
        project_id=2,
        internal_project_id="internal:def",
        constituency="ELURU",
        category="Repair and Renovation",
        peer_scope="constituency_category",
        peer_count=8,
        peer_quality=40,
        similarity_rationale="median work-title token Jaccard 0.20.",
        expected_cost=1_000_000.0,
        expected_range_low=500_000.0,
        expected_range_high=2_000_000.0,
        actual_allocation=3_550_000,
        deviation_percentage=255.0,
        cost_anomaly_score=90,
        evidence_confidence=70,
        flagged=True,
        outcome="COST_ANOMALY",
        explanation="Allocation is 255.0% above the median of 8 comparable works.",
        held_out_scenario_type="DEMO_OVERBILL",
        held_out_demo_case_id="OVERBILL",
    )
    text = format_evaluation_rows([real, hybrid])
    assert "[1] REAL / real_example" in text
    assert "[2] HYBRID / hybrid_demo_overbill" in text
    assert "held_out_label=scenario_type=DEMO_OVERBILL" in text
    assert "evidence_confidence=80" in text
    assert "peer_quality=88" in text
    assert "fraud" not in text.casefold()
