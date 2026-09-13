from __future__ import annotations

from app.engines.overlap.constants import FORBIDDEN_MODEL_INPUT_COLUMNS
from app.engines.overlap.enrichment import HeldOutOverlapLabel, HybridGps, assert_no_label_fields
from app.engines.overlap.evaluate import OverlapEvaluationRow, format_evaluation_rows
from app.engines.overlap.types import OverlapRecord


def test_forbidden_columns_are_not_overlap_features() -> None:
    fields = set(OverlapRecord.__dataclass_fields__)
    assert fields.isdisjoint(FORBIDDEN_MODEL_INPUT_COLUMNS)
    gps_fields = set(HybridGps.__dataclass_fields__)
    assert gps_fields.isdisjoint(FORBIDDEN_MODEL_INPUT_COLUMNS)
    assert_no_label_fields(HybridGps(internal_project_id="internal:x", latitude=1.0, longitude=2.0))
    for name in (
        "scenario_type",
        "demo_case_id",
        "mixed_signals",
        "anomaly_notes",
        "overlap_group_id",
        "coordinate_source",
    ):
        assert name in FORBIDDEN_MODEL_INPUT_COLUMNS


def test_held_out_labels_are_separate_from_gps() -> None:
    assert "scenario_type" in HeldOutOverlapLabel.__dataclass_fields__
    assert "overlap_group_id" in HeldOutOverlapLabel.__dataclass_fields__
    assert "scenario_type" not in HybridGps.__dataclass_fields__
    assert "overlap_group_id" not in HybridGps.__dataclass_fields__
    assert "coordinate_source" not in HybridGps.__dataclass_fields__


def test_evaluation_formatter_marks_real_and_hybrid() -> None:
    real = OverlapEvaluationRow(
        dataset="REAL",
        case_id="real_ap_water_tanks",
        project_id=1,
        internal_project_id="internal:abc",
        overlap_mode="REAL",
        constituency="KURNOOL",
        category="Normal/Others",
        candidate_count=12,
        match_count=1,
        top_linked_internal_project_id="internal:def",
        top_semantic_similarity=0.91,
        top_category_match=True,
        top_constituency_match=True,
        top_amount_similarity=0.88,
        top_date_gap_days=12,
        top_location_similarity=None,
        top_gps_distance_m=None,
        overlap_score=74,
        evidence_confidence=54,
        flagged=True,
        outcome="POTENTIAL_OVERLAP",
        geographic_evidence_available=False,
        embedding_backend="hashed-token-charngram-v1",
        explanation="Potential Overlap: semantic similarity with same constituency.",
    )
    hybrid = OverlapEvaluationRow(
        dataset="HYBRID",
        case_id="hybrid_clear_overlap_a",
        project_id=2,
        internal_project_id="internal:ghi",
        overlap_mode="HYBRID_TEST",
        constituency="ELURU",
        category="Normal/Others",
        candidate_count=8,
        match_count=2,
        top_linked_internal_project_id="internal:jkl",
        top_semantic_similarity=0.40,
        top_category_match=True,
        top_constituency_match=True,
        top_amount_similarity=None,
        top_date_gap_days=None,
        top_location_similarity=None,
        top_gps_distance_m=120.4,
        overlap_score=61,
        evidence_confidence=58,
        flagged=True,
        outcome="POTENTIAL_OVERLAP",
        geographic_evidence_available=True,
        embedding_backend="hashed-token-charngram-v1",
        explanation="HYBRID/TEST Potential Overlap from GPS proximity.",
        held_out_scenario_type="OVERLAP",
        held_out_demo_case_id="",
        held_out_overlap_group_id="synthetic:overlap:26102:0001",
    )
    text = format_evaluation_rows([real, hybrid])
    assert "[1] REAL / real_ap_water_tanks" in text
    assert "[2] HYBRID / hybrid_clear_overlap_a" in text
    assert "overlap_mode=REAL" in text
    assert "overlap_mode=HYBRID_TEST" in text
    assert "geographic_evidence_available=False" in text
    assert "held_out_label=scenario_type=OVERLAP" in text
    assert "fraud" not in text.casefold()
