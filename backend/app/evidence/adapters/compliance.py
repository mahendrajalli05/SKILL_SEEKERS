"""Compliance Engine V1 → canonical Evidence Object.

Does not change rule logic. Scenario labels are not copied.
"""

from __future__ import annotations

from app.domain.enums import (
    DataMode,
    EvidenceDisposition,
    EvidenceEngine,
    SignalType,
    SourceType,
)
from app.domain.schemas.evidence import EvidenceObject
from app.engines.compliance.constants import ENGINE_NAME, ENGINE_VERSION
from app.engines.compliance.types import (
    ComplianceIntelligenceResult,
    ComplianceStatus,
)
from app.evidence.constants import DISPOSITION_TO_STATUS
from app.evidence.facts import confidence_unit, format_amount_statement, make_fact
from app.evidence.ids import make_evidence_id
from app.evidence.provenance import build_provenance, build_source_ids, resolve_data_mode
from app.models.project import Project
from app.models.snapshot import DatasetSnapshot


def _disposition(status: ComplianceStatus) -> EvidenceDisposition:
    if status == ComplianceStatus.RULES_TRIGGERED:
        return EvidenceDisposition.WHY_FLAGGED
    if status == ComplianceStatus.NO_RULES_TRIGGERED:
        return EvidenceDisposition.WHY_NOT_FLAGGED
    return EvidenceDisposition.NOT_ASSESSABLE


def _finding(result: ComplianceIntelligenceResult) -> str:
    if result.compliance_status == ComplianceStatus.RULES_TRIGGERED:
        ids = ", ".join(result.triggered_rule_ids) or "one or more rules"
        return f"Guideline rules triggered for review: {ids}"
    if result.compliance_status == ComplianceStatus.NO_RULES_TRIGGERED:
        return "Assessable guideline rules were not triggered"
    missing = ", ".join(result.not_assessable_rule_ids[:8]) or "required fields"
    return (
        "Guideline rules are not assessable from the available fields "
        f"({missing}). Missing government fields were not invented."
    )


def _confidence(result: ComplianceIntelligenceResult) -> int:
    assessable = len(result.triggered_rules) + len(result.non_triggered_rules)
    total = len(result.rule_results) or 1
    if result.compliance_status == ComplianceStatus.INCONCLUSIVE:
        return 8
    return min(70, 20 + int(50 * assessable / total))


def compliance_result_to_evidence(
    result: ComplianceIntelligenceResult,
    project: Project,
    *,
    snapshot: DatasetSnapshot | None = None,
) -> EvidenceObject:
    data_mode = resolve_data_mode(
        is_synthetic=bool(project.is_synthetic),
        engine_mode=result.compliance_mode.value,
    )
    source_type = (
        SourceType.SYNTHETIC_TEST_RECORD
        if data_mode == DataMode.SYNTHETIC
        else SourceType.HYBRID_ENRICHMENT
        if data_mode == DataMode.HYBRID
        else SourceType.MPLADS_PROJECT_RECORD
    )
    extra_ids = list(result.triggered_rule_ids) + list(result.guideline_refs[:12])
    source_ids = build_source_ids(result.internal_project_id, extra_ids)
    provenance = build_provenance(
        project,
        data_mode=data_mode,
        source_type=source_type,
        source_ids=source_ids,
        snapshot=snapshot,
        extra_notes="Guideline rule IDs and source references are preserved on this object.",
    )
    derived = ENGINE_VERSION
    rule_payload = [
        {
            "rule_id": item.rule_id,
            "category": item.category,
            "status": item.status.value,
            "severity": item.severity,
            "explanation": item.explanation,
            "evidence": item.evidence,
            "source_reference": item.source_reference,
            "missing_fields": item.missing_fields,
        }
        for item in result.rule_results
    ]
    facts = [
        make_fact(
            "allocation_amount",
            result.allocation_amount,
            "project.allocation_amount",
            statement=format_amount_statement(result.allocation_amount),
        ),
        make_fact("observed_status", result.observed_status, "project.status"),
        make_fact(
            "recommended_date",
            result.recommended_date.isoformat() if result.recommended_date else None,
            "project.recommended_date",
        ),
        make_fact("ida", result.ida, "project.ida"),
        make_fact("signal_kind", result.signal_kind, derived),
        make_fact("dataset_type", result.dataset_type, derived),
        make_fact("compliance_mode", result.compliance_mode.value, derived),
        make_fact("compliance_status", result.compliance_status.value, derived),
        make_fact("triggered_rule_ids", result.triggered_rule_ids, derived),
        make_fact("not_assessable_rule_ids", result.not_assessable_rule_ids, derived),
        make_fact("rule_results", rule_payload, derived),
        make_fact("data_mode", data_mode.value, derived),
    ]
    disposition = _disposition(result.compliance_status)
    engine_confidence = _confidence(result)
    return EvidenceObject(
        evidence_id=make_evidence_id(
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            project_id=result.project_id,
            signal_type=result.signal_kind,
            data_mode=data_mode.value,
        ),
        project_id=result.project_id,
        signal_type=SignalType.MPLADS_COMPLIANCE,
        finding=_finding(result),
        severity=result.severity,
        score=None,
        confidence=confidence_unit(engine_confidence),
        source_type=source_type,
        source_ids=source_ids,
        evidence_facts=facts,
        explanation=result.explanation,
        engine_name=EvidenceEngine.COMPLIANCE,
        engine_version=ENGINE_VERSION,
        data_mode=data_mode,
        provenance=provenance,
        disposition=disposition,
        status=DISPOSITION_TO_STATUS[disposition],
        rule_ids=list(result.triggered_rule_ids),
        guideline_refs=list(result.guideline_refs),
    )
