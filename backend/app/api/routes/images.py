from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain.schemas.image import ImageAttachResult, ImageListResponse, ImageRead, ImageSummaryRead
from app.engines.image.service import (
    analyze_image,
    attach_image_to_evidence,
    get_photo,
    image_read_payload,
    list_project_photos,
    parse_data_mode,
    project_image_summary,
    upload_image,
)
from app.errors import AppError
from app.models.project import Project

router = APIRouter()


def _project(db: Session, project_id: int) -> Project:
    row = db.get(Project, project_id)
    if row is None:
        raise AppError("Project not found.", code="not_found", status_code=404)
    return row


def _as_read(payload: dict) -> ImageRead:
    return ImageRead.model_validate(payload)


@router.post("/projects/{project_id}/images", response_model=ImageRead)
def post_project_image(
    project_id: int,
    file: UploadFile = File(...),
    data_mode: str | None = Form(default=None),
    source: str | None = Form(default="officer_upload"),
    db: Session = Depends(get_db),
) -> ImageRead:
    project = _project(db, project_id)
    mode = parse_data_mode(data_mode, project)
    payload = file.file.read()
    row = upload_image(
        db,
        project,
        payload=payload,
        filename=file.filename,
        declared_mime=file.content_type,
        data_mode=mode,
        source=source or "officer_upload",
    )
    db.commit()
    db.refresh(row)
    return _as_read(image_read_payload(db, row))


@router.get("/projects/{project_id}/images", response_model=ImageListResponse)
def get_project_images(
    project_id: int,
    data_mode: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> ImageListResponse:
    project = _project(db, project_id)
    mode = parse_data_mode(data_mode, project)
    items = []
    for row in list_project_photos(db, project_id):
        if mode.value == "REAL" and row.data_mode and row.data_mode != "REAL":
            continue
        items.append(_as_read(image_read_payload(db, row)))
    summary = project_image_summary(db, project, mode)
    return ImageListResponse(
        project_id=project_id,
        internal_project_id=project.internal_project_id,
        summary=ImageSummaryRead.model_validate(summary),
        items=items,
    )


@router.get("/images/{image_id}", response_model=ImageRead)
def get_one_image(
    image_id: int,
    db: Session = Depends(get_db),
) -> ImageRead:
    row = get_photo(db, image_id)
    if row is None:
        raise AppError("Image not found.", code="not_found", status_code=404)
    return _as_read(image_read_payload(db, row))


@router.post("/images/{image_id}/analyze", response_model=ImageRead)
def post_analyze_image(
    image_id: int,
    data_mode: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> ImageRead:
    row = get_photo(db, image_id)
    if row is None:
        raise AppError("Image not found.", code="not_found", status_code=404)
    project = _project(db, row.project_id)
    parse_data_mode(data_mode or row.data_mode, project)
    analyze_image(db, project, row)
    db.commit()
    db.refresh(row)
    return _as_read(image_read_payload(db, row))


@router.post("/images/{image_id}/attach-evidence", response_model=ImageAttachResult)
def post_attach_image_evidence(
    image_id: int,
    db: Session = Depends(get_db),
) -> ImageAttachResult:
    row = get_photo(db, image_id)
    if row is None:
        raise AppError("Image not found.", code="not_found", status_code=404)
    project = _project(db, row.project_id)
    evidence_ids = attach_image_to_evidence(db, project, row)
    db.commit()
    db.refresh(row)
    return ImageAttachResult(
        image_id=row.id,
        project_id=project.id,
        attached_to_evidence=True,
        evidence_ids=evidence_ids,
    )
