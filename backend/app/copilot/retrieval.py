"""Structured retrieval for Investigation Copilot V1.

Reads stored project fields, Evidence Objects, and existing service
snapshots. Does not recalculate Cost, Time, Overlap, Compliance, or
Risk Fusion scoring. Does not persist engine side-effects.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.copilot.constants import (
    MAX_CITIZEN_SNIPPETS,
    MAX_DOCUMENT_SNIPPETS,
    UNAVAILABLE_PHRASE,
)
from app.copilot.semantic import rank_texts
from app.copilot.types import EvidenceSlice, InvestigationBundle, LifecycleSlice, RiskSlice, RiskV2Slice
from app.domain.enums import DataMode, EvidenceFactKind
from app.domain.schemas.evidence import EvidenceObject
from app.engines.citizen.service import list_project_reports, parse_data_mode as citizen_mode
from app.engines.citizen.service import project_citizen_summary
from app.engines.document.repository import get_artifact, list_project_documents
from app.engines.fusion.service import assess_project_risk, select_evidence_for_mode
from app.engines.fusion_v2.service import assess_project_risk_v2
from app.engines.fusion_v2.types import FusionV2Result
from app.engines.image.service import project_image_summary
from app.engines.lifecycle.service import get_project_lifecycle
from app.engines.milestone.service import list_project_milestones, parse_data_mode as milestone_mode
from app.engines.pce.service import parse_data_mode as pce_mode
from app.engines.pce.service import verify_project
from app.evidence.repository import list_project_evidence
from app.identity.scheme_id import scheme_id_for_project
from app.models.fusion import FusionScore
from app.models.fusion_v2 import FusionScoreV2
from app.models.project import Project
from app.scope import resolve_data_mode
from app.search.availability import UNAVAILABLE_REAL_FIELDS
from app.search.hybrid import has_hybrid_enrichment


def parse_copilot_data_mode(value: str | DataMode | None, project: Project) -> DataMode:
    if project.is_synthetic:
        return DataMode.SYNTHETIC
    if isinstance(value, DataMode):
        return value
    text = str(value or "").strip().upper().replace("-", "_")
    if text in {"HYBRID", "HYBRID_TEST", "HYBRIDTEST", "HYBRID_DEMO"}:
        return DataMode.HYBRID
    if text in {"SYNTHETIC"}:
        return DataMode.SYNTHETIC
    resolved = resolve_data_mode(text.lower() if text else None)
    if resolved == "HYBRID":
        return DataMode.HYBRID
    return DataMode.REAL


def _fact_payload(fact) -> dict[str, Any]:
    return {
        "key": fact.key,
        "value": fact.value,
        "source": fact.source,
        "kind": fact.kind.value if hasattr(fact.kind, "value") else str(fact.kind),
        "statement": fact.statement,
    }


def _slice_from_object(obj: EvidenceObject) -> EvidenceSlice:
    observed = [_fact_payload(item) for item in obj.evidence_facts if item.kind == EvidenceFactKind.OBSERVATION]
    derived = [_fact_payload(item) for item in obj.evidence_facts if item.kind != EvidenceFactKind.OBSERVATION]
    return EvidenceSlice(
        evidence_id=obj.evidence_id,
        engine=str(obj.engine_name),
        signal_type=obj.signal_type.value if hasattr(obj.signal_type, "value") else str(obj.signal_type),
        finding=obj.finding,
        explanation=obj.explanation,
        disposition=obj.disposition.value if hasattr(obj.disposition, "value") else str(obj.disposition),
        status=obj.status.value if hasattr(obj.status, "value") else str(obj.status),
        score=obj.score,
        confidence=obj.confidence,
        data_mode=obj.data_mode.value if hasattr(obj.data_mode, "value") else str(obj.data_mode),
        facts_observed=observed,
        facts_derived=derived,
        comparables=list(obj.comparables or []),
        rule_ids=list(obj.rule_ids or []),
        guideline_refs=list(obj.guideline_refs or []),
    )


def _safe_json(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def _risk_from_stored(row: FusionScore, data_mode: DataMode) -> RiskSlice | None:
    if not row.data_mode or row.data_mode != data_mode.value:
        return None
    payload = _safe_json(row.payload_json, {})
    explanation = row.why_flagged or row.why_not_flagged
    if isinstance(payload, dict):
        explanation = str(payload.get("explanation") or explanation or "")
        contributing = list(payload.get("contributing_signals") or [])
        unavailable = list(payload.get("unavailable_signals") or [])
        evidence_ids = list(payload.get("evidence_ids") or [])
        ip_100 = payload.get("investigation_priority_0_100")
    else:
        contributing, unavailable, evidence_ids, ip_100 = [], [], [], None
    return RiskSlice(
        investigation_priority=row.investigation_priority,
        investigation_priority_0_100=float(ip_100) if ip_100 is not None else None,
        evidence_confidence=row.evidence_confidence,
        explanation_type=row.explanation_type,
        explanation=explanation,
        recommended_action=row.recommended_action,
        contributing=contributing,
        unavailable=unavailable,
        evidence_ids=evidence_ids,
        data_mode=row.data_mode,
        stored=True,
    )


def _risk_from_fusion(session: Session, project: Project, data_mode: DataMode) -> RiskSlice:
    row = session.scalars(select(FusionScore).where(FusionScore.project_id == project.id)).first()
    if row is not None:
        sliced = _risk_from_stored(row, data_mode)
        if sliced is not None:
            return sliced
    result = assess_project_risk(session, project.id, data_mode=data_mode, persist=False)
    return RiskSlice(
        investigation_priority=result.investigation_priority,
        investigation_priority_0_100=result.investigation_priority_0_100,
        evidence_confidence=result.evidence_confidence,
        explanation_type=result.explanation_type.value,
        explanation=result.explanation,
        recommended_action=result.recommended_action.value,
        contributing=[item.as_payload() for item in result.contributing_signals],
        unavailable=[item.as_payload() for item in result.unavailable_signals],
        evidence_ids=list(result.evidence_ids),
        data_mode=result.data_mode.value,
        stored=False,
    )


def _strip_paths(payload: dict[str, Any]) -> dict[str, Any]:
    blocked = {"path", "watermark_path", "storage_path", "absolute_path", "file_path"}
    cleaned: dict[str, Any] = {}
    for key, value in payload.items():
        if key in blocked:
            continue
        if isinstance(value, dict):
            cleaned[key] = _strip_paths(value)
        elif isinstance(value, list):
            cleaned[key] = [
                _strip_paths(item) if isinstance(item, dict) else item for item in value
            ]
        else:
            cleaned[key] = value
    return cleaned


def _document_payloads(session: Session, project_id: int, data_mode: DataMode) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for row in list_project_documents(session, project_id)[: MAX_DOCUMENT_SNIPPETS * 2]:
        if data_mode == DataMode.REAL and row.data_mode and row.data_mode != DataMode.REAL.value:
            continue
        artifact = get_artifact(session, row.id)
        extract = None
        if artifact is not None and artifact.extracted_fields_json:
            extract = artifact.extracted_fields_json[:800]
        items.append(
            {
                "id": f"document:{row.id}",
                "document_id": row.id,
                "filename": row.filename,
                "document_type": row.document_type or row.kind,
                "extraction_status": row.extraction_status,
                "data_mode": row.data_mode,
                "text": (row.extracted_text or extract or row.notes or "")[:800],
            }
        )
        if len(items) >= MAX_DOCUMENT_SNIPPETS:
            break
    return items


def _pce_payload(session: Session, project: Project, data_mode: DataMode) -> dict[str, Any] | None:
    try:
        mode = pce_mode(data_mode, project)
        result = verify_project(session, project, mode, persist=False)
    except Exception:
        return None
    return {
        "overall_result": result.overall_result.value if hasattr(result.overall_result, "value") else str(result.overall_result),
        "explanation": result.explanation,
        "missing_information": list(result.missing_information),
        "plan_findings": list(result.plan_findings),
        "claim_findings": list(result.claim_findings),
        "evidence_findings": list(result.evidence_findings),
        "evidence_ids": list(result.evidence_ids),
        "evidence_confidence": result.evidence_confidence,
        "data_mode": result.data_mode.value if hasattr(result.data_mode, "value") else str(result.data_mode),
        "mismatches": [
            {
                "field": item.field,
                "status": item.status.value if hasattr(item.status, "value") else str(item.status),
                "explanation": item.explanation,
            }
            for item in result.mismatches
        ],
    }


def _citizen_payloads(session: Session, project: Project, data_mode: DataMode) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    mode = citizen_mode(data_mode, project)
    reports = list_project_reports(session, project, mode, include_location=False)
    items: list[dict[str, Any]] = []
    for record in reports[:MAX_CITIZEN_SNIPPETS]:
        payload = _strip_paths(record.as_dict())
        payload.pop("latitude", None)
        payload.pop("longitude", None)
        payload.pop("thumbnail_data_url", None)
        items.append(
            {
                "id": f"citizen:{payload.get('citizen_report_id')}",
                "citizen_report_id": payload.get("citizen_report_id"),
                "satisfaction_rating": payload.get("satisfaction_rating"),
                "observation_text": payload.get("observation_text"),
                "issue_category": payload.get("issue_category"),
                "submission_status": payload.get("submission_status"),
                "verification_result": payload.get("verification_result"),
                "evidence_ids": payload.get("evidence_ids") or [],
                "data_mode": payload.get("data_mode"),
                "synthetic": payload.get("synthetic"),
                "text": payload.get("observation_text") or "",
            }
        )
    try:
        summary = project_citizen_summary(session, project, mode, persist=False)
        summary_payload = _strip_paths(summary.as_dict())
        summary_payload.pop("latitude", None)
        summary_payload.pop("longitude", None)
    except Exception:
        summary_payload = None
    return items, summary_payload


def _milestone_payload(session: Session, project: Project, data_mode: DataMode) -> dict[str, Any] | None:
    try:
        mode = milestone_mode(data_mode, project)
        bundle = list_project_milestones(session, project, mode)
    except Exception:
        return None
    items = []
    for record in bundle.items:
        payload = record.as_dict() if hasattr(record, "as_dict") else {}
        items.append(
            {
                "milestone_id": payload.get("milestone_id") or getattr(record, "milestone_id", None),
                "milestone_name": payload.get("milestone_name") or getattr(record, "milestone_name", None),
                "recommendation": payload.get("recommendation") or getattr(record, "recommendation", None),
                "status": payload.get("status") or getattr(record, "status", None),
                "evidence_status": payload.get("evidence_status") or getattr(record, "evidence_status", None),
            }
        )
    return {
        "current_recommendation": bundle.current_recommendation,
        "items": items,
        "investigation_priority": bundle.investigation_priority,
        "evidence_confidence": bundle.evidence_confidence,
        "hybrid_notice": bundle.hybrid_notice,
    }


def _risk_v2_from_result(result: FusionV2Result, *, stored: bool) -> RiskV2Slice:
    return RiskV2Slice(
        investigation_priority=result.investigation_priority,
        evidence_confidence=result.evidence_confidence,
        risk_class=result.risk_class.value,
        explanation_type=result.explanation_type.value,
        explanation=result.explanation,
        recommended_action=result.recommended_action.value,
        contributing=[item.as_payload() for item in result.contributing_evidence_groups],
        independent=[item.as_payload() for item in result.independent_evidence_groups],
        discounted=[item.as_payload() for item in result.discounted_correlated_evidence],
        unavailable=[item.as_payload() for item in result.unavailable_evidence],
        conflicting=[item.as_payload() for item in result.conflicting_evidence],
        breakdown=[item.as_payload() for item in result.all_groups],
        evidence_ids=list(result.evidence_ids),
        data_mode=result.data_mode.value,
        synthetic_disclosure=result.synthetic_disclosure,
        stored=stored,
    )


def _risk_v2_from_stored(row: FusionScoreV2, data_mode: DataMode) -> RiskV2Slice | None:
    if row.data_mode != data_mode.value:
        return None
    payload = _safe_json(row.payload_json, {})
    if not isinstance(payload, dict):
        payload = {}
    return RiskV2Slice(
        investigation_priority=row.investigation_priority,
        evidence_confidence=row.evidence_confidence,
        risk_class=row.risk_class,
        explanation_type=row.explanation_type,
        explanation=str(payload.get("explanation") or ""),
        recommended_action=row.recommended_action,
        contributing=list(payload.get("contributing_evidence_groups") or []),
        independent=list(payload.get("independent_evidence_groups") or []),
        discounted=list(payload.get("discounted_correlated_evidence") or []),
        unavailable=list(payload.get("unavailable_evidence") or []),
        conflicting=list(payload.get("conflicting_evidence") or []),
        breakdown=list(payload.get("all_groups") or []),
        evidence_ids=list(payload.get("evidence_ids") or []),
        data_mode=row.data_mode,
        synthetic_disclosure=payload.get("synthetic_disclosure") if isinstance(payload.get("synthetic_disclosure"), str) else None,
        stored=True,
    )


def _risk_v2_from_fusion(session: Session, project: Project, data_mode: DataMode) -> RiskV2Slice:
    row = session.scalars(
        select(FusionScoreV2).where(
            FusionScoreV2.project_id == project.id,
            FusionScoreV2.data_mode == data_mode.value,
        )
    ).first()
    if row is not None:
        sliced = _risk_v2_from_stored(row, data_mode)
        if sliced is not None:
            return sliced
    result = assess_project_risk_v2(session, project.id, data_mode=data_mode, persist=False)
    return _risk_v2_from_result(result, stored=False)


def _lifecycle_slice(session: Session, project: Project, data_mode: DataMode) -> LifecycleSlice | None:
    try:
        result = get_project_lifecycle(session, project, data_mode)
    except Exception:
        return None
    last_ms = None
    if result.milestone_summary:
        last = result.milestone_summary.get("last_officer_action") or {}
        last_ms = last.get("officer_action") or result.milestone_summary.get("current_recommendation")
    pending_verify = [
        item.stage
        for item in result.timeline
        if item.status in {"PENDING", "CURRENT", "INCONCLUSIVE", "NOT AVAILABLE"}
        and item.stage
        not in {
            "FUTURE",
            "PRIORITIZATION",
            "ONGOING",
            "COMPLETION",
        }
    ]
    return LifecycleSlice(
        lifecycle_state=result.lifecycle_state,
        source_status=result.source_status,
        current_stage=result.current_stage,
        planning_state=result.planning_state,
        completed_stages=list(result.completed_stages),
        pending_stages=list(result.pending_stages),
        timeline=[item.as_dict() for item in result.timeline],
        recommendation=result.recommendation,
        last_milestone_decision=last_ms,
        missing=list(result.unavailable_inputs) + pending_verify[:8],
        data_mode=result.data_mode.value if hasattr(result.data_mode, "value") else str(result.data_mode),
        explanation=result.explanation,
    )


def retrieve_bundle(
    session: Session,
    project: Project,
    data_mode: DataMode,
    *,
    question: str = "",
) -> InvestigationBundle:
    stored = list_project_evidence(session, project.id)
    selected = select_evidence_for_mode(stored, data_mode)
    selected_ids = {item.evidence_id for item in selected}
    extra = [
        item
        for item in stored
        if item.evidence_id not in selected_ids
        and (data_mode != DataMode.REAL or item.data_mode == DataMode.REAL)
        and str(item.engine_name) not in {"cost", "time", "overlap", "compliance"}
    ]
    evidence = [_slice_from_object(item) for item in [*selected, *extra]]
    unavailable = [dict(item) for item in UNAVAILABLE_REAL_FIELDS]
    hybrid = has_hybrid_enrichment(project.internal_project_id)
    documents = _document_payloads(session, project.id, data_mode)
    try:
        images = project_image_summary(session, project, data_mode)
        images = _strip_paths(images) if isinstance(images, dict) else None
    except Exception:
        images = None
    citizen_reports, citizen_summary = _citizen_payloads(session, project, data_mode)
    pce = _pce_payload(session, project, data_mode)
    milestones = _milestone_payload(session, project, data_mode)
    risk = _risk_from_fusion(session, project, data_mode)
    risk_v2 = _risk_v2_from_fusion(session, project, data_mode)
    lifecycle = _lifecycle_slice(session, project, data_mode)
    corpus: list[dict[str, str]] = []
    for item in evidence:
        corpus.append(
            {
                "id": item.evidence_id,
                "title": f"{item.engine} {item.signal_type}",
                "text": f"{item.finding} {item.explanation}",
            }
        )
    for item in documents:
        corpus.append({"id": str(item["id"]), "title": str(item.get("filename") or "document"), "text": str(item.get("text") or "")})
    for item in citizen_reports:
        corpus.append({"id": str(item["id"]), "title": "citizen observation", "text": str(item.get("text") or "")})
    semantic_hits = rank_texts(question, corpus) if question else []
    return InvestigationBundle(
        project_id=project.id,
        internal_project_id=project.internal_project_id,
        scheme_id=scheme_id_for_project(session, project),
        data_mode=data_mode,
        is_synthetic=bool(project.is_synthetic),
        hybrid_enrichment=bool(hybrid),
        work_description=project.work_description,
        constituency=project.constituency,
        category=project.category,
        status=project.status,
        allocation_amount=project.allocation_amount,
        recommended_date=project.recommended_date.isoformat() if project.recommended_date else None,
        mp_name=project.mp_name,
        state=project.state,
        unavailable_fields=unavailable,
        evidence=evidence,
        risk=risk,
        risk_v2=risk_v2,
        lifecycle=lifecycle,
        pce=pce,
        documents=documents,
        images=images,
        citizen_reports=citizen_reports,
        citizen_summary=citizen_summary,
        milestones=milestones,
        semantic_hits=semantic_hits,
    )


def engines_present(bundle: InvestigationBundle) -> list[str]:
    return sorted({item.engine for item in bundle.evidence})


def unavailable_message(_topic: str | None = None) -> str:
    return UNAVAILABLE_PHRASE
