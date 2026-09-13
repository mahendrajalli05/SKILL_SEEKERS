from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain.schemas.document import AttachResult, DocumentListResponse, DocumentRead, ExtractionRead
from app.engines.document.service import (
    attach_extracted_to_evidence,
    attach_extracted_to_plan,
    document_read_payload,
    extract_document,
    get_document,
    list_conflicts,
    list_project_documents,
    parse_data_mode,
    upload_document,
)
from app.engines.document.types import ExtractionResult
from app.errors import AppError
from app.models.project import Project

router = APIRouter()


def _project(db: Session, project_id: int) -> Project:
    row = db.get(Project, project_id)
    if row is None:
        raise AppError("Project not found.", code="not_found", status_code=404)
    return row


def _as_read(payload: dict) -> DocumentRead:
    extraction = payload.get("extraction")
    return DocumentRead(
        document_id=payload["document_id"],
        project_id=payload["project_id"],
        filename=payload.get("filename"),
        mime_type=payload.get("mime_type"),
        document_type=payload.get("document_type"),
        pce_kind=payload.get("pce_kind"),
        uploaded_at=payload.get("uploaded_at"),
        data_mode=payload.get("data_mode"),
        provenance=payload.get("provenance") or {},
        content_sha256=payload.get("content_sha256"),
        file_size=payload.get("file_size"),
        extraction_status=payload.get("extraction_status"),
        integrity_status=payload.get("integrity_status"),
        duplicate_of_id=payload.get("duplicate_of_id"),
        attached_to_plan=bool(payload.get("attached_to_plan")),
        attached_to_evidence=bool(payload.get("attached_to_evidence")),
        observed_quantity=payload.get("observed_quantity"),
        observed_quantity_unit=payload.get("observed_quantity_unit"),
        observed_expenditure=payload.get("observed_expenditure"),
        extraction=ExtractionRead.model_validate(extraction) if extraction else None,
        engine_version=payload["engine_version"],
        note=payload.get("note") or DocumentRead.model_fields["note"].default,
    )


def _extraction_read(result: ExtractionResult) -> ExtractionRead:
    return ExtractionRead(
        status=result.status,
        extraction_method=result.extraction_method,
        fields=[item.as_dict() for item in result.fields],
        structure=result.structure.as_dict(),
        page_count=result.page_count,
        raw_text_available=result.raw_text_available,
        notes=result.notes,
        text_sha256=result.text_sha256,
        similar_document_ids=result.similar_document_ids,
        evidence_id=result.evidence_id,
    )


@router.post("/projects/{project_id}/documents", response_model=DocumentRead)
def post_project_document(
    project_id: int,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    data_mode: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> DocumentRead:
    project = _project(db, project_id)
    mode = parse_data_mode(data_mode, project)
    payload = file.file.read()
    row = upload_document(
        db,
        project,
        payload=payload,
        filename=file.filename,
        declared_mime=file.content_type,
        document_type=document_type,
        data_mode=mode,
    )
    db.commit()
    db.refresh(row)
    return _as_read(document_read_payload(db, row))


@router.get("/projects/{project_id}/documents", response_model=DocumentListResponse)
def get_project_documents(
    project_id: int,
    data_mode: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> DocumentListResponse:
    project = _project(db, project_id)
    mode = parse_data_mode(data_mode, project)
    items = []
    for row in list_project_documents(db, project_id):
        if mode.value == "REAL" and row.data_mode and row.data_mode != "REAL":
            continue
        items.append(_as_read(document_read_payload(db, row)))
    return DocumentListResponse(
        project_id=project_id,
        items=items,
        conflicts=list_conflicts(db, project, mode),
    )


@router.get("/documents/{document_id}", response_model=DocumentRead)
def get_one_document(
    document_id: int,
    db: Session = Depends(get_db),
) -> DocumentRead:
    row = get_document(db, document_id)
    if row is None:
        raise AppError("Document not found.", code="not_found", status_code=404)
    return _as_read(document_read_payload(db, row))


@router.post("/documents/{document_id}/extract", response_model=ExtractionRead)
def post_extract_document(
    document_id: int,
    data_mode: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> ExtractionRead:
    row = get_document(db, document_id)
    if row is None:
        raise AppError("Document not found.", code="not_found", status_code=404)
    project = _project(db, row.project_id)
    mode = parse_data_mode(data_mode or row.data_mode, project)
    result = extract_document(db, project, row, data_mode=mode)
    db.commit()
    return _extraction_read(result)


@router.post("/documents/{document_id}/attach-plan", response_model=AttachResult)
def post_attach_plan(
    document_id: int,
    db: Session = Depends(get_db),
) -> AttachResult:
    row = get_document(db, document_id)
    if row is None:
        raise AppError("Document not found.", code="not_found", status_code=404)
    project = _project(db, row.project_id)
    conflicts, notes = attach_extracted_to_plan(db, project, row)
    db.commit()
    db.refresh(row)
    return AttachResult(
        document_id=row.id,
        project_id=project.id,
        attached_to_plan=True,
        attached_to_evidence=False,
        conflicts=[item.as_dict() for item in conflicts],
        notes=notes,
    )


@router.post("/documents/{document_id}/attach-evidence", response_model=AttachResult)
def post_attach_evidence(
    document_id: int,
    db: Session = Depends(get_db),
) -> AttachResult:
    row = get_document(db, document_id)
    if row is None:
        raise AppError("Document not found.", code="not_found", status_code=404)
    project = _project(db, row.project_id)
    evidence_id = attach_extracted_to_evidence(db, project, row)
    db.commit()
    db.refresh(row)
    return AttachResult(
        document_id=row.id,
        project_id=project.id,
        attached_to_plan=False,
        attached_to_evidence=True,
        evidence_id=evidence_id,
        observed_quantity=row.observed_quantity,
        observed_quantity_unit=row.observed_quantity_unit,
        observed_expenditure=row.observed_expenditure,
    )
