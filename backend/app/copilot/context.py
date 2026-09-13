"""Evidence context construction for Investigation Copilot V1."""

from __future__ import annotations

from typing import Any

from app.copilot.constants import (
    CITIZEN_LIMITATION,
    CONTEXT_NOT_PROJECT_FACT,
    GPS_UNAVAILABLE,
    HYBRID_NOTICE,
    REAL_NOTICE,
    SATELLITE_UNAVAILABLE,
    SYNTHETIC_NOTICE,
    TIME_REAL_LIMITATION,
    UNAVAILABLE_PHRASE,
)
from app.copilot.types import CopilotIntent, InvestigationBundle, SourceRef
from app.domain.enums import DataMode


def data_mode_notice(bundle: InvestigationBundle) -> str:
    if bundle.is_synthetic or bundle.data_mode == DataMode.SYNTHETIC:
        return SYNTHETIC_NOTICE
    if bundle.data_mode == DataMode.HYBRID:
        return HYBRID_NOTICE
    return REAL_NOTICE


def evidence_by_engine(bundle: InvestigationBundle, engine: str) -> list:
    return [item for item in bundle.evidence if item.engine == engine]


def source_refs_for(bundle: InvestigationBundle, evidence_ids: list[str]) -> list[SourceRef]:
    refs: list[SourceRef] = []
    seen: set[str] = set()
    if bundle.scheme_id:
        refs.append(SourceRef(id=bundle.scheme_id, kind="project", label="Scheme ID"))
        seen.add(bundle.scheme_id)
    if bundle.internal_project_id not in seen:
        refs.append(
            SourceRef(id=bundle.internal_project_id, kind="project", label="Internal project ID")
        )
        seen.add(bundle.internal_project_id)
    by_id = {item.evidence_id: item for item in bundle.evidence}
    for evidence_id in evidence_ids:
        if evidence_id in seen:
            continue
        item = by_id.get(evidence_id)
        label = f"{item.engine} {item.signal_type}" if item else "Evidence"
        refs.append(SourceRef(id=evidence_id, kind="evidence", label=label))
        seen.add(evidence_id)
    return refs


def allowed_identifiers(bundle: InvestigationBundle) -> set[str]:
    ids = {bundle.internal_project_id}
    if bundle.scheme_id:
        ids.add(bundle.scheme_id)
    for item in bundle.evidence:
        ids.add(item.evidence_id)
        ids.update(item.rule_ids)
        for comparable in item.comparables:
            if isinstance(comparable, dict):
                for key in (
                    "internal_project_id",
                    "linked_internal_project_id",
                    "evidence_id",
                ):
                    value = comparable.get(key)
                    if value:
                        ids.add(str(value))
    for report in bundle.citizen_reports:
        for evidence_id in report.get("evidence_ids") or []:
            ids.add(str(evidence_id))
    if bundle.pce:
        for evidence_id in bundle.pce.get("evidence_ids") or []:
            ids.add(str(evidence_id))
    if bundle.risk:
        ids.update(bundle.risk.evidence_ids)
    if bundle.risk_v2:
        ids.update(bundle.risk_v2.evidence_ids)
    return {item for item in ids if item}


def compact_context(bundle: InvestigationBundle, intent: CopilotIntent) -> dict[str, Any]:
    """Structured retrieval payload for templates or an optional LLM."""
    payload: dict[str, Any] = {
        "project": {
            "id": bundle.project_id,
            "scheme_id": bundle.scheme_id,
            "internal_project_id": bundle.internal_project_id,
            "work_description": bundle.work_description,
            "constituency": bundle.constituency,
            "category": bundle.category,
            "status": bundle.status,
            "allocation_amount": bundle.allocation_amount,
            "recommended_date": bundle.recommended_date,
            "state": bundle.state,
            "mp_name": bundle.mp_name,
            "data_mode": bundle.data_mode.value,
            "is_synthetic": bundle.is_synthetic,
            "hybrid_enrichment": bundle.hybrid_enrichment,
        },
        "data_mode_notice": data_mode_notice(bundle),
        "unavailable_fields": bundle.unavailable_fields,
        "intent": intent.value,
        "risk": None,
        "risk_v2": None,
        "lifecycle": None,
        "evidence": [],
        "pce": bundle.pce,
        "citizen_summary": bundle.citizen_summary,
        "citizen_reports": [
            {
                "id": item.get("id"),
                "satisfaction_rating": item.get("satisfaction_rating"),
                "observation_text": item.get("observation_text"),
                "issue_category": item.get("issue_category"),
                "submission_status": item.get("submission_status"),
                "verification_result": item.get("verification_result"),
                "evidence_ids": item.get("evidence_ids"),
                "data_mode": item.get("data_mode"),
            }
            for item in bundle.citizen_reports
        ],
        "milestones": bundle.milestones,
        "documents": [
            {
                "id": item.get("id"),
                "filename": item.get("filename"),
                "document_type": item.get("document_type"),
                "extraction_status": item.get("extraction_status"),
                "data_mode": item.get("data_mode"),
            }
            for item in bundle.documents
        ],
        "images": bundle.images,
        "semantic_hits": bundle.semantic_hits,
        "limitations": _limitations(bundle),
    }
    if bundle.risk_v2:
        payload["risk_v2"] = {
            "investigation_priority": bundle.risk_v2.investigation_priority,
            "evidence_confidence": bundle.risk_v2.evidence_confidence,
            "risk_class": bundle.risk_v2.risk_class,
            "explanation_type": bundle.risk_v2.explanation_type,
            "explanation": bundle.risk_v2.explanation,
            "recommended_action": bundle.risk_v2.recommended_action,
            "contributing": bundle.risk_v2.contributing,
            "independent": bundle.risk_v2.independent,
            "discounted": bundle.risk_v2.discounted,
            "unavailable": bundle.risk_v2.unavailable,
            "conflicting": bundle.risk_v2.conflicting,
            "evidence_ids": bundle.risk_v2.evidence_ids,
            "data_mode": bundle.risk_v2.data_mode,
            "synthetic_disclosure": bundle.risk_v2.synthetic_disclosure,
        }
    if bundle.lifecycle:
        payload["lifecycle"] = {
            "lifecycle_state": bundle.lifecycle.lifecycle_state,
            "source_status": bundle.lifecycle.source_status,
            "current_stage": bundle.lifecycle.current_stage,
            "planning_state": bundle.lifecycle.planning_state,
            "completed_stages": bundle.lifecycle.completed_stages,
            "pending_stages": bundle.lifecycle.pending_stages,
            "recommendation": bundle.lifecycle.recommendation,
            "last_milestone_decision": bundle.lifecycle.last_milestone_decision,
            "missing": bundle.lifecycle.missing,
            "data_mode": bundle.lifecycle.data_mode,
        }
    if bundle.risk:
        payload["risk"] = {
            "investigation_priority": bundle.risk.investigation_priority,
            "evidence_confidence": bundle.risk.evidence_confidence,
            "explanation_type": bundle.risk.explanation_type,
            "explanation": bundle.risk.explanation,
            "recommended_action": bundle.risk.recommended_action,
            "contributing": bundle.risk.contributing,
            "unavailable": bundle.risk.unavailable,
            "evidence_ids": bundle.risk.evidence_ids,
            "data_mode": bundle.risk.data_mode,
        }
    wanted_engines = _engines_for_intent(intent)
    for item in bundle.evidence:
        if wanted_engines and item.engine not in wanted_engines and intent not in {
            CopilotIntent.GENERAL,
            CopilotIntent.PROJECT_OVERVIEW,
            CopilotIntent.STRONGEST_EVIDENCE,
            CopilotIntent.MISSING_INFORMATION,
            CopilotIntent.INSPECT_NEXT,
            CopilotIntent.SIGNALS,
            CopilotIntent.RISK_V2_CONTRIBUTION,
            CopilotIntent.RISK_V2_CORRELATED,
            CopilotIntent.RISK_V2_CONFLICTING,
            CopilotIntent.RISK_V2_SCORE_CHANGE,
            CopilotIntent.LIFECYCLE_WHERE,
            CopilotIntent.LIFECYCLE_REMAINING,
            CopilotIntent.LIFECYCLE_LAST_MILESTONE,
            CopilotIntent.WHY_FLAGGED,
            CopilotIntent.WHY_NOT_FLAGGED,
        }:
            continue
        payload["evidence"].append(
            {
                "evidence_id": item.evidence_id,
                "engine": item.engine,
                "signal_type": item.signal_type,
                "finding": item.finding,
                "explanation": item.explanation,
                "disposition": item.disposition,
                "status": item.status,
                "score": item.score,
                "confidence": item.confidence,
                "data_mode": item.data_mode,
                "comparables": item.comparables[:8],
                "rule_ids": item.rule_ids,
                "guideline_refs": item.guideline_refs,
                "observed_facts": item.facts_observed[:12],
                "derived_facts": item.facts_derived[:12],
            }
        )
    return payload


def _engines_for_intent(intent: CopilotIntent) -> set[str]:
    mapping = {
        CopilotIntent.TIME_INCONCLUSIVE: {"time"},
        CopilotIntent.COMPARABLES: {"cost", "overlap"},
        CopilotIntent.COMPLIANCE: {"compliance"},
        CopilotIntent.CITIZEN: {"citizen"},
        CopilotIntent.SATELLITE: {"satellite"},
        CopilotIntent.GEOSPATIAL: {"geo", "image"},
        CopilotIntent.GRAPH: {"graph", "overlap"},
        CopilotIntent.DOCUMENTS: {"document"},
        CopilotIntent.IMAGES: {"image"},
        CopilotIntent.FORENSICS: {"forensics", "image"},
        CopilotIntent.NEED_IMPACT: {"need"},
        CopilotIntent.EXTERNAL_CONTEXT: {"context"},
        CopilotIntent.MILESTONE: {"milestone"},
        CopilotIntent.PCE_SUMMARY: {"pce", "document", "image"},
        CopilotIntent.ML_EVIDENCE: {"ml"},
        CopilotIntent.ML_FRAUD_CLARIFICATION: {"ml"},
    }
    return mapping.get(intent, set())


def _limitations(bundle: InvestigationBundle) -> list[str]:
    notes = [data_mode_notice(bundle)]
    if bundle.data_mode == DataMode.REAL:
        notes.append(TIME_REAL_LIMITATION)
        notes.append(GPS_UNAVAILABLE)
    if not evidence_by_engine(bundle, "satellite"):
        notes.append(SATELLITE_UNAVAILABLE)
    if evidence_by_engine(bundle, "context"):
        notes.append(CONTEXT_NOT_PROJECT_FACT)
    if bundle.citizen_reports or evidence_by_engine(bundle, "citizen"):
        notes.append(CITIZEN_LIMITATION)
    if not bundle.evidence:
        notes.append(UNAVAILABLE_PHRASE)
    return notes
