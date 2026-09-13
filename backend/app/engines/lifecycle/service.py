"""End-to-End Project Lifecycle Orchestration V1.

Connects frozen engines into FUTURE / ONGOING / COMPLETED workflows.
Does not rewrite intelligence engines or Risk Fusion V2 formula.
Does not create duplicate Evidence Objects.
Does not sanction, pay, or conclude fraud.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import DataMode, LifecycleStage
from app.engines.fusion.service import select_evidence_for_mode
from app.engines.fusion_v2.constants import ENGINE_VERSION as FUSION_V2_VERSION
from app.engines.fusion_v2.constants import GROUP_WEIGHTS
from app.engines.fusion_v2.service import select_evidence_for_mode_v2
from app.engines.lifecycle.constants import (
    ENGINE_VERSION,
    FROZEN_FUSION_V2_VERSION,
    FROZEN_FUSION_V2_WEIGHTS,
    GOVERNANCE_NOTE,
    NO_FRAUD_NOTE,
    NO_PAYMENT_NOTE,
    NO_SANCTION_NOTE,
    PLANNING,
    PLANNING_ACTION_TO_STATE,
    PLANNING_ACTIONS,
    PLANNING_DECISION_AUDIT,
    PLANNING_ENTITY_TYPE,
    WEIGHT_NOTE,
)
from app.engines.lifecycle.errors import LifecycleError
from app.engines.lifecycle.state import (
    checkpoint_actions_for,
    completed_evidence_insufficient,
    default_planning_state,
    derive_current_stage,
    risk_fusion_appropriate,
    workflow_recommendation,
)
from app.engines.lifecycle.summaries import (
    citizen_summary_payload,
    compliance_status_payload,
    document_status_payload,
    evidence_module_summary,
    geo_status_payload,
    graph_status_payload,
    image_status_payload,
    milestone_summary,
    need_summary,
    pce_summary,
    risk_v2_summary,
    satellite_status_payload,
)
from app.engines.lifecycle.timeline import build_timeline, split_completed_pending
from app.engines.lifecycle.types import LifecycleFacts, LifecycleResult, parse_lifecycle_state
from app.engines.pce.repository import list_claims
from app.errors import AppError
from app.evidence.repository import list_project_evidence
from app.identity.scheme_id import scheme_id_for_project
from app.models.audit import AuditEvent
from app.models.fusion import FusionScore
from app.models.fusion_v2 import FusionScoreV2
from app.models.lifecycle import LifecycleDecision, LifecycleWorkflow
from app.models.project import Project
from app.review.service import list_officer_decisions

_FORBIDDEN = ("fraud confirmed", "automatic sanction", "automatic payment", "pfms payment")


def parse_lifecycle_data_mode(value: str | DataMode | None, project: Project) -> DataMode:
    if project.is_synthetic:
        return DataMode.SYNTHETIC
    if isinstance(value, DataMode):
        return value
    text = str(value or "").strip().upper().replace("-", "_")
    if text in {"HYBRID", "HYBRID_TEST", "HYBRIDTEST", "HYBRID_DEMO"}:
        return DataMode.HYBRID
    if text in {"SYNTHETIC"}:
        return DataMode.SYNTHETIC
    return DataMode.REAL


def assert_fusion_v2_frozen() -> None:
    if FUSION_V2_VERSION != FROZEN_FUSION_V2_VERSION:
        raise LifecycleError("Risk Fusion V2 version changed; lifecycle must not rewrite it.")
    for key, weight in FROZEN_FUSION_V2_WEIGHTS.items():
        if GROUP_WEIGHTS.get(key) != weight:
            raise LifecycleError("Risk Fusion V2 weights changed; lifecycle must not rewrite them.")


def _score_snapshots(session: Session, project_id: int) -> dict[str, Any]:
    v1 = session.scalars(select(FusionScore).where(FusionScore.project_id == project_id)).first()
    v2 = list(session.scalars(select(FusionScoreV2).where(FusionScoreV2.project_id == project_id)).all())
    return {
        "v1": None
        if v1 is None
        else (v1.investigation_priority, v1.evidence_confidence, v1.recommended_action),
        "v2": [
            (row.id, row.data_mode, row.investigation_priority, row.evidence_confidence)
            for row in v2
        ],
    }


def _reject_forbidden(*values: object) -> None:
    blob = "\n".join("" if item is None else str(item) for item in values).casefold()
    if "fraud" in blob and "not" not in blob:
        raise LifecycleError(
            "Lifecycle orchestration must not record a legal fraud conclusion.",
            code="fraud_language_forbidden",
        )
    for term in _FORBIDDEN:
        if term in blob:
            raise LifecycleError(
                "Lifecycle orchestration must not sanction, pay, or conclude fraud.",
                code="forbidden_output_term",
            )


def _latest_workflow(session: Session, project_id: int) -> LifecycleWorkflow | None:
    return session.scalars(
        select(LifecycleWorkflow).where(LifecycleWorkflow.project_id == project_id)
    ).first()


def list_planning_decisions(session: Session, project_id: int) -> list[LifecycleDecision]:
    return list(
        session.scalars(
            select(LifecycleDecision)
            .where(LifecycleDecision.project_id == project_id)
            .order_by(LifecycleDecision.created_at.desc(), LifecycleDecision.id.desc())
        ).all()
    )


def record_planning_decision(
    session: Session,
    project: Project,
    *,
    action: str,
    reason: str | None,
    actor_role: str | None,
    data_mode: DataMode,
) -> tuple[LifecycleDecision, dict[str, Any]]:
    lifecycle_state = parse_lifecycle_state(project.lifecycle_stage)
    if lifecycle_state != LifecycleStage.FUTURE.value:
        raise LifecycleError(
            "Planning PRIORITIZE / DEFER / NEED MORE INFORMATION apply to FUTURE / proposed works only.",
            code="planning_not_applicable",
        )
    value = str(action or "").strip().upper().replace(" ", "_")
    if value not in PLANNING_ACTIONS:
        raise LifecycleError(
            "Unsupported planning action. Use PRIORITIZE, DEFER, NEED_MORE_INFORMATION, or RETURN_TO_PLANNING.",
            code="invalid_planning_action",
        )
    _reject_forbidden(value, reason)
    resulting = PLANNING_ACTION_TO_STATE[value]
    before = _score_snapshots(session, project.id)
    payload = {
        "project_id": project.id,
        "internal_project_id": project.internal_project_id,
        "lifecycle_state": lifecycle_state,
        "source_status": project.status,
        "action": value,
        "resulting_state": resulting,
        "automatic_sanction": False,
        "automatic_payment": False,
        "scores_unchanged": True,
        "note": "SARVSAKSHI planning state only. Not a sanction and not an official MPLADS status.",
    }
    decision = LifecycleDecision(
        project_id=project.id,
        action=value,
        resulting_state=resulting,
        reason=reason,
        actor_role=(actor_role or "officer").strip() or "officer",
        data_mode=data_mode.value,
        payload_json=json.dumps(payload, sort_keys=True),
    )
    session.add(decision)
    session.flush()
    row = _latest_workflow(session, project.id)
    if row is None:
        row = LifecycleWorkflow(project_id=project.id)
        session.add(row)
    row.planning_state = resulting
    row.last_action = value
    row.last_reason = reason
    row.actor_role = decision.actor_role
    row.data_mode = data_mode.value
    row.payload_json = json.dumps(payload, sort_keys=True)
    session.add(
        AuditEvent(
            actor_role=decision.actor_role,
            action=PLANNING_DECISION_AUDIT,
            entity_type=PLANNING_ENTITY_TYPE,
            entity_id=str(decision.id),
            payload=json.dumps({**payload, "decision_id": decision.id}, sort_keys=True),
        )
    )
    session.flush()
    after = _score_snapshots(session, project.id)
    if after != before:
        raise AppError(
            "Officer planning decision must not change stored intelligence scores.",
            code="score_mutation_forbidden",
            status_code=500,
        )
    project_stage = parse_lifecycle_state(project.lifecycle_stage)
    if project_stage != lifecycle_state:
        raise AppError(
            "Planning decision must not change source-derived lifecycle_stage.",
            code="lifecycle_mutation_forbidden",
            status_code=500,
        )
    return decision, payload


def _select_evidence(session: Session, project: Project, data_mode: DataMode):
    stored = list_project_evidence(session, project.id)
    if data_mode == DataMode.REAL:
        return [item for item in stored if item.data_mode == DataMode.REAL]
    try:
        return select_evidence_for_mode_v2(stored, data_mode)
    except Exception:
        return select_evidence_for_mode(stored, data_mode)


def _has_investigation_evidence(items) -> bool:
    engines = {str(item.engine_name) for item in items}
    return bool(engines & {"cost", "time", "overlap", "compliance", "graph", "pce", "image", "geo"})


def _explanation(
    result_state: str,
    current: str,
    facts: LifecycleFacts,
    data_mode: DataMode,
    is_synthetic: bool,
    synthetic_label: str | None,
    risk: dict[str, Any] | None,
) -> str:
    parts = [
        f"{GOVERNANCE_NOTE}",
        f"SARVSAKSHI workflow state is {result_state}. Current stage is {current}.",
        NO_SANCTION_NOTE,
        NO_PAYMENT_NOTE,
        NO_FRAUD_NOTE,
        WEIGHT_NOTE,
    ]
    if data_mode == DataMode.HYBRID:
        parts.append("HYBRID: real project fields plus clearly labelled synthetic enrichment.")
    elif data_mode == DataMode.SYNTHETIC or is_synthetic:
        parts.append(
            synthetic_label
            or "SYNTHETIC: test-only. This is not a government finding."
        )
    else:
        parts.append("REAL: observed MPLADS extract fields only.")
    if risk and risk.get("synthetic_disclosure"):
        parts.append(str(risk["synthetic_disclosure"]))
    if facts.completed_insufficient:
        parts.append("Final evidence is insufficient. Result is INCONCLUSIVE.")
    return " ".join(parts)


def get_project_lifecycle(
    session: Session,
    project: Project,
    data_mode: DataMode,
) -> LifecycleResult:
    assert_fusion_v2_frozen()
    lifecycle_state = parse_lifecycle_state(project.lifecycle_stage)
    stored_workflow = _latest_workflow(session, project.id)
    planning_state = default_planning_state(
        lifecycle_state,
        stored_workflow.planning_state if stored_workflow else None,
    )
    evidence_items = _select_evidence(session, project, data_mode)
    evidence = evidence_module_summary(evidence_items)
    need = need_summary(session, project, data_mode)
    pce = pce_summary(session, project, data_mode)
    claims = list_claims(session, project.id)
    has_claim = any(
        not (data_mode == DataMode.REAL and row.data_mode and row.data_mode != DataMode.REAL.value)
        for row in claims
    )
    if pce is not None:
        pce["claim_recorded"] = has_claim
    milestones = milestone_summary(session, project, data_mode)
    citizen = citizen_summary_payload(session, project, data_mode)
    documents = document_status_payload(session, project.id, evidence_items)
    images = image_status_payload(session, project, data_mode, evidence_items)
    geo = geo_status_payload(evidence_items)
    satellite = satellite_status_payload(evidence_items)
    compliance = compliance_status_payload(evidence_items)
    graph = graph_status_payload(evidence_items)

    has_investigation = _has_investigation_evidence(evidence_items)
    risk_ok = risk_fusion_appropriate(lifecycle_state, has_investigation_evidence=has_investigation)
    risk = risk_v2_summary(session, project, data_mode, appropriate=risk_ok)

    investigation_decisions = list_officer_decisions(session, project.id)
    last_inv = investigation_decisions[0][0].decision_type if investigation_decisions else None

    latest_ms_status = None
    latest_ms_action = None
    latest_ms_rec = None
    ms_count = 0
    if milestones:
        ms_count = int(milestones.get("count") or 0)
        latest_ms_rec = milestones.get("current_recommendation")
        items = milestones.get("items") or []
        if items:
            latest_ms_status = items[-1].get("status")
            latest_ms_action = items[-1].get("officer_action")
        last_off = milestones.get("last_officer_action") or {}
        if last_off.get("officer_action"):
            latest_ms_action = last_off.get("officer_action")

    risk_insufficient = False
    risk_expl = None
    if risk_ok:
        risk_expl = risk.get("explanation_type")
        risk_insufficient = risk_expl in {"INSUFFICIENT_EVIDENCE", "INCONCLUSIVE"} or (
            risk.get("investigation_priority") in {0, None} and not risk.get("contributing_evidence_groups")
        )

    facts = LifecycleFacts(
        lifecycle_state=lifecycle_state,
        source_status=project.status,
        planning_state=planning_state or PLANNING,
        data_mode=data_mode,
        has_need=bool(need and need.get("priority_class")),
        need_priority_class=None if not need else need.get("priority_class"),
        need_inconclusive=bool(need and need.get("priority_class") == "INCONCLUSIVE"),
        has_plan=bool(pce and pce.get("plan_recorded")),
        has_claim=has_claim,
        has_pce_evidence=bool(pce and (pce.get("evidence_ids") or pce.get("overall_result") not in {None, "INCONCLUSIVE"})),
        pce_result=None if not pce else pce.get("overall_result"),
        milestone_count=ms_count,
        latest_milestone_status=latest_ms_status,
        latest_milestone_officer_action=latest_ms_action,
        latest_milestone_recommendation=latest_ms_rec,
        has_officer_investigation_decision=bool(investigation_decisions),
        last_investigation_decision=last_inv,
        risk_appropriate=risk_ok,
        risk_insufficient=risk_insufficient,
        risk_explanation_type=risk_expl,
        has_documents=bool(documents.get("available")),
        has_images=bool(images.get("available")),
        has_geo=bool(geo.get("available")),
        has_satellite=bool(satellite.get("available")),
        satellite_unavailable=not bool(satellite.get("available")),
        has_citizen=bool(citizen and citizen.get("available")),
        has_graph=bool(graph and graph.get("available")),
        has_compliance=bool(compliance and compliance.get("available")),
    )
    facts.completed_insufficient = completed_evidence_insufficient(facts)
    current = derive_current_stage(facts)
    timeline = build_timeline(facts, current)
    completed_stages, pending_stages = split_completed_pending(timeline)
    recommendation, rationale = workflow_recommendation(facts, current)
    if lifecycle_state == LifecycleStage.FUTURE.value and need:
        rationale = need.get("recommendation_rationale") or rationale
        if need.get("priority_class") and recommendation is None:
            recommendation = str(need["priority_class"]).replace("_", " ")

    officer_rows: list[dict[str, Any]] = []
    for decision in list_planning_decisions(session, project.id):
        officer_rows.append(
            {
                "kind": "planning",
                "action": decision.action,
                "resulting_state": decision.resulting_state,
                "reason": decision.reason,
                "actor_role": decision.actor_role,
                "created_at": decision.created_at.isoformat() if decision.created_at else None,
                "scores_unchanged": True,
            }
        )
    for row, payload in investigation_decisions:
        officer_rows.append(
            {
                "kind": "investigation",
                "action": row.decision_type,
                "reason": row.reason,
                "actor_role": row.actor_role,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "scores_unchanged": bool(payload.get("scores_unchanged", True)),
                "investigation_priority_snapshot": payload.get("investigation_priority_snapshot"),
                "evidence_confidence_snapshot": payload.get("evidence_confidence_snapshot"),
            }
        )
    if latest_ms_action:
        officer_rows.append(
            {
                "kind": "milestone",
                "action": latest_ms_action,
                "milestone_status": latest_ms_status,
                "recommendation": latest_ms_rec,
                "scores_unchanged": True,
            }
        )

    unavailable: list[str] = []
    if need:
        unavailable.extend(str(item) for item in (need.get("unavailable_inputs") or []))
    if pce:
        unavailable.extend(str(item) for item in (pce.get("missing_information") or []))
    if not geo.get("available"):
        unavailable.append("verified project GPS")
    if satellite.get("status") == "SATELLITE_UNAVAILABLE":
        unavailable.append("satellite imagery")
    if facts.completed_insufficient:
        unavailable.append("sufficient final investigation evidence")

    status_summary: dict[str, Any] = {
        "lifecycle_state": lifecycle_state,
        "source_status": project.status,
        "current_stage": current,
        "data_mode": data_mode.value,
        "planning_state": planning_state if lifecycle_state == LifecycleStage.FUTURE.value else None,
    }
    if risk_ok and risk.get("investigation_priority") is not None:
        status_summary["investigation_priority"] = risk.get("investigation_priority")
        status_summary["evidence_confidence"] = risk.get("evidence_confidence")
    if need and lifecycle_state == LifecycleStage.FUTURE.value:
        status_summary["need_score"] = need.get("need_score")
        status_summary["impact_score"] = need.get("impact_score")
        status_summary["priority"] = need.get("priority_class")
        status_summary["need_evidence_confidence"] = need.get("evidence_confidence")
    if milestones and ms_count:
        status_summary["milestone_status"] = latest_ms_status or milestones.get("current_recommendation")
    if citizen and citizen.get("available"):
        status_summary["citizen_evidence"] = citizen.get("status")
    if geo.get("available"):
        status_summary["geospatial_status"] = geo.get("status")
    if satellite:
        status_summary["satellite_status"] = satellite.get("status")
    if documents.get("available"):
        status_summary["document_status"] = documents.get("status")
    if images.get("available"):
        status_summary["image_status"] = images.get("status")
    if compliance:
        status_summary["compliance_status"] = compliance.get("status")
    if graph:
        status_summary["relationship_status"] = graph.get("status")

    final_case = None
    if lifecycle_state == LifecycleStage.COMPLETED.value:
        final_case = {
            "result": "INCONCLUSIVE" if facts.completed_insufficient else "FINAL_INVESTIGATION",
            "investigation_priority": None if not risk_ok else risk.get("investigation_priority"),
            "evidence_confidence": None if not risk_ok else risk.get("evidence_confidence"),
            "pce_result": None if not pce else pce.get("overall_result"),
            "officer_decision": last_inv,
            "completion_date": None,
            "expenditure": None,
            "note": (
                "INCONCLUSIVE because stored evidence is insufficient."
                if facts.completed_insufficient
                else "Final case summary from stored evidence, Risk Fusion V2, and officer decisions. "
                "Completion date and expenditure were not invented."
            ),
            "automatic_sanction": False,
            "automatic_payment": False,
            "fraud_conclusion": False,
        }

    return LifecycleResult(
        project_id=project.id,
        internal_project_id=project.internal_project_id,
        scheme_id=scheme_id_for_project(session, project),
        work_description=project.work_description,
        constituency=project.constituency,
        category=project.category,
        requested_amount=project.allocation_amount,
        data_mode=data_mode,
        lifecycle_state=lifecycle_state,
        source_status=project.status,
        current_stage=current,
        planning_state=planning_state if lifecycle_state == LifecycleStage.FUTURE.value else None,
        completed_stages=completed_stages,
        pending_stages=pending_stages,
        timeline=timeline,
        evidence_summary=evidence,
        risk_summary=risk,
        milestone_summary=milestones if ms_count else None,
        need_impact_summary=need if lifecycle_state in {LifecycleStage.FUTURE.value, LifecycleStage.UNKNOWN.value} or need else need,
        pce_summary=pce,
        citizen_summary=citizen if citizen and (citizen.get("available") or lifecycle_state != LifecycleStage.FUTURE.value) else (citizen if citizen and citizen.get("available") else None),
        geospatial_status=geo if geo.get("available") else (geo if lifecycle_state != LifecycleStage.FUTURE.value else None),
        satellite_status=satellite,
        document_status=documents if documents.get("available") else None,
        image_status=images if images.get("available") else None,
        compliance_status=compliance,
        relationship_status=graph,
        project_status_summary=status_summary,
        officer_decisions=officer_rows,
        checkpoint_actions=checkpoint_actions_for(lifecycle_state),
        final_case_summary=final_case,
        recommendation=recommendation,
        recommendation_rationale=rationale,
        unavailable_inputs=list(dict.fromkeys(unavailable)),
        is_synthetic=bool(project.is_synthetic),
        synthetic_label=project.synthetic_label,
        explanation=_explanation(
            lifecycle_state,
            current,
            facts,
            data_mode,
            bool(project.is_synthetic),
            project.synthetic_label,
            risk if risk_ok else None,
        ),
    )
