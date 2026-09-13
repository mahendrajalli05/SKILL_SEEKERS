"""Deterministic operators for the compliance rule catalog."""

from __future__ import annotations

from typing import Any

from app.engines.compliance.errors import ComplianceRuleError
from app.engines.compliance.fields import as_bool, as_date, as_number, days_between, field_value, is_missing
from app.engines.compliance.types import ComplianceContext, RuleResultStatus


def _threshold(logic: dict[str, Any], rule_id: str) -> float:
    if "threshold" not in logic:
        raise ComplianceRuleError(f"{rule_id}: evaluation_logic.threshold is required.")
    value = as_number(logic.get("threshold"))
    if value is None:
        raise ComplianceRuleError(f"{rule_id}: threshold must be numeric.")
    return value


def _constant(logic: dict[str, Any], rule_id: str) -> float:
    if "right_constant" not in logic:
        raise ComplianceRuleError(f"{rule_id}: evaluation_logic.right_constant is required.")
    value = as_number(logic.get("right_constant"))
    if value is None:
        raise ComplianceRuleError(f"{rule_id}: right_constant must be numeric.")
    return value


def apply_operator(
    context: ComplianceContext,
    logic: dict[str, Any],
    *,
    rule_id: str,
) -> tuple[RuleResultStatus, dict[str, Any], list[str]]:
    operator = str(logic.get("operator") or "").strip()
    if operator == "date_diff_gt":
        return _date_diff_gt(context, logic, rule_id=rule_id)
    if operator == "duration_gt":
        return _duration_gt(context, logic, rule_id=rule_id)
    if operator == "numeric_gt":
        return _numeric_compare(context, logic, rule_id=rule_id, triggered_when="gt")
    if operator == "numeric_lt":
        return _numeric_compare(context, logic, rule_id=rule_id, triggered_when="lt")
    if operator == "no_recorded_spend_after_days":
        return _no_recorded_spend(context, logic, rule_id=rule_id)
    if operator == "boolean_true":
        return _boolean(context, logic, triggered_when_true=True)
    if operator == "boolean_true_not_triggered":
        return _boolean(context, logic, triggered_when_true=False)
    if operator == "blank_triggers":
        return _blank_triggers(context, logic)
    if operator == "repair_admissible":
        return _repair_admissible(context, logic)
    raise ComplianceRuleError(f"{rule_id}: unknown operator '{operator}'.")


def _date_diff_gt(
    context: ComplianceContext,
    logic: dict[str, Any],
    *,
    rule_id: str,
) -> tuple[RuleResultStatus, dict[str, Any], list[str]]:
    left_name = str(logic.get("left_field") or "")
    right_name = str(logic.get("right_field") or "")
    left = as_date(field_value(context, left_name))
    right = as_date(field_value(context, right_name))
    evidence = {left_name: _iso(left), right_name: _iso(right)}
    if left is None or right is None:
        missing = [name for name, value in ((left_name, left), (right_name, right)) if value is None]
        return RuleResultStatus.NOT_ASSESSABLE, evidence, missing
    days = days_between(right, left)
    evidence["days"] = days
    evidence["threshold_days"] = int(_threshold(logic, rule_id))
    if days is None:
        return RuleResultStatus.NOT_ASSESSABLE, evidence, [left_name, right_name]
    if days < 0:
        evidence["invalid_date_order"] = True
        return RuleResultStatus.NOT_ASSESSABLE, evidence, []
    threshold = int(_threshold(logic, rule_id))
    status = RuleResultStatus.TRIGGERED if days > threshold else RuleResultStatus.NOT_TRIGGERED
    return status, evidence, []


def _duration_gt(
    context: ComplianceContext,
    logic: dict[str, Any],
    *,
    rule_id: str,
) -> tuple[RuleResultStatus, dict[str, Any], list[str]]:
    start_name = str(logic.get("start_field") or "")
    end_name = str(logic.get("end_field") or "")
    as_of_name = str(logic.get("as_of_field") or "as_of_date")
    start = as_date(field_value(context, start_name))
    end = as_date(field_value(context, end_name))
    as_of = as_date(field_value(context, as_of_name))
    used_end_field = end_name if end is not None else as_of_name
    used_end = end if end is not None else as_of
    evidence = {
        start_name: _iso(start),
        end_name: _iso(end),
        as_of_name: _iso(as_of),
        "end_field_used": used_end_field,
    }
    if start is None:
        return RuleResultStatus.NOT_ASSESSABLE, evidence, [start_name]
    if used_end is None:
        return RuleResultStatus.NOT_ASSESSABLE, evidence, [end_name, as_of_name]
    days = days_between(start, used_end)
    evidence["days"] = days
    evidence["threshold_days"] = int(_threshold(logic, rule_id))
    if days is None or days < 0:
        evidence["invalid_date_order"] = days is not None and days < 0
        return RuleResultStatus.NOT_ASSESSABLE, evidence, []
    threshold = int(_threshold(logic, rule_id))
    status = RuleResultStatus.TRIGGERED if days > threshold else RuleResultStatus.NOT_TRIGGERED
    return status, evidence, []


def _numeric_compare(
    context: ComplianceContext,
    logic: dict[str, Any],
    *,
    rule_id: str,
    triggered_when: str,
) -> tuple[RuleResultStatus, dict[str, Any], list[str]]:
    left_name = str(logic.get("left_field") or "")
    left = as_number(field_value(context, left_name))
    if "right_field" in logic:
        right_name = str(logic.get("right_field") or "")
        right = as_number(field_value(context, right_name))
        evidence = {left_name: left, right_name: right}
        missing = [name for name, value in ((left_name, left), (right_name, right)) if value is None]
    else:
        right_name = "right_constant"
        right = _constant(logic, rule_id)
        evidence = {left_name: left, right_name: right}
        missing = [left_name] if left is None else []
    if missing:
        return RuleResultStatus.NOT_ASSESSABLE, evidence, missing
    assert left is not None and right is not None
    if triggered_when == "gt":
        triggered = left > right
    else:
        triggered = left < right
    evidence["comparison"] = triggered_when
    status = RuleResultStatus.TRIGGERED if triggered else RuleResultStatus.NOT_TRIGGERED
    return status, evidence, []


def _no_recorded_spend(
    context: ComplianceContext,
    logic: dict[str, Any],
    *,
    rule_id: str,
) -> tuple[RuleResultStatus, dict[str, Any], list[str]]:
    start_name = str(logic.get("start_field") or "")
    payment_name = str(logic.get("payment_date_field") or "first_payment_date")
    spend_name = str(logic.get("expenditure_field") or "expenditure_amount")
    as_of_name = str(logic.get("as_of_field") or "as_of_date")
    start = as_date(field_value(context, start_name))
    payment = as_date(field_value(context, payment_name))
    spend = as_number(field_value(context, spend_name))
    as_of = as_date(field_value(context, as_of_name))
    threshold = int(_threshold(logic, rule_id))
    evidence: dict[str, Any] = {
        start_name: _iso(start),
        payment_name: _iso(payment),
        spend_name: spend,
        as_of_name: _iso(as_of),
        "threshold_days": threshold,
    }
    if start is None:
        return RuleResultStatus.NOT_ASSESSABLE, evidence, [start_name]
    if payment is not None:
        days = days_between(start, payment)
        evidence["days"] = days
        if days is None or days < 0:
            return RuleResultStatus.NOT_ASSESSABLE, evidence, []
        status = RuleResultStatus.TRIGGERED if days > threshold else RuleResultStatus.NOT_TRIGGERED
        return status, evidence, []
    if spend is None:
        return RuleResultStatus.NOT_ASSESSABLE, evidence, [payment_name, spend_name]
    if as_of is None:
        return RuleResultStatus.NOT_ASSESSABLE, evidence, [as_of_name]
    days = days_between(start, as_of)
    evidence["days"] = days
    evidence["spend_used_as_payment_proxy"] = True
    if days is None or days < 0:
        return RuleResultStatus.NOT_ASSESSABLE, evidence, []
    if spend == 0:
        status = RuleResultStatus.TRIGGERED if days > threshold else RuleResultStatus.NOT_TRIGGERED
        return status, evidence, []
    evidence["payment_date_unavailable_with_recorded_spend"] = True
    return RuleResultStatus.NOT_ASSESSABLE, evidence, [payment_name]


def _boolean(
    context: ComplianceContext,
    logic: dict[str, Any],
    *,
    triggered_when_true: bool,
) -> tuple[RuleResultStatus, dict[str, Any], list[str]]:
    name = str(logic.get("field") or "")
    value = as_bool(field_value(context, name))
    evidence = {name: value}
    if value is None:
        return RuleResultStatus.NOT_ASSESSABLE, evidence, [name]
    triggered = value if triggered_when_true else (not value)
    status = RuleResultStatus.TRIGGERED if triggered else RuleResultStatus.NOT_TRIGGERED
    return status, evidence, []


def _blank_triggers(
    context: ComplianceContext,
    logic: dict[str, Any],
) -> tuple[RuleResultStatus, dict[str, Any], list[str]]:
    name = str(logic.get("field") or "")
    value = field_value(context, name)
    evidence = {name: value if not is_missing(value) else ""}
    if is_missing(value):
        return RuleResultStatus.TRIGGERED, evidence, []
    return RuleResultStatus.NOT_TRIGGERED, evidence, []


def _repair_admissible(
    context: ComplianceContext,
    logic: dict[str, Any],
) -> tuple[RuleResultStatus, dict[str, Any], list[str]]:
    name = str(logic.get("field") or "category")
    value = str(field_value(context, name) or "").strip()
    matches = [str(item).strip() for item in logic.get("match_values") or []]
    evidence = {name: value, "match_values": matches}
    if not value:
        return RuleResultStatus.NOT_ASSESSABLE, evidence, [name]
    if value in matches:
        evidence["repair_admissible_under_guidelines_2023"] = True
        return RuleResultStatus.NOT_TRIGGERED, evidence, []
    return RuleResultStatus.NOT_ASSESSABLE, evidence, []


def _iso(value: date | None) -> str | None:
    return value.isoformat() if value else None
