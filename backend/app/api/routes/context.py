from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain.schemas.context import ContextSourceListRead, ContextSourceRead, ProjectContextRead
from app.engines.context.errors import ContextError
from app.engines.context.registry import load_registry
from app.engines.context.service import assess_project_context, parse_data_mode
from app.errors import AppError
from app.models.project import Project

router = APIRouter()


def _project(db: Session, project_id: int) -> Project:
    row = db.get(Project, project_id)
    if row is None:
        raise AppError("Project not found.", code="not_found", status_code=404)
    return row


@router.get("/context/sources", response_model=ContextSourceListRead)
def get_context_sources() -> ContextSourceListRead:
    items = [
        ContextSourceRead(
            source_id=item.source_id,
            source_name=item.source_name,
            publisher=item.publisher,
            source_type=item.source_type,
            url=item.url,
            retrieval_date=item.retrieval_date,
            dataset_version=item.dataset_version,
            geographic_level=item.geographic_level,
            unit=item.unit,
            update_frequency=item.update_frequency,
            license_note=item.license_note,
            transformation_notes=item.transformation_notes,
            limitations=item.limitations,
            active=item.active,
            requires_credential=item.requires_credential,
            real_mode_allowed=item.real_mode_allowed,
            unavailable_reason=item.unavailable_reason,
            indicators=item.indicators,
        )
        for item in load_registry()
    ]
    return ContextSourceListRead(items=items)


@router.get("/projects/{project_id}/context", response_model=ProjectContextRead)
def get_project_context(
    project_id: int,
    data_mode: str | None = Query(default=None),
    geographic_level: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> ProjectContextRead:
    project = _project(db, project_id)
    mode = parse_data_mode(data_mode, project)
    result = assess_project_context(
        db, project, mode, persist=True, requested_level=geographic_level
    )
    db.commit()
    return ProjectContextRead.model_validate(result.as_dict())


@router.post("/projects/{project_id}/context/refresh", response_model=ProjectContextRead)
def post_project_context_refresh(
    project_id: int,
    data_mode: str | None = Query(default=None),
    geographic_level: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> ProjectContextRead:
    project = _project(db, project_id)
    mode = parse_data_mode(data_mode, project)
    try:
        result = assess_project_context(
            db, project, mode, persist=True, requested_level=geographic_level
        )
    except ContextError:
        raise
    db.commit()
    return ProjectContextRead.model_validate(result.as_dict())
