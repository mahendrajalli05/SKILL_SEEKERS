from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain.enums import DataMode
from app.domain.schemas.lifecycle import (
    LifecyclePlanningDecisionCreate,
    LifecyclePlanningDecisionRead,
    ProjectLifecycleResponse,
)
from app.engines.lifecycle.constants import NO_SANCTION_NOTE
from app.engines.lifecycle.errors import LifecycleError
from app.engines.lifecycle.service import (
    get_project_lifecycle,
    parse_lifecycle_data_mode,
    record_planning_decision,
)
from app.errors import AppError
from app.models.project import Project

router = APIRouter()


def _project(db: Session, project_id: int) -> Project:
    row = db.get(Project, project_id)
    if row is None:
        raise AppError("Project not found.", code="not_found", status_code=404)
    return row


@router.get(
    "/projects/{project_id}/lifecycle",
    response_model=ProjectLifecycleResponse,
)
def get_project_lifecycle_v2(
    project_id: int,
    db: Session = Depends(get_db),
    data_mode: Literal["REAL", "HYBRID", "SYNTHETIC"] = Query(
        default="REAL",
        description=(
            "Orchestrated FUTURE / ONGOING / COMPLETED workflow. "
            "Does not recalculate frozen intelligence engines. "
            "Not a sanction or payment."
        ),
    ),
) -> ProjectLifecycleResponse:
    project = _project(db, project_id)
    mode = parse_lifecycle_data_mode(data_mode, project)
    try:
        result = get_project_lifecycle(db, project, mode)
    except LifecycleError as exc:
        raise AppError(exc.message, code=exc.code, status_code=exc.status_code) from exc
    return ProjectLifecycleResponse.from_result(result)


@router.post(
    "/projects/{project_id}/lifecycle/decision",
    response_model=LifecyclePlanningDecisionRead,
)
def post_lifecycle_planning_decision(
    project_id: int,
    body: LifecyclePlanningDecisionCreate,
    db: Session = Depends(get_db),
    data_mode: Literal["REAL", "HYBRID", "SYNTHETIC"] = Query(default="REAL"),
) -> LifecyclePlanningDecisionRead:
    """FUTURE planning decision. Does not sanction or change intelligence scores."""
    project = _project(db, project_id)
    mode = parse_lifecycle_data_mode(data_mode, project)
    try:
        decision, payload = record_planning_decision(
            db,
            project,
            action=body.action,
            reason=body.reason,
            actor_role=body.actor_role,
            data_mode=mode,
        )
    except LifecycleError as exc:
        raise AppError(exc.message, code=exc.code, status_code=exc.status_code) from exc
    db.commit()
    db.refresh(decision)
    return LifecyclePlanningDecisionRead(
        id=decision.id,
        project_id=decision.project_id,
        action=decision.action,
        resulting_state=decision.resulting_state,
        reason=decision.reason,
        actor_role=decision.actor_role,
        scores_unchanged=True,
        automatic_sanction=False,
        automatic_payment=False,
        note=str(payload.get("note") or NO_SANCTION_NOTE),
    )
