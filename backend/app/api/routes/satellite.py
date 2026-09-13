from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain.schemas.satellite import SatelliteCheckRequest, SatelliteRead
from app.engines.satellite.service import check_project_satellite, parse_data_mode
from app.errors import AppError
from app.models.project import Project

router = APIRouter()


def _project(db: Session, project_id: int) -> Project:
    row = db.get(Project, project_id)
    if row is None:
        raise AppError("Project not found.", code="not_found", status_code=404)
    return row


def _as_read(payload: dict) -> SatelliteRead:
    return SatelliteRead.model_validate(payload)


@router.get("/projects/{project_id}/satellite", response_model=SatelliteRead)
def get_project_satellite(
    project_id: int,
    data_mode: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> SatelliteRead:
    project = _project(db, project_id)
    mode = parse_data_mode(data_mode, project)
    result = check_project_satellite(db, project, mode, persist=True)
    db.commit()
    return _as_read(result.as_dict())


@router.post("/projects/{project_id}/satellite/check", response_model=SatelliteRead)
def post_project_satellite_check(
    project_id: int,
    body: SatelliteCheckRequest | None = None,
    data_mode: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> SatelliteRead:
    project = _project(db, project_id)
    payload = body or SatelliteCheckRequest()
    mode = parse_data_mode(payload.data_mode or data_mode, project)
    result = check_project_satellite(
        db,
        project,
        mode,
        provider_name=payload.provider,
        test_scenario=payload.test_scenario,
        date_start=payload.date_start,
        date_end=payload.date_end,
        aoi_radius_m=payload.aoi_radius_meters,
        persist=True,
    )
    db.commit()
    return _as_read(result.as_dict())
