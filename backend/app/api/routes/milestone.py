from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain.schemas.milestone import (
    MilestoneCreate,
    MilestoneDecisionCreate,
    MilestoneRead,
    ProjectMilestonesRead,
)
from app.engines.milestone.service import (
    assess_milestone,
    create_milestone,
    get_milestone_record,
    list_project_milestones,
    parse_data_mode,
    record_officer_action,
)
from app.errors import AppError
from app.models.project import Project

router = APIRouter()


def _project(db: Session, project_id: int) -> Project:
    row = db.get(Project, project_id)
    if row is None:
        raise AppError("Project not found.", code="not_found", status_code=404)
    return row


@router.get("/projects/{project_id}/milestones", response_model=ProjectMilestonesRead)
def get_project_milestones(
    project_id: int,
    data_mode: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> ProjectMilestonesRead:
    project = _project(db, project_id)
    mode = parse_data_mode(data_mode, project)
    payload = list_project_milestones(db, project, mode)
    return ProjectMilestonesRead.model_validate(payload.as_dict())


@router.post("/projects/{project_id}/milestones", response_model=MilestoneRead)
def post_project_milestone(
    project_id: int,
    body: MilestoneCreate,
    data_mode: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> MilestoneRead:
    project = _project(db, project_id)
    mode = parse_data_mode(body.data_mode or data_mode, project)
    record = create_milestone(db, project, body.model_dump(), mode)
    db.commit()
    return MilestoneRead.model_validate(record.as_dict())


@router.get("/milestones/{milestone_id}", response_model=MilestoneRead)
def get_one_milestone(
    milestone_id: int,
    data_mode: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> MilestoneRead:
    record = get_milestone_record(db, milestone_id, data_mode)
    return MilestoneRead.model_validate(record.as_dict())


@router.post("/milestones/{milestone_id}/assess", response_model=MilestoneRead)
def post_milestone_assess(
    milestone_id: int,
    data_mode: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> MilestoneRead:
    from app.engines.milestone.repository import get_milestone
    from app.engines.milestone.service import parse_data_mode as _parse

    row = get_milestone(db, milestone_id)
    if row is None:
        raise AppError("Milestone not found.", code="not_found", status_code=404)
    project = _project(db, row.project_id)
    mode = _parse(data_mode or row.data_mode, project)
    record = assess_milestone(db, milestone_id, mode, persist=True)
    db.commit()
    return MilestoneRead.model_validate(record.as_dict())


@router.post("/milestones/{milestone_id}/decision", response_model=MilestoneRead)
def post_milestone_decision(
    milestone_id: int,
    body: MilestoneDecisionCreate,
    data_mode: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> MilestoneRead:
    mode_text = body.data_mode or data_mode
    from app.engines.milestone.repository import get_milestone

    row = get_milestone(db, milestone_id)
    if row is None:
        raise AppError("Milestone not found.", code="not_found", status_code=404)
    project = _project(db, row.project_id)
    mode = parse_data_mode(mode_text or row.data_mode, project)
    record = record_officer_action(
        db,
        milestone_id,
        action=body.action,
        reason=body.reason,
        actor_role=body.actor_role,
        data_mode=mode,
    )
    db.commit()
    return MilestoneRead.model_validate(record.as_dict())
