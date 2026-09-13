"""Rule-trace explanations. Not SHAP and not an ML model."""

from __future__ import annotations

from app.engines.compliance.constants import HYBRID_TEST_NOTE, REAL_LIMITATION_NOTE, SIGNAL_SEPARATION_NOTE
from app.engines.compliance.types import (
    ComplianceIntelligenceResult,
    ComplianceMode,
    ComplianceRule,
    RuleResult,
    RuleResultStatus,
)


def _source_clause(rule: ComplianceRule) -> str:
    ref = rule.source_reference
    para = f" Para {ref.para}." if ref.para else ""
    return f" Source: {ref.document}.{para} {ref.source_id}."


def explanation_for_rule(
    rule: ComplianceRule,
    status: RuleResultStatus,
    *,
    missing_fields: list[str],
    evidence: dict[str, object],
    dataset_label: str,
) -> str:
    if status == RuleResultStatus.NOT_ASSESSABLE:
        if rule.not_assessable_template:
            base = rule.not_assessable_template.replace(
                "current real dataset",
                f"current {dataset_label} dataset",
            )
        elif missing_fields:
            listed = ", ".join(missing_fields)
            base = (
                f"{listed} evidence is unavailable in the current {dataset_label} dataset."
            )
        else:
            base = (
                f"Required inputs for {rule.rule_id} are insufficient in the current "
                f"{dataset_label} dataset."
            )
        return base + _source_clause(rule)

    if status == RuleResultStatus.TRIGGERED:
        detail = _evidence_clause(evidence)
        return (
            f"{rule.rule_id}. Status: TRIGGERED. Required condition is not satisfied "
            f"based on the available project information.{detail}"
            + _source_clause(rule)
        )

    detail = _evidence_clause(evidence)
    return (
        f"{rule.rule_id}. Status: NOT_TRIGGERED. Required condition is satisfied "
        f"based on the available project information.{detail}"
        + _source_clause(rule)
    )


def _evidence_clause(evidence: dict[str, object]) -> str:
    skip = {
        "match_values",
        "comparison",
        "spend_used_as_payment_proxy",
        "payment_date_unavailable_with_recorded_spend",
        "repair_admissible_under_guidelines_2023",
        "invalid_date_order",
        "end_field_used",
    }
    parts: list[str] = []
    for key in sorted(evidence):
        if key in skip:
            continue
        value = evidence[key]
        if value is None or value == "":
            continue
        parts.append(f"{key}={value}")
    if not parts:
        return ""
    return " Evidence: " + "; ".join(parts) + "."


def project_explanation(result: ComplianceIntelligenceResult) -> str:
    triggered = [item.rule_id for item in result.triggered_rules]
    assessable = [item.rule_id for item in result.non_triggered_rules]
    pending = [item.rule_id for item in result.not_assessable_rules]
    lines = [
        SIGNAL_SEPARATION_NOTE,
        (
            f"Compliance status: {result.compliance_status.value}. "
            f"Triggered: {', '.join(triggered) if triggered else 'none'}. "
            f"Not triggered (assessable): {', '.join(assessable) if assessable else 'none'}. "
            f"Not assessable: {', '.join(pending) if pending else 'none'}."
        ),
    ]
    if result.compliance_mode == ComplianceMode.HYBRID_TEST:
        lines.append(HYBRID_TEST_NOTE)
    else:
        lines.append(REAL_LIMITATION_NOTE)
    if result.triggered_rules:
        lines.append(result.triggered_rules[0].explanation)
    elif result.not_assessable_rules and not result.non_triggered_rules:
        lines.append(
            "No assessable guideline condition could be evaluated from the available fields."
        )
    else:
        lines.append(
            "No sourced guideline condition was triggered from the available project information."
        )
    blob = " ".join(lines)
    assert "fraud" not in blob.casefold()
    return blob
