from __future__ import annotations

from datetime import date

from app.engines.compliance.apply import evaluate_rule
from app.engines.compliance.loader import load_rules
from app.engines.compliance.service import assess_compliance
from app.engines.compliance.types import (
    ComplianceContext,
    ComplianceMode,
    ComplianceStatus,
    RuleResultStatus,
)

RULESET = load_rules()


def _ctx(**overrides: object) -> ComplianceContext:
    values: dict[str, object] = {
        "project_id": 1,
        "internal_project_id": "internal:test:compliance:1",
        "mode": ComplianceMode.HYBRID_TEST,
        "mp_name": "Test MP",
        "work_description": "NA - Construction of water tanks",
        "category": "Normal/Others",
        "state": "Andhra Pradesh",
        "constituency": "KURNOOL",
        "ida": "KURNOOL_IDA",
        "city": "",
        "ward": "",
        "block": "",
        "village": "",
        "recommended_date": date(2023, 6, 1),
        "allocation_amount": 500_000,
        "ida_approval": "Approved by IDA",
        "status": "Sanctioned",
        "house": "Lok Sabha",
        "lifecycle_stage": "FUTURE",
        "as_of_date": date(2024, 6, 30),
        "sanction_date": date(2023, 6, 20),
        "sanctioned_amount": 500_000,
        "expenditure_amount": 400_000,
    }
    values.update(overrides)
    return ComplianceContext(**values)


def _rule(rule_id: str):
    return next(rule for rule in RULESET.rules if rule.rule_id == rule_id)


def test_triggered_rule_45_day_sanction() -> None:
    rule = _rule("R001")
    result = evaluate_rule(
        rule,
        _ctx(recommended_date=date(2023, 6, 1), sanction_date=date(2023, 8, 1)),
    )
    assert result.status == RuleResultStatus.TRIGGERED
    assert result.severity == "attention"
    assert result.evidence["days"] == 61
    assert "TRIGGERED" in result.explanation
    assert "not satisfied" in result.explanation
    assert result.source_reference["para"] == "3.2.4"
    assert result.source_reference["url"] == rule.source_reference.url


def test_non_triggered_rule_45_day_sanction() -> None:
    result = evaluate_rule(
        _rule("R001"),
        _ctx(recommended_date=date(2023, 6, 1), sanction_date=date(2023, 6, 20)),
    )
    assert result.status == RuleResultStatus.NOT_TRIGGERED
    assert result.evidence["days"] == 19
    assert "NOT_TRIGGERED" in result.explanation
    assert "satisfied" in result.explanation


def test_missing_required_field_is_not_assessable() -> None:
    result = evaluate_rule(_rule("R001"), _ctx(sanction_date=None, mode=ComplianceMode.REAL))
    assert result.status == RuleResultStatus.NOT_ASSESSABLE
    assert "sanction_date" in result.missing_fields
    assert "unavailable" in result.explanation.lower()
    assert result.source_reference["para"] == "3.2.4"


def test_not_assessable_when_real_completion_missing() -> None:
    result = evaluate_rule(
        _rule("R002"),
        _ctx(
            mode=ComplianceMode.REAL,
            sanction_date=None,
            actual_completion_date=None,
            as_of_date=None,
        ),
    )
    assert result.status == RuleResultStatus.NOT_ASSESSABLE
    assert "Completion-date evidence is unavailable" in result.explanation


def test_spend_versus_sanction_triggered_and_not_triggered() -> None:
    triggered = evaluate_rule(
        _rule("R004"),
        _ctx(sanctioned_amount=100, expenditure_amount=180),
    )
    clean = evaluate_rule(
        _rule("R004"),
        _ctx(sanctioned_amount=100, expenditure_amount=90),
    )
    assert triggered.status == RuleResultStatus.TRIGGERED
    assert triggered.severity == "attention"
    assert clean.status == RuleResultStatus.NOT_TRIGGERED
    assert triggered.source_reference["source_id"] == "MOSPI-MPLADS-ABOUT"


def test_blank_ida_triggers_and_recorded_ida_does_not() -> None:
    blank = evaluate_rule(_rule("R015"), _ctx(ida=""))
    present = evaluate_rule(_rule("R015"), _ctx(ida="KURNOOL_IDA"))
    assert blank.status == RuleResultStatus.TRIGGERED
    assert present.status == RuleResultStatus.NOT_TRIGGERED
    assert blank.severity == "info"


def test_repair_category_is_not_triggered_other_titles_not_assessable() -> None:
    repair = evaluate_rule(_rule("R016"), _ctx(category="Repair and Renovation"))
    other = evaluate_rule(_rule("R016"), _ctx(category="Normal/Others"))
    assert repair.status == RuleResultStatus.NOT_TRIGGERED
    assert other.status == RuleResultStatus.NOT_ASSESSABLE
    assert "Repair and Renovation" in repair.explanation or "satisfied" in repair.explanation


def test_sc_earmark_uses_injected_share_only() -> None:
    triggered = evaluate_rule(_rule("R005"), _ctx(mp_sc_share_percent=10.0))
    ok = evaluate_rule(_rule("R005"), _ctx(mp_sc_share_percent=16.0))
    missing = evaluate_rule(_rule("R005"), _ctx())
    assert triggered.status == RuleResultStatus.TRIGGERED
    assert ok.status == RuleResultStatus.NOT_TRIGGERED
    assert missing.status == RuleResultStatus.NOT_ASSESSABLE
    assert missing.severity == "watch"


def test_one_year_completion_open_clock() -> None:
    overdue = evaluate_rule(
        _rule("R002"),
        _ctx(
            sanction_date=date(2023, 1, 1),
            actual_completion_date=None,
            as_of_date=date(2024, 6, 30),
        ),
    )
    on_time = evaluate_rule(
        _rule("R002"),
        _ctx(
            sanction_date=date(2023, 6, 1),
            actual_completion_date=date(2023, 12, 1),
            as_of_date=date(2024, 6, 30),
        ),
    )
    assert overdue.status == RuleResultStatus.TRIGGERED
    assert overdue.evidence["days"] == 546
    assert on_time.status == RuleResultStatus.NOT_TRIGGERED


def test_zero_spend_after_90_days_triggers_payment_rule() -> None:
    result = evaluate_rule(
        _rule("R003"),
        _ctx(
            sanction_date=date(2023, 1, 1),
            expenditure_amount=0,
            first_payment_date=None,
            as_of_date=date(2024, 6, 30),
        ),
    )
    assert result.status == RuleResultStatus.TRIGGERED
    assert result.severity == "watch"


def test_recorded_spend_without_payment_date_is_not_assessable() -> None:
    result = evaluate_rule(
        _rule("R003"),
        _ctx(
            sanction_date=date(2023, 1, 1),
            expenditure_amount=50_000,
            first_payment_date=None,
            as_of_date=date(2024, 6, 30),
        ),
    )
    assert result.status == RuleResultStatus.NOT_ASSESSABLE
    assert "first_payment_date" in result.missing_fields


def test_project_severity_follows_triggered_attention_rule() -> None:
    result = assess_compliance(
        _ctx(recommended_date=date(2023, 6, 1), sanction_date=date(2023, 9, 1)),
        RULESET,
    )
    assert result.compliance_status == ComplianceStatus.RULES_TRIGGERED
    assert result.flagged is True
    assert result.severity.value == "attention"
    assert "R001" in result.triggered_rule_ids


def test_real_mode_is_inconclusive_or_has_assessable_non_triggers_only() -> None:
    result = assess_compliance(
        _ctx(
            mode=ComplianceMode.REAL,
            sanction_date=None,
            sanctioned_amount=None,
            expenditure_amount=None,
            as_of_date=None,
            category="Normal/Others",
            ida="KURNOOL_IDA",
        ),
        RULESET,
    )
    assert result.dataset_type == "REAL"
    assert result.triggered_rule_ids == [] or result.triggered_rule_ids == ["R015"]
    assert "R001" in result.not_assessable_rule_ids
    assert "R002" in result.not_assessable_rule_ids
    assert "R004" in result.not_assessable_rule_ids
    assert any(item.rule_id == "R015" for item in result.non_triggered_rules)
    assert "fraud" not in result.explanation.casefold()
