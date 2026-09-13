"""Read-only summaries from existing engines. Does not duplicate scoring."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.domain.enums import DataMode, EvidenceEngine
from app.domain.schemas.evidence import EvidenceObject
from app.engines.citizen.service import parse_data_mode as citizen_mode
from app.engines.citizen.service import project_citizen_summary
from app.engines.document.repository import list_project_documents
from app.engines.fusion_v2.service import assess_project_risk_v2
from app.engines.fusion_v2.types import FusionV2Result
from app.engines.image.service import project_image_summary
from app.engines.milestone.service import list_project_milestones, parse_data_mode as milestone_mode
from app.engines.need.service import assess_project_need_impact, parse_data_mode as need_mode
from app.engines.pce.service import get_project_plan, parse_data_mode as pce_mode, verify_project
from app.models.fusion_v2 import FusionScoreV2
from app.models.project import Project
from sqlalchemy import select


def _engine_items(items: list[EvidenceObject], engine: str) -> list[EvidenceObject]:
    return [item for item in items if str(item.engine_name) == engine]


def _disposition_status(items: list[EvidenceObject]) -> tuple[bool, str | None, list[str]]:
    if not items:
        return False, None, []
    ids = [item.evidence_id for item in items if item.evidence_id]
    flagged = any(str(item.disposition) == "WHY_FLAGGED" for item in items)
    inconclusive = all(
        str(item.disposition) in {"INCONCLUSIVE", "NOT_ASSESSABLE"}
        or str(item.status) in {"inconclusive", "not_assessable"}
        for item in items
    )
    if flagged:
        return True, "FLAGGED_FOR_REVIEW", ids
    if inconclusive:
        return True, "INCONCLUSIVE", ids
    return True, str(items[0].disposition), ids


def evidence_module_summary(items: list[EvidenceObject]) -> dict[str, Any]:
    by_engine: dict[str, list[EvidenceObject]] = {}
    for item in items:
        by_engine.setdefault(str(item.engine_name), []).append(item)
    modules = []
    for engine in sorted(by_engine):
        available, status, ids = _disposition_status(by_engine[engine])
        modules.append(
            {
                "engine": engine,
                "available": available,
                "status": status,
                "count": len(by_engine[engine]),
                "evidence_ids": ids,
            }
        )
    return {
        "count": len(items),
        "engines": sorted(by_engine.keys()),
        "modules": modules,
        "evidence_ids": [item.evidence_id for item in items if item.evidence_id],
        "note": "Existing Evidence Object V1 records only. Lifecycle does not create duplicate evidence.",
    }


def need_summary(session: Session, project: Project, data_mode: DataMode) -> dict[str, Any] | None:
    try:
        mode = need_mode(data_mode, project)
        result = assess_project_need_impact(session, project, mode, persist=False)
    except Exception:
        return None
    return {
        "need_score": result.need.score,
        "impact_score": result.impact.score,
        "priority_score": result.priority_score,
        "priority_class": result.priority_class,
        "evidence_confidence": result.evidence_confidence,
        "unavailable_inputs": list(result.unavailable_inputs),
        "recommendation_rationale": result.explanation,
        "finding": result.finding,
        "automatic_sanction": False,
        "sanction_decision": None,
        "enrichment_used": result.enrichment_used,
        "enrichment_label": result.enrichment_label,
        "data_mode": result.data_mode.value if hasattr(result.data_mode, "value") else str(result.data_mode),
        "evidence_ids": list(result.evidence_ids),
        "governance_note": result.governance_note,
    }


def pce_summary(session: Session, project: Project, data_mode: DataMode) -> dict[str, Any] | None:
    try:
        mode = pce_mode(data_mode, project)
        plan = get_project_plan(session, project, mode)
        result = verify_project(session, project, mode, persist=False)
    except Exception:
        return None
    return {
        "plan_recorded": bool(plan.recorded),
        "claim_recorded": bool(result.claim_findings) and "No claim has been recorded" not in " ".join(result.claim_findings),
        "overall_result": result.overall_result.value if hasattr(result.overall_result, "value") else str(result.overall_result),
        "missing_information": list(result.missing_information),
        "mismatch_count": len(result.mismatches),
        "evidence_confidence": result.evidence_confidence,
        "explanation": result.explanation,
        "evidence_ids": list(result.evidence_ids),
        "data_mode": mode.value,
        "completion_date": None,
        "expenditure": None,
        "note": "Completion dates and expenditure are not invented. Absent values stay unavailable.",
    }


def milestone_summary(session: Session, project: Project, data_mode: DataMode) -> dict[str, Any] | None:
    try:
        mode = milestone_mode(data_mode, project)
        bundle = list_project_milestones(session, project, mode)
    except Exception:
        return None
    items = []
    last_officer = None
    for record in bundle.items:
        payload = record.as_dict() if hasattr(record, "as_dict") else {}
        action = payload.get("officer_action")
        if action:
            last_officer = {
                "milestone_id": payload.get("milestone_id"),
                "milestone_name": payload.get("milestone_name"),
                "officer_action": action,
                "officer_reason": payload.get("officer_reason"),
                "officer_acted_at": payload.get("officer_acted_at"),
            }
        items.append(
            {
                "milestone_id": payload.get("milestone_id"),
                "milestone_name": payload.get("milestone_name"),
                "status": payload.get("status"),
                "recommendation": payload.get("recommendation"),
                "officer_action": action,
            }
        )
    return {
        "count": len(items),
        "current_milestone_id": bundle.current_milestone_id,
        "current_milestone_name": bundle.current_milestone_name,
        "current_recommendation": bundle.current_recommendation,
        "items": items,
        "last_officer_action": last_officer,
        "automatic_sanction": False,
        "pfms_integrated": False,
        "funds_released": False,
        "data_mode": bundle.data_mode,
        "hybrid_notice": bundle.hybrid_notice,
    }


def _risk_from_stored(row: FusionScoreV2) -> dict[str, Any]:
    import json

    payload: dict[str, Any] = {}
    if row.payload_json:
        try:
            loaded = json.loads(row.payload_json)
            if isinstance(loaded, dict):
                payload = loaded
        except json.JSONDecodeError:
            payload = {}
    return {
        "appropriate": True,
        "stored": True,
        "investigation_priority": row.investigation_priority,
        "evidence_confidence": row.evidence_confidence,
        "risk_class": row.risk_class,
        "recommended_action": row.recommended_action,
        "explanation_type": row.explanation_type,
        "explanation": payload.get("explanation"),
        "contributing_evidence_groups": [
            item.get("display_name") or item.get("group_id")
            for item in (payload.get("contributing_evidence_groups") or [])
            if isinstance(item, dict)
        ],
        "conflicting_evidence": payload.get("conflicting_evidence") or [],
        "unavailable_evidence": [
            item.get("display_name") or item.get("group_id")
            for item in (payload.get("unavailable_evidence") or [])
            if isinstance(item, dict)
        ],
        "data_mode": row.data_mode,
        "engine_version": row.engine_version,
        "synthetic_disclosure": payload.get("synthetic_disclosure"),
        "formula_unchanged": True,
    }


def _risk_from_result(result: FusionV2Result, *, stored: bool) -> dict[str, Any]:
    return {
        "appropriate": True,
        "stored": stored,
        "investigation_priority": result.investigation_priority,
        "evidence_confidence": result.evidence_confidence,
        "risk_class": result.risk_class.value if hasattr(result.risk_class, "value") else result.risk_class,
        "recommended_action": result.recommended_action.value
        if hasattr(result.recommended_action, "value")
        else result.recommended_action,
        "explanation_type": result.explanation_type.value
        if hasattr(result.explanation_type, "value")
        else result.explanation_type,
        "explanation": result.explanation,
        "contributing_evidence_groups": [
            item.display_name for item in result.contributing_evidence_groups
        ],
        "conflicting_evidence": [item.as_payload() for item in result.conflicting_evidence],
        "unavailable_evidence": [item.display_name for item in result.unavailable_evidence],
        "data_mode": result.data_mode.value,
        "engine_version": result.engine_version,
        "synthetic_disclosure": result.synthetic_disclosure,
        "formula_unchanged": True,
    }


def risk_v2_summary(
    session: Session,
    project: Project,
    data_mode: DataMode,
    *,
    appropriate: bool,
) -> dict[str, Any]:
    if not appropriate:
        return {
            "appropriate": False,
            "stored": False,
            "reason": (
                "Need & Impact is the primary FUTURE workflow. "
                "Risk Fusion V2 is used for ONGOING and COMPLETED investigation."
            ),
            "investigation_priority": None,
            "evidence_confidence": None,
            "formula_unchanged": True,
            "engine_version": "risk-fusion-v2",
        }
    row = session.scalars(
        select(FusionScoreV2).where(
            FusionScoreV2.project_id == project.id,
            FusionScoreV2.data_mode == data_mode.value,
        )
    ).first()
    if row is not None:
        return _risk_from_stored(row)
    result = assess_project_risk_v2(session, project.id, data_mode=data_mode, persist=False)
    return _risk_from_result(result, stored=False)


def citizen_summary_payload(session: Session, project: Project, data_mode: DataMode) -> dict[str, Any] | None:
    try:
        mode = citizen_mode(data_mode, project)
        summary = project_citizen_summary(session, project, mode, persist=False)
    except Exception:
        return None
    if summary.total_submissions == 0:
        return {
            "available": False,
            "status": "NOT AVAILABLE",
            "total_submissions": 0,
            "aggregate_finding": None,
            "note": "No citizen reports are stored. One report would not establish truth.",
        }
    return {
        "available": True,
        "status": summary.sample_size_status,
        "total_submissions": summary.total_submissions,
        "verified_location_submissions": summary.verified_location_submissions,
        "aggregate_finding": summary.aggregate_finding,
        "citizen_evidence_confidence": summary.citizen_evidence_confidence,
        "evidence_ids": list(summary.evidence_ids),
        "data_mode": summary.data_mode,
        "note": "Citizen evidence is supporting only. A single report does not establish truth.",
    }


def document_status_payload(session: Session, project_id: int, items: list[EvidenceObject]) -> dict[str, Any]:
    docs = list_project_documents(session, project_id)
    available, status, ids = _disposition_status(_engine_items(items, EvidenceEngine.DOCUMENT.value))
    if not docs and not available:
        return {"available": False, "status": "NOT AVAILABLE", "count": 0}
    return {
        "available": True,
        "status": status or "RECORDED",
        "count": len(docs),
        "evidence_ids": ids,
    }


def image_status_payload(
    session: Session,
    project: Project,
    data_mode: DataMode,
    items: list[EvidenceObject],
) -> dict[str, Any]:
    try:
        summary = project_image_summary(session, project, data_mode)
    except Exception:
        summary = {}
    available, status, ids = _disposition_status(_engine_items(items, EvidenceEngine.IMAGE.value))
    submitted = int(summary.get("images_submitted") or 0)
    if submitted == 0 and not available:
        return {"available": False, "status": "NOT AVAILABLE", "images_submitted": 0}
    return {
        "available": True,
        "status": status or "RECORDED",
        "images_submitted": submitted,
        "exact_duplicates": summary.get("exact_duplicates"),
        "potential_reuse": summary.get("potential_reuse"),
        "evidence_ids": ids,
        "authenticity_capability": summary.get("authenticity_capability"),
    }


def geo_status_payload(items: list[EvidenceObject]) -> dict[str, Any]:
    available, status, ids = _disposition_status(_engine_items(items, EvidenceEngine.GEO.value))
    if not available:
        return {
            "available": False,
            "status": "NOT AVAILABLE",
            "note": "REAL project GPS is typically unavailable in the current extract.",
        }
    return {"available": True, "status": status, "evidence_ids": ids}


def satellite_status_payload(items: list[EvidenceObject]) -> dict[str, Any]:
    available, status, ids = _disposition_status(_engine_items(items, EvidenceEngine.SATELLITE.value))
    if not available:
        return {
            "available": False,
            "status": "SATELLITE_UNAVAILABLE",
            "note": "Satellite imagery is not claimed as live unless a provider actually returned it.",
        }
    return {"available": True, "status": status or "INCONCLUSIVE", "evidence_ids": ids}


def compliance_status_payload(items: list[EvidenceObject]) -> dict[str, Any] | None:
    available, status, ids = _disposition_status(_engine_items(items, EvidenceEngine.COMPLIANCE.value))
    if not available:
        return None
    return {"available": True, "status": status, "evidence_ids": ids}


def graph_status_payload(items: list[EvidenceObject]) -> dict[str, Any] | None:
    available, status, ids = _disposition_status(_engine_items(items, EvidenceEngine.GRAPH.value))
    if not available:
        return None
    return {"available": True, "status": status, "evidence_ids": ids}
