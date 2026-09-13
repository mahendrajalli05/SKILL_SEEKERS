from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain.schemas.review import (
    OfficerDecisionCreate,
    OfficerDecisionListResponse,
    OfficerDecisionRead,
)
from app.errors import AppError
from app.models.project import Project
from app.review.service import list_officer_decisions, record_officer_decision

router = APIRouter()


def _to_read(row, payload: dict) -> OfficerDecisionRead:
    return OfficerDecisionRead(
        id=row.id,
        project_id=row.project_id,
        decision_type=row.decision_type,
        reason=row.reason,
        actor_role=row.actor_role,
        created_at=row.created_at,
        investigation_priority_snapshot=payload.get("investigation_priority_snapshot"),
        evidence_confidence_snapshot=payload.get("evidence_confidence_snapshot"),
        recommended_action_snapshot=payload.get("recommended_action_snapshot"),
        scores_unchanged=bool(payload.get("scores_unchanged", True)),
    )


@router.get(
    "/projects/{project_id}/decisions",
    response_model=OfficerDecisionListResponse,
)
def get_project_decisions(
    project_id: int,
    db: Session = Depends(get_db),
) -> OfficerDecisionListResponse:
    row = db.get(Project, project_id)
    if row is None:
        raise AppError("Project not found.", code="not_found", status_code=404)
    items = [_to_read(decision, payload) for decision, payload in list_officer_decisions(db, project_id)]
    return OfficerDecisionListResponse(project_id=project_id, items=items)


@router.post(
    "/projects/{project_id}/decisions",
    response_model=OfficerDecisionRead,
)
def create_project_decision(
    project_id: int,
    body: OfficerDecisionCreate,
    db: Session = Depends(get_db),
) -> OfficerDecisionRead:
    row = db.get(Project, project_id)
    if row is None:
        raise AppError("Project not found.", code="not_found", status_code=404)
    decision, payload = record_officer_decision(
        db,
        row,
        decision_type=body.decision_type,
        reason=body.reason,
        actor_role=body.actor_role,
    )
    db.commit()
    db.refresh(decision)
    return _to_read(decision, payload)
