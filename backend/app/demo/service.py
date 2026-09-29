"""Assemble Demo Cases V1 from existing projects and services.

HYBRID assembly attaches labelled Demo Evidence Fixtures V1 through existing
APIs when they are missing. Does not recalculate Cost, Time, Overlap,
Compliance, or Risk Fusion V2 formulas.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.demo.catalog import catalog_entry, list_catalog, normalize_case_id
from app.demo.constants import (
    DEMO_NOTICE,
    FIXTURE_LAYER,
    FIXTURE_NOTICE,
    GOVERNANCE_NOTE,
    HYBRID_NOTICE,
    JOURNEY_STEPS,
    LAYER_VERSION,
    NO_FRAUD_NOTE,
    NO_SANCTION_NOTE,
    assert_fusion_v2_unchanged,
)
from app.demo.errors import DemoCaseError
from app.demo.preassembled import has_preassembled_case, load_preassembled_case
from app.domain.enums import DataMode
from app.engines.fusion_v2.service import assess_project_risk_v2, result_payload
from app.engines.lifecycle.service import get_project_lifecycle, parse_lifecycle_data_mode
from app.evidence.repository import list_project_evidence
from app.identity.scheme_id import scheme_id_for_project
from app.models.project import Project
from app.review.service import list_officer_decisions
from app.search.enrichment_display import enrichment_for
from app.search.hybrid import has_hybrid_enrichment


def parse_demo_data_mode(value: str | DataMode | None, project: Project) -> DataMode:
    return parse_lifecycle_data_mode(value, project)


def _reject_forbidden(*values: object) -> None:
    blob = "\n".join("" if item is None else str(item) for item in values).casefold()
    if "fraud confirmed" in blob or "this is fraud" in blob:
        raise DemoCaseError(
            "Demo Cases must not record a legal fraud conclusion.",
            code="fraud_language_forbidden",
        )


def _lookup_project(session: Session, internal_project_id: str) -> Project | None:
    return session.scalars(
        select(Project).where(Project.internal_project_id == internal_project_id)
    ).first()


def _evidence_payload(items) -> list[dict[str, Any]]:
    rows = []
    for item in items:
        rows.append(
            {
                "evidence_id": item.evidence_id,
                "engine_name": item.engine_name.value if hasattr(item.engine_name, "value") else str(item.engine_name),
                "signal_type": item.signal_type.value if hasattr(item.signal_type, "value") else str(item.signal_type),
                "finding": item.finding,
                "disposition": str(item.disposition) if item.disposition else None,
                "score": item.score,
                "confidence": item.confidence,
                "data_mode": item.data_mode.value if hasattr(item.data_mode, "value") else str(item.data_mode),
                "explanation": item.explanation,
            }
        )
    return rows


def _main_signals(
    *,
    case_id: str,
    risk: dict[str, Any] | None,
    lifecycle: dict[str, Any],
    evidence_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    groups = [] if not risk else (risk.get("contributing_evidence_groups") or [])
    for group in groups:
        if not isinstance(group, dict):
            continue
        signals.append(
            {
                "group": group.get("group_id") or group.get("display_name") or group.get("signal"),
                "status": group.get("state"),
                "mapped_score": group.get("raw_evidence_score") or group.get("confidence_adjusted_score"),
                "evidence_ids": group.get("evidence_ids") or [],
                "source": "risk-fusion-v2",
            }
        )
    if not signals:
        flagged = [item for item in evidence_items if str(item.get("disposition")) == "WHY_FLAGGED"]
        for item in flagged[:8]:
            signals.append(
                {
                    "group": item.get("engine_name"),
                    "status": item.get("disposition"),
                    "mapped_score": item.get("score"),
                    "evidence_ids": [item.get("evidence_id")] if item.get("evidence_id") else [],
                    "source": "evidence-object",
                }
            )
    if case_id == "CLEAN" and not signals:
        signals.append(
            {
                "group": "why_not_flagged",
                "status": "WHY_NOT_FLAGGED",
                "mapped_score": None if not risk else risk.get("investigation_priority"),
                "evidence_ids": [item.get("evidence_id") for item in evidence_items if item.get("evidence_id")],
                "source": "risk-fusion-v2",
            }
        )
    pce = lifecycle.get("pce_summary") or {}
    if pce:
        signals.append(
            {
                "group": "pce",
                "status": pce.get("overall_result"),
                "mapped_score": None,
                "evidence_ids": pce.get("evidence_ids") or [],
                "source": "plan-claim-evidence-v1",
            }
        )
    return signals


def _missing(lifecycle: dict[str, Any], risk: dict[str, Any] | None) -> list[str]:
    missing: list[str] = []
    for item in lifecycle.get("unavailable_inputs") or []:
        missing.append(str(item))
    pce = lifecycle.get("pce_summary") or {}
    for item in pce.get("missing_information") or []:
        text = str(item)
        if text not in missing:
            missing.append(text)
    if risk:
        for group in risk.get("unavailable_evidence") or []:
            if isinstance(group, dict):
                label = group.get("group_id") or group.get("display_name") or group.get("signal")
                if label:
                    missing.append(f"{label} unavailable")
    return missing


def _recommendation(lifecycle: dict[str, Any], risk: dict[str, Any] | None) -> str | None:
    if lifecycle.get("recommendation"):
        return str(lifecycle["recommendation"])
    if risk and risk.get("recommended_action"):
        return str(risk["recommended_action"])
    return None


def _journey(project_id: int, case_id: str, mode: str) -> list[dict[str, Any]]:
    query = f"mode={'hybrid' if mode != 'REAL' else 'real'}&demo={case_id.lower()}"
    passport = f"/projects/{project_id}?{query}"
    investigate = f"/projects/{project_id}/investigate?{query}"
    graph = f"/projects/{project_id}/graph?{query}"
    demo = f"/demo/{case_id.lower()}"
    hrefs = {
        "PROJECT": f"{demo}#project",
        "PASSPORT": passport,
        "LIFECYCLE": f"{investigate}#lifecycle",
        "PLAN": f"{demo}#plan",
        "CLAIM": f"{demo}#claim",
        "EVIDENCE": f"{investigate}#evidence",
        "RISK": f"{investigate}#risk",
        "COPILOT": f"{investigate}#copilot",
        "DECISION": f"{investigate}#officer-decision",
        "SUMMARY": f"{demo}#summary",
    }
    return [{"step": step, "href": hrefs[step]} for step in JOURNEY_STEPS]


def _plan_claim_from_lifecycle(
    lifecycle: dict[str, Any],
    enrichment: dict[str, Any] | None,
    recorded_plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    pce = lifecycle.get("pce_summary") or {}
    plan = {
        "plan_recorded": pce.get("plan_recorded"),
        "pce_result": pce.get("overall_result"),
        "evidence_ids": pce.get("evidence_ids") or [],
        "completion_date": None,
        "expenditure": None,
        "note": pce.get("note"),
        "labels": ["DEMO", "SYNTHETIC", "CONTROLLED PROTOTYPE"],
        "official_mplads_record": False,
    }
    if recorded_plan:
        plan.update(recorded_plan)
    if enrichment:
        plan["synthetic_enrichment"] = {
            "label": "SYNTHETIC",
            "disclaimer": enrichment.get("disclaimer"),
            "planned_start_date": enrichment.get("planned_start_date"),
            "planned_completion_date": enrichment.get("planned_completion_date"),
            "actual_completion_date": enrichment.get("actual_completion_date"),
            "expenditure": enrichment.get("expenditure"),
            "physical_progress_percent": enrichment.get("physical_progress_percent"),
            "gps_latitude": enrichment.get("gps_latitude"),
            "gps_longitude": enrichment.get("gps_longitude"),
            "milestones": enrichment.get("milestones"),
        }
    return plan


def assemble_case(
    session: Session,
    case_id: str,
    *,
    data_mode: DataMode | str | None = None,
) -> dict[str, Any]:
    assert_fusion_v2_unchanged()
    entry = catalog_entry(case_id)
    key = entry["case_id"]
    # When requesting one of the fixed prototype demo cases (CLEAN, GHOST, OVERBILL, STUCK),
    # return the cached preassembled fixture directly with ZERO database queries.
    if has_preassembled_case(key):
        payload = load_preassembled_case(key)
        mode = str(data_mode or payload.get("data_mode") or "HYBRID").upper()
        if mode == "REAL":
            payload["data_mode"] = "REAL"
            payload["data_reliability"] = "REAL"
            real_items = [
                item for item in payload.get("available_evidence", {}).get("items", [])
                if item.get("data_mode") == "REAL"
            ]
            payload["available_evidence"] = {
                "items": real_items,
                "count": len(real_items),
                "evidence_ids": [item["evidence_id"] for item in real_items if item.get("evidence_id")],
            }
        _reject_forbidden(
            payload.get("short_description"),
            payload.get("recommended_action"),
            payload.get("risk_fusion_v2", {}).get("explanation"),
        )
        return payload

    project = _lookup_project(session, entry["internal_project_id"])
    if project is None:
        raise DemoCaseError(
            f"Controlled demo project for {entry['display_name']} is not loaded in this database.",
            code="not_found",
            status_code=404,
        )
    mode = parse_demo_data_mode(data_mode or DataMode.HYBRID, project)

    # Fallback assembly for any non-preassembled case
    payload = load_preassembled_case(key)

    # 1. Bind live project identity
    payload["project_id"] = project.id
    payload["internal_project_id"] = project.internal_project_id
    payload["work_description"] = project.work_description
    payload["constituency"] = project.constituency
    payload["category"] = project.category
    payload["state"] = project.state
    payload["source_status"] = project.status
    payload["allocation_amount"] = project.allocation_amount
    payload["data_mode"] = mode.value
    payload["is_synthetic"] = bool(project.is_synthetic)
    payload["synthetic_label"] = project.synthetic_label

    scheme_id = scheme_id_for_project(session, project)
    payload["scheme_id"] = scheme_id

    # 2. Dynamic URLs referencing project.id
    payload["journey"] = _journey(project.id, key, mode.value)
    payload["investigation_workspace"]["href"] = (
        f"/projects/{project.id}/investigate?mode={'hybrid' if mode != DataMode.REAL else 'real'}&demo={key.lower()}"
    )
    payload["copilot"]["href"] = (
        f"/projects/{project.id}/investigate?mode={'hybrid' if mode != DataMode.REAL else 'real'}&demo={key.lower()}#copilot"
    )

    # 3. Dynamic officer decisions from current session
    decisions = list_officer_decisions(session, project.id)
    if decisions:
        latest_row, latest_payload = decisions[0]
        decision_items = [
            {
                "kind": "investigation",
                "decision_type": row.decision_type,
                "reason": row.reason,
                "actor_role": row.actor_role,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "scores_unchanged": bool(d_payload.get("scores_unchanged", True)),
            }
            for row, d_payload in decisions
        ]
        payload["officer_decision"] = latest_row.decision_type
        payload["officer_decisions"] = decision_items
    else:
        payload["officer_decision"] = None
        payload["officer_decisions"] = []

    # 4. Sync evidence and risk scores when active database evidence exists
    evidence = list_project_evidence(session, project.id)
    if evidence:
        if mode == DataMode.REAL:
            evidence = [item for item in evidence if item.data_mode == DataMode.REAL]
        evidence_items = _evidence_payload(evidence)
        payload["available_evidence"] = {
            "items": evidence_items,
            "count": len(evidence_items),
            "evidence_ids": [item["evidence_id"] for item in evidence_items if item.get("evidence_id")],
        }
        risk_result = assess_project_risk_v2(session, project.id, data_mode=mode, persist=False)
        risk = result_payload(risk_result)
        payload["risk_fusion_v2"] = {
            "investigation_priority": risk.get("investigation_priority"),
            "evidence_confidence": risk.get("evidence_confidence"),
            "recommended_action": risk.get("recommended_action"),
            "explanation_type": risk.get("explanation_type"),
            "explanation": risk.get("explanation"),
            "evidence_ids": risk.get("evidence_ids") or [],
            "contributing_evidence_groups": risk.get("contributing_evidence_groups") or [],
            "unavailable_evidence": risk.get("unavailable_evidence") or [],
            "conflicting_evidence": risk.get("conflicting_evidence") or [],
            "formula_unchanged": True,
            "engine_version": risk.get("engine_version"),
            "synthetic_disclosure": risk.get("synthetic_disclosure"),
        }
    elif mode == DataMode.REAL:
        real_items = [
            item for item in payload.get("available_evidence", {}).get("items", [])
            if item.get("data_mode") == "REAL"
        ]
        payload["available_evidence"] = {
            "items": real_items,
            "count": len(real_items),
            "evidence_ids": [item["evidence_id"] for item in real_items if item.get("evidence_id")],
        }

    # 5. Sync summary block
    summary = payload.get("final_case_summary") or {}
    summary["project"] = {
        "id": project.id,
        "internal_project_id": project.internal_project_id,
        "scheme_id": scheme_id,
        "work_description": project.work_description,
        "constituency": project.constituency,
        "state": project.state,
        "status": project.status,
    }
    summary["officer_decision"] = payload["officer_decision"]
    summary["officer_decisions"] = payload["officer_decisions"]
    if evidence:
        summary["evidence"] = payload["available_evidence"]["evidence_ids"]
        summary["risk_fusion_v2"] = payload["risk_fusion_v2"]
    payload["final_case_summary"] = summary

    _reject_forbidden(
        payload.get("short_description"),
        payload.get("recommended_action"),
        payload.get("risk_fusion_v2", {}).get("explanation"),
    )
    return payload


def list_cases(session: Session, *, data_mode: DataMode | str | None = None) -> dict[str, Any]:
    assert_fusion_v2_unchanged()
    items = []
    for entry in list_catalog():
        project = _lookup_project(session, entry["internal_project_id"])
        item = {
            "case_id": entry["case_id"],
            "display_name": entry["display_name"],
            "purpose": entry["purpose"],
            "short_description": entry["short_description"],
            "expected_lifecycle": entry["expected_lifecycle"],
            "expected_direction": entry["expected_direction"],
            "internal_project_id": entry["internal_project_id"],
            "suggested_questions": list(entry["suggested_questions"]),
            "demo_notice": DEMO_NOTICE,
            "available": project is not None,
            "project_id": None if project is None else project.id,
            "scheme_id": None if project is None else scheme_id_for_project(session, project),
            "lifecycle_state": None if project is None else project.lifecycle_stage,
            "source_status": None if project is None else project.status,
            "work_description": None if project is None else project.work_description,
            "constituency": None if project is None else project.constituency,
            "href": f"/demo/{entry['case_id'].lower()}",
        }
        items.append(item)
    return {
        "items": items,
        "count": len(items),
        "demo_notice": DEMO_NOTICE,
        "hybrid_notice": HYBRID_NOTICE,
        "governance_note": GOVERNANCE_NOTE,
        "journey_steps": list(JOURNEY_STEPS),
        "engine_version": LAYER_VERSION,
        "fusion_v2_unchanged": True,
        "automatic_sanction": False,
        "automatic_payment": False,
        "fraud_conclusion": False,
        "data_mode": str(data_mode or DataMode.HYBRID.value),
        "fixture_layer": FIXTURE_LAYER,
        "fixture_notice": FIXTURE_NOTICE,
    }


def case_id_from_path(value: str) -> str:
    try:
        return normalize_case_id(value)
    except KeyError as exc:
        raise DemoCaseError(
            "Unknown demo case. Use GHOST, OVERBILL, STUCK, or CLEAN.",
            code="not_found",
            status_code=404,
        ) from exc
