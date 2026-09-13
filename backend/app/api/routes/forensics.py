from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain.schemas.forensics import ImageForensicsRead
from app.engines.forensics.service import get_image_forensics, parse_data_mode, run_image_forensics
from app.engines.image.repository import get_photo
from app.errors import AppError
from app.models.project import Project

router = APIRouter()


def _project(db: Session, project_id: int) -> Project:
    row = db.get(Project, project_id)
    if row is None:
        raise AppError("Project not found.", code="not_found", status_code=404)
    return row


def _as_read(payload: dict) -> ImageForensicsRead:
    return ImageForensicsRead.model_validate(payload)


@router.post("/images/{image_id}/forensics", response_model=ImageForensicsRead)
def post_image_forensics(
    image_id: int,
    data_mode: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> ImageForensicsRead:
    row = get_photo(db, image_id)
    if row is None:
        raise AppError("Image not found.", code="not_found", status_code=404)
    project = _project(db, row.project_id)
    mode = parse_data_mode(data_mode or row.data_mode, project)
    result = run_image_forensics(db, project, row, data_mode=mode, persist=True)
    db.commit()
    return _as_read(result.as_dict())


@router.get("/images/{image_id}/forensics", response_model=ImageForensicsRead)
def get_one_image_forensics(
    image_id: int,
    data_mode: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> ImageForensicsRead:
    row = get_photo(db, image_id)
    if row is None:
        raise AppError("Image not found.", code="not_found", status_code=404)
    project = _project(db, row.project_id)
    mode = parse_data_mode(data_mode or row.data_mode, project)
    result = get_image_forensics(db, project, row, data_mode=mode)
    db.commit()
    return _as_read(result.as_dict())
