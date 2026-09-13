from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain.schemas.geo import GeospatialCheckRequest, GeospatialRead
from app.engines.geo.service import check_project_geospatial, parse_data_mode
from app.errors import AppError
from app.models.project import Project

router = APIRouter()


def _project(db: Session, project_id: int) -> Project:
    row = db.get(Project, project_id)
    if row is None:
        raise AppError("Project not found.", code="not_found", status_code=404)
    return row


def _as_read(payload: dict) -> GeospatialRead:
    return GeospatialRead.model_validate(payload)


@router.get("/projects/{project_id}/geospatial", response_model=GeospatialRead)
def get_project_geospatial(
    project_id: int,
    data_mode: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> GeospatialRead:
    project = _project(db, project_id)
    mode = parse_data_mode(data_mode, project)
    result = check_project_geospatial(db, project, mode, persist=True)
    db.commit()
    return _as_read(result.as_dict())


@router.post("/projects/{project_id}/geospatial/check", response_model=GeospatialRead)
def post_project_geospatial_check(
    project_id: int,
    body: GeospatialCheckRequest | None = None,
    data_mode: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> GeospatialRead:
    project = _project(db, project_id)
    payload = body or GeospatialCheckRequest()
    mode = parse_data_mode(payload.data_mode or data_mode, project)
    result = check_project_geospatial(
        db,
        project,
        mode,
        threshold_meters=payload.threshold_meters,
        persist=True,
    )
    db.commit()
    return _as_read(result.as_dict())
