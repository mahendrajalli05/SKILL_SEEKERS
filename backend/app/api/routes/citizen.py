from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile as StarletteUploadFile

from app.db import get_db
from app.domain.schemas.citizen import (
    CitizenReportCreate,
    CitizenReportListResponse,
    CitizenReportRead,
    CitizenSummaryRead,
)
from app.engines.citizen.constants import ENGINE_NAME, ENGINE_VERSION, GOVERNANCE_NOTE, PRIVACY_NOTE, THRESHOLD_NOTE
from app.engines.citizen.service import (
    get_report_record,
    list_project_reports,
    parse_data_mode,
    project_citizen_summary,
    submit_citizen_report,
    verify_citizen_report,
)
from app.errors import AppError
from app.models.project import Project

router = APIRouter()


def _project(db: Session, project_id: int) -> Project:
    row = db.get(Project, project_id)
    if row is None:
        raise AppError("Project not found.", code="not_found", status_code=404)
    return row


def _as_read(payload: dict) -> CitizenReportRead:
    return CitizenReportRead.model_validate(payload)


def _form_value(form, key: str) -> str | None:
    value = form.get(key)
    if value is None or isinstance(value, StarletteUploadFile):
        return None
    text = str(value).strip()
    return text or None


@router.post("/projects/{project_id}/citizen-reports", response_model=CitizenReportRead)
async def post_citizen_report(
    project_id: int,
    request: Request,
    data_mode: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> CitizenReportRead:
    project = _project(db, project_id)
    content_type = (request.headers.get("content-type") or "").casefold()
    image_bytes = None
    filename = None
    declared_mime = None
    if "multipart/form-data" in content_type:
        form = await request.form()
        payload = {
            "satisfaction_rating": _form_value(form, "satisfaction_rating"),
            "observation_text": _form_value(form, "observation_text"),
            "issue_category": _form_value(form, "issue_category"),
            "latitude": _form_value(form, "latitude"),
            "longitude": _form_value(form, "longitude"),
            "capture_timestamp": _form_value(form, "capture_timestamp"),
            "data_mode": _form_value(form, "data_mode") or data_mode,
        }
        upload = form.get("file")
        if isinstance(upload, StarletteUploadFile):
            image_bytes = await upload.read()
            filename = upload.filename
            declared_mime = upload.content_type
        mode_text = payload.get("data_mode") or data_mode
    else:
        body = CitizenReportCreate.model_validate(await request.json())
        payload = body.model_dump()
        mode_text = body.data_mode or data_mode
    mode = parse_data_mode(mode_text, project)
    record = submit_citizen_report(
        db,
        project,
        payload,
        mode,
        image_bytes=image_bytes,
        filename=filename,
        declared_mime=declared_mime,
    )
    db.commit()
    return _as_read(record.as_dict())


@router.get("/projects/{project_id}/citizen-reports", response_model=CitizenReportListResponse)
def get_citizen_reports(
    project_id: int,
    data_mode: str | None = Query(default=None),
    include_location: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> CitizenReportListResponse:
    project = _project(db, project_id)
    mode = parse_data_mode(data_mode, project)
    items = list_project_reports(db, project, mode, include_location=include_location)
    return CitizenReportListResponse(
        project_id=project.id,
        internal_project_id=project.internal_project_id,
        data_mode=mode.value,
        items=[_as_read(item.as_dict()) for item in items],
        privacy_note=PRIVACY_NOTE,
        threshold_note=THRESHOLD_NOTE,
        governance_note=GOVERNANCE_NOTE,
        engine_version=ENGINE_VERSION,
        engine_name=ENGINE_NAME,
    )


@router.get("/citizen-reports/{report_id}", response_model=CitizenReportRead)
def get_one_citizen_report(
    report_id: int,
    data_mode: str | None = Query(default=None),
    include_location: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> CitizenReportRead:
    record = get_report_record(db, report_id, data_mode, include_location=include_location)
    return _as_read(record.as_dict())


@router.post("/citizen-reports/{report_id}/verify", response_model=CitizenReportRead)
def post_verify_citizen_report(
    report_id: int,
    data_mode: str | None = Query(default=None),
    include_location: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> CitizenReportRead:
    from app.engines.citizen.repository import get_report

    row = get_report(db, report_id)
    if row is None:
        raise AppError("Citizen report not found.", code="not_found", status_code=404)
    project = _project(db, row.project_id)
    mode = parse_data_mode(data_mode or row.data_mode, project)
    record = verify_citizen_report(db, report_id, mode, include_location=include_location)
    db.commit()
    return _as_read(record.as_dict())


@router.get("/projects/{project_id}/citizen-summary", response_model=CitizenSummaryRead)
def get_citizen_summary(
    project_id: int,
    data_mode: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> CitizenSummaryRead:
    project = _project(db, project_id)
    mode = parse_data_mode(data_mode, project)
    summary = project_citizen_summary(db, project, mode, persist=True)
    db.commit()
    payload = summary.as_dict()
    payload["threshold_note"] = THRESHOLD_NOTE
    return CitizenSummaryRead.model_validate(payload)
