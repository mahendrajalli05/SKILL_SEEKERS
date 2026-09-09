from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain.schemas.common import ProjectListResponse
from app.domain.schemas.project import ProjectRead
from app.errors import AppError
from app.models.project import Project

router = APIRouter()


@router.get("/projects", response_model=ProjectListResponse)
def list_projects(db: Session = Depends(get_db)) -> ProjectListResponse:
    total = db.scalar(select(func.count()).select_from(Project)) or 0
    rows = db.scalars(select(Project).order_by(Project.id)).all()
    return ProjectListResponse(
        items=[ProjectRead.model_validate(row) for row in rows],
        total=total,
    )


@router.get("/projects/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, db: Session = Depends(get_db)) -> ProjectRead:
    row = db.get(Project, project_id)
    if row is None:
        raise AppError("Project not found.", code="not_found", status_code=404)
    return ProjectRead.model_validate(row)
