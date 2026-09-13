from __future__ import annotations

from datetime import date

from app.engines.compliance.constants import FORBIDDEN_MODEL_INPUT_COLUMNS
from app.engines.compliance.enrichment import (
    HeldOutComplianceLabel,
    HybridComplianceFields,
    assert_no_label_fields,
)
from app.engines.compliance.evaluate import ComplianceEvaluationRow, format_evaluation_rows
from app.engines.compliance.explain import explanation_for_rule
from app.engines.compliance.loader import load_rules
from app.engines.compliance.types import ComplianceMode, RuleResultStatus


def test_forbidden_columns_are_not_compliance_features() -> None:
    from app.engines.compliance.types import ComplianceContext

    fields = set(ComplianceContext.__dataclass_fields__)
    assert fields.isdisjoint(FORBIDDEN_MODEL_INPUT_COLUMNS)
    hybrid_fields = set(HybridComplianceFields.__dataclass_fields__)
    assert hybrid_fields.isdisjoint(FORBIDDEN_MODEL_INPUT_COLUMNS)
    assert_no_label_fields(
        HybridComplianceFields(
            internal_project_id="internal:x",
            sanction_date=date(2023, 6, 1),
            planned_start_date=None,
            planned_completion_date=None,
            actual_start_date=None,
            actual_completion_date=None,
            sanctioned_amount=1,
            expenditure_amount=0,
            physical_progress_percent=0,
            as_of_date=date(2024, 6, 30),
        )
    )
    for name in (
        "scenario_type",
        "demo_case_id",
        "mixed_signals",
        "anomaly_notes",
        "overlap_group_id",
        "coordinate_source",
    ):
        assert name in FORBIDDEN_MODEL_INPUT_COLUMNS


def test_held_out_labels_are_separate_from_hybrid_fields() -> None:
    assert "scenario_type" in HeldOutComplianceLabel.__dataclass_fields__
    assert "scenario_type" not in HybridComplianceFields.__dataclass_fields__
    assert "demo_case_id" not in HybridComplianceFields.__dataclass_fields__
    assert "coordinate_source" not in HybridComplianceFields.__dataclass_fields__


def test_explanation_wording_matches_required_status_form() -> None:
    rule = next(item for item in load_rules().rules if item.rule_id == "R002")
    triggered = explanation_for_rule(
        rule,
        RuleResultStatus.TRIGGERED,
        missing_fields=[],
        evidence={"days": 400},
        dataset_label="HYBRID/TEST",
    )
    missing = explanation_for_rule(
        rule,
        RuleResultStatus.NOT_ASSESSABLE,
        missing_fields=["actual_completion_date"],
        evidence={},
        dataset_label="real",
    )
    assert triggered.startswith("R002. Status: TRIGGERED.")
    assert "not satisfied based on the available project information" in triggered
    assert "Completion-date evidence is unavailable in the current real dataset." in missing
    assert "fraud" not in triggered.casefold()
    assert "fraud" not in missing.casefold()


def test_evaluation_formatter_marks_real_and_hybrid() -> None:
    real = ComplianceEvaluationRow(
        dataset="REAL",
        case_id="real_ap_unsanctioned",
        project_id=1,
        internal_project_id="internal:abc",
        compliance_mode="REAL",
        constituency="KURNOOL",
        category="Normal/Others",
        status="Unsanctioned",
        compliance_status="INCONCLUSIVE",
        flagged=False,
        severity="info",
        triggered_rule_ids=[],
        non_triggered_rule_ids=["R015"],
        not_assessable_rule_ids=["R001", "R002"],
        explanation="REAL extract cannot assess sanction-date rules.",
        sample_rule_id="R001",
        sample_rule_status="NOT_ASSESSABLE",
        sample_rule_explanation="Sanction-date evidence is unavailable in the current real dataset.",
    )
    hybrid = ComplianceEvaluationRow(
        dataset="HYBRID",
        case_id="hybrid_demo_overbill",
        project_id=2,
        internal_project_id="internal:def",
        compliance_mode="HYBRID_TEST",
        constituency="ELURU",
        category="Normal/Others",
        status="Completed",
        compliance_status="RULES_TRIGGERED",
        flagged=True,
        severity="attention",
        triggered_rule_ids=["R004"],
        non_triggered_rule_ids=["R015"],
        not_assessable_rule_ids=["R005"],
        explanation="HYBRID/TEST spend versus sanctioned amount.",
        sample_rule_id="R004",
        sample_rule_status="TRIGGERED",
        sample_rule_explanation="R004. Status: TRIGGERED. Required condition is not satisfied.",
        held_out_scenario_type="DEMO_OVERBILL",
        held_out_demo_case_id="OVERBILL",
    )
    text = format_evaluation_rows([real, hybrid])
    assert "[1] REAL / real_ap_unsanctioned" in text
    assert "[2] HYBRID / hybrid_demo_overbill" in text
    assert "compliance_mode=REAL" in text
    assert "compliance_mode=HYBRID_TEST" in text
    assert "held_out_label=scenario_type=DEMO_OVERBILL" in text
    assert "fraud" not in text.casefold()
    assert ComplianceMode.REAL.value == "REAL"
