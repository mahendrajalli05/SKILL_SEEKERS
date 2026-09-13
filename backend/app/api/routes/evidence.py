from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain.schemas.evidence import ProjectEvidenceResponse
from app.errors import AppError
from app.evidence.repository import list_project_evidence
from app.models.project import Project

router = APIRouter()


@router.get(
    "/projects/{project_id}/evidence",
    response_model=ProjectEvidenceResponse,
)
def get_project_evidence(
    project_id: int,
    engine: str | None = Query(default=None),
    data_mode: str | None = Query(default=None),
    signal_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> ProjectEvidenceResponse:
    """Return stored Evidence Objects for one project. Does not fuse Investigation Priority."""
    row = db.get(Project, project_id)
    if row is None:
        raise AppError("Project not found.", code="not_found", status_code=404)
    items = list_project_evidence(
        db,
        project_id,
        engine=engine,
        data_mode=data_mode,
        signal_type=signal_type,
    )
    return ProjectEvidenceResponse(
        project_id=project_id,
        internal_project_id=row.internal_project_id,
        items=items,
    )
