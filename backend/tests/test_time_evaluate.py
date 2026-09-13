from __future__ import annotations

from app.engines.time.constants import FORBIDDEN_MODEL_INPUT_COLUMNS
from app.engines.time.enrichment import HybridSchedule, HeldOutTimeLabel
from app.engines.time.evaluate import TimeEvaluationRow, format_evaluation_rows
from app.engines.time.types import TimePeerRecord


def test_forbidden_columns_are_not_time_features() -> None:
    fields = set(TimePeerRecord.__dataclass_fields__)
    assert fields.isdisjoint(FORBIDDEN_MODEL_INPUT_COLUMNS)
    schedule_fields = set(HybridSchedule.__dataclass_fields__)
    assert schedule_fields.isdisjoint(FORBIDDEN_MODEL_INPUT_COLUMNS)
    for name in (
        "scenario_type",
        "demo_case_id",
        "mixed_signals",
        "anomaly_notes",
        "overlap_group_id",
        "coordinate_source",
    ):
        assert name in FORBIDDEN_MODEL_INPUT_COLUMNS


def test_held_out_labels_are_separate_from_schedule() -> None:
    assert "scenario_type" in HeldOutTimeLabel.__dataclass_fields__
    assert "scenario_type" not in HybridSchedule.__dataclass_fields__
    assert "demo_case_id" not in HybridSchedule.__dataclass_fields__


def test_evaluation_formatter_marks_real_and_hybrid() -> None:
    real = TimeEvaluationRow(
        dataset="REAL",
        case_id="real_ap_completed",
        project_id=1,
        internal_project_id="internal:abc",
        status="Completed",
        time_mode="REAL",
        peer_scope="constituency_category",
        peer_count=12,
        planned_duration_days=None,
        actual_duration_days=None,
        elapsed_duration_days=None,
        slippage_days=None,
        physical_progress_percent=None,
        time_anomaly_score=None,
        evidence_confidence=14,
        flagged=False,
        outcome="INSUFFICIENT_EVIDENCE",
        explanation="INCONCLUSIVE / INSUFFICIENT EVIDENCE for schedule or delay.",
    )
    hybrid = TimeEvaluationRow(
        dataset="HYBRID",
        case_id="hybrid_demo_stuck",
        project_id=2,
        internal_project_id="internal:def",
        status="Ongoing",
        time_mode="HYBRID_TEST",
        peer_scope="constituency_category_work_type",
        peer_count=8,
        planned_duration_days=100,
        actual_duration_days=None,
        elapsed_duration_days=160,
        slippage_days=80,
        physical_progress_percent=12,
        time_anomaly_score=88,
        evidence_confidence=54,
        flagged=True,
        outcome="TIME_ANOMALY",
        explanation="HYBRID/TEST: elapsed duration vs planned time.",
        held_out_scenario_type="DEMO_STUCK",
        held_out_demo_case_id="STUCK",
    )
    text = format_evaluation_rows([real, hybrid])
    assert "[1] REAL / real_ap_completed" in text
    assert "[2] HYBRID / hybrid_demo_stuck" in text
    assert "time_mode=REAL" in text
    assert "time_mode=HYBRID_TEST" in text
    assert "time_anomaly_score=None" in text
    assert "time_anomaly_score=88" in text
    assert "held_out_label=scenario_type=DEMO_STUCK" in text
    assert "fraud" not in text.casefold()
