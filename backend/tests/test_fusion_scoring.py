from __future__ import annotations

from app.domain.enums import DataMode, EvidenceDisposition
from app.engines.fusion.constants import FORBIDDEN_MODEL_INPUT_COLUMNS
from app.engines.fusion.evaluate import FusionEvaluationRow, format_evaluation_rows
from app.engines.fusion.scoring import (
    bounded_score,
    evidence_confidence,
    evidence_coverage,
    investigation_priority,
    investigation_priority_0_100,
    raw_risk,
    unavailable_signal_weight,
)
from app.engines.fusion.signals import compliance_signal_score
from app.engines.fusion.types import SignalContribution
from app.domain.enums import RiskSignalState
from fusion_fixtures import make_signal_evidence


def test_forbidden_columns_are_not_fusion_features() -> None:
    for name in (
        "scenario_type",
        "demo_case_id",
        "mixed_signals",
        "anomaly_notes",
        "overlap_group_id",
        "coordinate_source",
    ):
        assert name in FORBIDDEN_MODEL_INPUT_COLUMNS


def test_bounded_score_clips() -> None:
    assert bounded_score(-10) == 0
    assert bounded_score(0) == 0
    assert bounded_score(100) == 100
    assert bounded_score(250) == 100
    assert bounded_score(39.4) == 39
    assert bounded_score(39.5) == 40


def test_compliance_mapping_does_not_reimplement_rules() -> None:
    flagged = make_signal_evidence(
        "compliance",
        score=None,
        disposition=EvidenceDisposition.WHY_FLAGGED,
        severity="attention",
        rule_ids=["R004", "R001"],
    )
    assert compliance_signal_score(flagged) == 90
    watch = make_signal_evidence(
        "compliance",
        score=None,
        disposition=EvidenceDisposition.WHY_FLAGGED,
        severity="watch",
        rule_ids=["R003"],
    )
    assert compliance_signal_score(watch) == 60


def test_evaluation_formatter_marks_real_and_hybrid() -> None:
    real = FusionEvaluationRow(
        dataset="REAL",
        case_id="real_example",
        project_id=1,
        internal_project_id="internal:abc",
        data_mode="REAL",
        investigation_priority=21,
        investigation_priority_0_100=21.0,
        raw_risk=14.7,
        evidence_confidence=40,
        priority_band="LOW",
        explanation_type="WHY_NOT_FLAGGED",
        recommended_action="MONITOR",
        contributing_signals=["Cost:21", "Overlap:40"],
        unavailable_integrated=["Schedule"],
        evidence_ids=["ev:cost:1:allocation_cost_anomaly:REAL:abc"],
        available_weight=0.40,
        available_signal_weight=0.40,
        unavailable_signal_weight=0.30,
        unused_weight=0.60,
        evidence_coverage=0.5714,
        explanation="Two assessable signals. Time is not assessable in the real extract.",
        recommendation="Monitor the work using the available records.",
    )
    hybrid = FusionEvaluationRow(
        dataset="HYBRID",
        case_id="hybrid_demo_stuck",
        project_id=2,
        internal_project_id="internal:def",
        data_mode="HYBRID",
        investigation_priority=48,
        investigation_priority_0_100=48.0,
        raw_risk=33.6,
        evidence_confidence=55,
        priority_band="HIGH",
        explanation_type="WHY_FLAGGED",
        recommended_action="INSPECT",
        contributing_signals=["Schedule:93", "Cost:50"],
        unavailable_integrated=[],
        evidence_ids=["ev:time:2:time_anomaly:HYBRID:abc"],
        available_weight=0.70,
        available_signal_weight=0.70,
        unavailable_signal_weight=0.0,
        unused_weight=0.30,
        evidence_coverage=1.0,
        explanation="HYBRID/TEST schedule evidence contributed. Not a real delay statistic.",
        recommendation="Inspect supporting documents.",
        held_out_scenario_type="DEMO_STUCK",
        held_out_demo_case_id="STUCK",
        held_out_mixed_signals="",
    )
    text = format_evaluation_rows([real, hybrid])
    assert "[1] REAL / real_example" in text
    assert "[2] HYBRID / hybrid_demo_stuck" in text
    assert "investigation_priority=21" in text
    assert "evidence_confidence=40" in text
    assert "held_out_label=scenario_type=DEMO_STUCK" in text
    assert "fraud" not in text.casefold()


def test_evidence_confidence_uses_mode_cap() -> None:
    signals = [
        SignalContribution(
            signal_id=slot,
            display_name=slot,
            weight=weight,
            state=RiskSignalState.ASSESSABLE,
            risk_score=50,
            contribution=weight * 50,
            evidence_confidence=0.95,
            evidence_id=f"ev:{slot}",
            disposition="WHY_NOT_FLAGGED",
            finding="ok",
            support="peer comparison",
            unavailable_reason=None,
        )
        for slot, weight in (
            ("cost", 0.25),
            ("schedule", 0.15),
            ("overlap", 0.15),
            ("compliance", 0.15),
        )
    ]
    real = evidence_confidence(signals, data_mode=DataMode.REAL)
    hybrid = evidence_confidence(signals, data_mode=DataMode.HYBRID)
    synthetic = evidence_confidence(signals, data_mode=DataMode.SYNTHETIC)
    assert real <= 90
    assert hybrid <= 72
    assert synthetic <= 55
    assert hybrid < real
    assert synthetic <= hybrid
    dummy_ip = investigation_priority(signals)
    assert real != dummy_ip or dummy_ip == 0
    assert investigation_priority_0_100(signals) == 50.0
    assert raw_risk(signals) == 35.0
    assert evidence_coverage(signals) == 1.0
    assert unavailable_signal_weight(signals) == 0.0
