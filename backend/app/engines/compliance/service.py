"""Compliance Engine V1 orchestration.

Loads sourced rules and evaluates a project/evidence context.
Does not run cost, time, overlap, risk fusion, graph, copilot, or frontend.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from app.domain.enums import EvidenceEngine, EvidenceSeverity, EvidenceStatus
from app.engines.compliance.constants import (
    ENGINE_NAME,
    ENGINE_VERSION,
    EVIDENCE_TYPE,
    FORBIDDEN_MODEL_INPUT_COLUMNS,
    SEVERITY_RANK,
    SIGNAL_KIND,
    rules_path,
)
from app.engines.compliance.context import context_from_project
from app.engines.compliance.enrichment import HybridComplianceFields, load_hybrid_compliance_fields
from app.engines.compliance.apply import evaluate_rule
from app.engines.compliance.explain import project_explanation
from app.engines.compliance.loader import load_rules
from app.engines.compliance.types import (
    ComplianceContext,
    ComplianceIntelligenceResult,
    ComplianceMode,
    ComplianceStatus,
    RuleResult,
    RuleResultStatus,
    RuleSet,
)
from app.errors import AppError
from app.models.evidence import EvidenceObjectRow
from app.models.project import Project


def _dataset_type(mode: ComplianceMode) -> str:
    return "HYBRID" if mode == ComplianceMode.HYBRID_TEST else "REAL"


def _overall_status(results: list[RuleResult]) -> ComplianceStatus:
    if any(item.status == RuleResultStatus.TRIGGERED for item in results):
        return ComplianceStatus.RULES_TRIGGERED
    if any(item.status == RuleResultStatus.NOT_TRIGGERED for item in results):
        return ComplianceStatus.NO_RULES_TRIGGERED
    return ComplianceStatus.INCONCLUSIVE


def _overall_severity(results: list[RuleResult]) -> EvidenceSeverity:
    triggered = [item for item in results if item.status == RuleResultStatus.TRIGGERED]
    if not triggered:
        return EvidenceSeverity.INFO
    rank = max(SEVERITY_RANK.get(item.severity, 0) for item in triggered)
    if rank >= 2:
        return EvidenceSeverity.ATTENTION
    if rank == 1:
        return EvidenceSeverity.WATCH
    return EvidenceSeverity.INFO


def _evidence_status(compliance_status: ComplianceStatus) -> EvidenceStatus:
    if compliance_status == ComplianceStatus.RULES_TRIGGERED:
        return EvidenceStatus.MISMATCH
    if compliance_status == ComplianceStatus.NO_RULES_TRIGGERED:
        return EvidenceStatus.CONSISTENT
    return EvidenceStatus.INCONCLUSIVE


def assess_compliance(
    context: ComplianceContext,
    ruleset: RuleSet | None = None,
    *,
    rules_file: Path | None = None,
) -> ComplianceIntelligenceResult:
    """Pure evaluation against an in-memory context. Does not write to the database."""
    catalog = ruleset or load_rules(rules_path(rules_file))
    results = [evaluate_rule(rule, context) for rule in catalog.rules]
    triggered = [item for item in results if item.status == RuleResultStatus.TRIGGERED]
    not_triggered = [item for item in results if item.status == RuleResultStatus.NOT_TRIGGERED]
    not_assessable = [item for item in results if item.status == RuleResultStatus.NOT_ASSESSABLE]
    compliance_status = _overall_status(results)
    severity = _overall_severity(results)
    evidence_status = _evidence_status(compliance_status)
    refs: list[str] = []
    seen: set[str] = set()
    for item in results:
        para = item.source_reference.get("para")
        document = str(item.source_reference.get("document") or "")
        label = f"{document} para {para}" if para else document
        if label and label not in seen:
            seen.add(label)
            refs.append(label)
    result = ComplianceIntelligenceResult(
        project_id=context.project_id,
        internal_project_id=context.internal_project_id,
        engine=ENGINE_NAME,
        engine_version=ENGINE_VERSION,
        evidence_type=EVIDENCE_TYPE,
        dataset_type=_dataset_type(context.mode),
        compliance_mode=context.mode,
        compliance_status=compliance_status,
        flagged=bool(triggered),
        status=evidence_status,
        severity=severity,
        signal_kind=SIGNAL_KIND,
        triggered_rules=triggered,
        non_triggered_rules=not_triggered,
        not_assessable_rules=not_assessable,
        rule_results=results,
        observed_status=context.status,
        lifecycle_stage=context.lifecycle_stage,
        category=context.category,
        constituency=context.constituency,
        recommended_date=context.recommended_date,
        allocation_amount=context.allocation_amount,
        ida=context.ida,
        house=context.house,
        triggered_rule_ids=[item.rule_id for item in triggered],
        not_assessable_rule_ids=[item.rule_id for item in not_assessable],
        guideline_refs=refs,
    )
    result.explanation = project_explanation(result)
    return result


def assess_project_compliance(
    session: Session,
    project_id: int,
    *,
    mode: ComplianceMode = ComplianceMode.REAL,
    persist: bool = True,
    hybrid_fields: dict[str, HybridComplianceFields] | None = None,
    rules_file: Path | None = None,
) -> ComplianceIntelligenceResult:
    row = session.get(Project, project_id)
    if row is None:
        raise AppError("Project not found.", code="not_found", status_code=404)
    leaked = set(FORBIDDEN_MODEL_INPUT_COLUMNS).intersection(row.__dict__.keys())
    if leaked:
        raise RuntimeError(f"Project row unexpectedly contains label columns: {sorted(leaked)}")
    hybrid = None
    if mode == ComplianceMode.HYBRID_TEST:
        records = hybrid_fields if hybrid_fields is not None else load_hybrid_compliance_fields()
        hybrid = records.get(row.internal_project_id)
    context = context_from_project(row, mode=mode, hybrid=hybrid)
    result = assess_compliance(context, rules_file=rules_file)
    if persist:
        persist_compliance_evidence(session, result)
        session.commit()
    return result


def persist_compliance_evidence(
    session: Session,
    result: ComplianceIntelligenceResult,
) -> EvidenceObjectRow:
    """Replace the current compliance evidence object for this project."""
    from app.evidence.adapters.compliance import compliance_result_to_evidence
    from app.evidence.repository import persist_evidence_object

    project = session.get(Project, result.project_id)
    if project is None:
        raise AppError("Project not found.", code="not_found", status_code=404)
    obj = compliance_result_to_evidence(result, project, snapshot=project.snapshot)
    return persist_evidence_object(session, obj, replace_engine=EvidenceEngine.COMPLIANCE)
