from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain.schemas.need import NeedImpactRankRead, NeedImpactRankRequest, NeedImpactRead
from app.engines.need.errors import NeedImpactError
from app.engines.need.service import assess_project_need_impact, parse_data_mode, rank_projects
from app.errors import AppError
from app.models.project import Project

router = APIRouter()


def _project(db: Session, project_id: int) -> Project:
    row = db.get(Project, project_id)
    if row is None:
        raise AppError("Project not found.", code="not_found", status_code=404)
    return row


@router.get("/projects/{project_id}/need-impact", response_model=NeedImpactRead)
def get_project_need_impact(
    project_id: int,
    data_mode: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> NeedImpactRead:
    project = _project(db, project_id)
    mode = parse_data_mode(data_mode, project)
    result = assess_project_need_impact(db, project, mode, persist=True)
    db.commit()
    return NeedImpactRead.model_validate(result.as_dict())


@router.post("/need-impact/rank", response_model=NeedImpactRankRead)
def post_need_impact_rank(
    body: NeedImpactRankRequest,
    data_mode: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> NeedImpactRankRead:
    if not body.project_ids:
        raise NeedImpactError("At least one candidate project id is required.", code="empty_candidates")
    mode = parse_data_mode(body.data_mode or data_mode)
    ranked = rank_projects(
        db,
        body.project_ids,
        mode,
        available_budget=body.available_budget,
        available_budget_crore=body.available_budget_crore,
        persist=True,
    )
    db.commit()
    return NeedImpactRankRead.model_validate(ranked.as_dict())
