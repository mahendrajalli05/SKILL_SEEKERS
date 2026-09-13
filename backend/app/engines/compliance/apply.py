"""Apply one sourced rule to a project context."""

from __future__ import annotations

from app.engines.compliance.explain import explanation_for_rule
from app.engines.compliance.fields import missing_required
from app.engines.compliance.loader import source_reference_dict
from app.engines.compliance.operators import apply_operator
from app.engines.compliance.types import (
    ComplianceContext,
    ComplianceMode,
    ComplianceRule,
    RuleResult,
    RuleResultStatus,
)


def dataset_label(mode: ComplianceMode) -> str:
    return "HYBRID/TEST" if mode == ComplianceMode.HYBRID_TEST else "real"


def evaluate_rule(rule: ComplianceRule, context: ComplianceContext) -> RuleResult:
    missing = missing_required(context, rule.required_fields)
    if missing:
        status = RuleResultStatus.NOT_ASSESSABLE
        evidence = {name: None for name in missing}
        explanation = explanation_for_rule(
            rule,
            status,
            missing_fields=missing,
            evidence=evidence,
            dataset_label=dataset_label(context.mode),
        )
        return _result(rule, status, explanation, evidence, missing)

    status, evidence, extra_missing = apply_operator(
        context,
        rule.evaluation_logic,
        rule_id=rule.rule_id,
    )
    if extra_missing and status == RuleResultStatus.NOT_ASSESSABLE:
        missing = extra_missing
    explanation = explanation_for_rule(
        rule,
        status,
        missing_fields=missing,
        evidence=evidence,
        dataset_label=dataset_label(context.mode),
    )
    return _result(rule, status, explanation, evidence, missing)


def _result(
    rule: ComplianceRule,
    status: RuleResultStatus,
    explanation: str,
    evidence: dict[str, object],
    missing: list[str],
) -> RuleResult:
    return RuleResult(
        rule_id=rule.rule_id,
        category=rule.category,
        title=rule.title,
        description=rule.description,
        status=status,
        severity=rule.severity,
        explanation=explanation,
        evidence=dict(evidence),
        source_reference=source_reference_dict(rule),
        missing_fields=list(missing),
        limitations=list(rule.limitations),
    )
