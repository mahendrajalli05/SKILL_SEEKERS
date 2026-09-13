"""Human officer decisions. Never mutates intelligence scores."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import OfficerDecisionType
from app.errors import AppError
from app.models.audit import AuditEvent
from app.models.fusion import FusionScore
from app.models.fusion_v2 import FusionScoreV2
from app.models.project import Project
from app.models.review import OfficerDecision

DECISION_AUDIT_ACTION = "officer_decision"
DECISION_ENTITY_TYPE = "officer_decision"
SCORES_UNCHANGED_NOTE = (
    "Human officer decision. Underlying intelligence scores were not changed."
)


def _payload_loads(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _fusion_v2_snapshots(db: Session, project_id: int) -> list[dict[str, Any]]:
    rows = list(
        db.scalars(select(FusionScoreV2).where(FusionScoreV2.project_id == project_id)).all()
    )
    return [
        {
            "fusion_score_v2_id": row.id,
            "data_mode": row.data_mode,
            "investigation_priority": row.investigation_priority,
            "evidence_confidence": row.evidence_confidence,
            "recommended_action": row.recommended_action,
        }
        for row in rows
    ]


def _fusion_snapshot(db: Session, project_id: int) -> dict[str, Any]:
    row = db.scalars(select(FusionScore).where(FusionScore.project_id == project_id)).first()
    if row is None:
        return {
            "investigation_priority_snapshot": None,
            "evidence_confidence_snapshot": None,
            "recommended_action_snapshot": None,
            "fusion_score_id": None,
        }
    return {
        "investigation_priority_snapshot": row.investigation_priority,
        "evidence_confidence_snapshot": row.evidence_confidence,
        "recommended_action_snapshot": row.recommended_action,
        "fusion_score_id": row.id,
    }


def record_officer_decision(
    db: Session,
    project: Project,
    *,
    decision_type: OfficerDecisionType | str,
    reason: str | None,
    actor_role: str | None,
) -> tuple[OfficerDecision, dict[str, Any]]:
    value = (
        decision_type.value
        if isinstance(decision_type, OfficerDecisionType)
        else str(decision_type).strip()
    )
    allowed = {item.value for item in OfficerDecisionType}
    if value not in allowed:
        raise AppError(
            "Unsupported officer action. Use confirm_concern, dismiss, or need_more_info.",
            code="invalid_decision",
            status_code=422,
        )
    if "fraud" in value.casefold() or (reason and "fraud" in reason.casefold()):
        raise AppError(
            "Legal fraud conclusions are not officer actions in this prototype.",
            code="invalid_decision",
            status_code=422,
        )

    snapshot = _fusion_snapshot(db, project.id)
    v2_before = _fusion_v2_snapshots(db, project.id)
    fusion_before = {
        "investigation_priority": snapshot["investigation_priority_snapshot"],
        "evidence_confidence": snapshot["evidence_confidence_snapshot"],
        "recommended_action": snapshot["recommended_action_snapshot"],
    }

    decision = OfficerDecision(
        project_id=project.id,
        decision_type=value,
        reason=reason,
        actor_role=(actor_role or "officer").strip() or "officer",
    )
    db.add(decision)
    db.flush()

    payload = {
        **snapshot,
        "project_id": project.id,
        "internal_project_id": project.internal_project_id,
        "decision_id": decision.id,
        "decision_type": value,
        "v2_snapshots": v2_before,
        "scores_unchanged": True,
        "note": SCORES_UNCHANGED_NOTE,
    }
    db.add(
        AuditEvent(
            actor_role=decision.actor_role,
            action=DECISION_AUDIT_ACTION,
            entity_type=DECISION_ENTITY_TYPE,
            entity_id=str(decision.id),
            payload=json.dumps(payload, sort_keys=True),
        )
    )
    db.flush()

    fusion_after = _fusion_snapshot(db, project.id)
    v2_after = _fusion_v2_snapshots(db, project.id)
    if (
        fusion_after["investigation_priority_snapshot"] != fusion_before["investigation_priority"]
        or fusion_after["evidence_confidence_snapshot"] != fusion_before["evidence_confidence"]
        or fusion_after["recommended_action_snapshot"] != fusion_before["recommended_action"]
        or v2_after != v2_before
    ):
        raise AppError(
            "Officer decision must not change stored intelligence scores.",
            code="score_mutation_forbidden",
            status_code=500,
        )
    return decision, payload


def list_officer_decisions(db: Session, project_id: int) -> list[tuple[OfficerDecision, dict[str, Any]]]:
    decisions = list(
        db.scalars(
            select(OfficerDecision)
            .where(OfficerDecision.project_id == project_id)
            .order_by(OfficerDecision.created_at.desc(), OfficerDecision.id.desc())
        ).all()
    )
    audits = list(
        db.scalars(
            select(AuditEvent).where(
                AuditEvent.action == DECISION_AUDIT_ACTION,
                AuditEvent.entity_type == DECISION_ENTITY_TYPE,
            )
        ).all()
    )
    by_id = {item.entity_id: _payload_loads(item.payload) for item in audits}
    return [(row, by_id.get(str(row.id), {})) for row in decisions]
