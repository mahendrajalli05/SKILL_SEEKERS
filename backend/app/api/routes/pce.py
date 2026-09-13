from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain.schemas.pce import (
    ClaimListResponse,
    ClaimRead,
    ClaimWrite,
    EvidenceAttachmentRead,
    EvidenceAttachmentWrite,
    PlanRead,
    PlanWrite,
    VerificationRead,
)
from app.engines.pce.repository import list_claims
from app.engines.pce.service import (
    assembled_claim_from_row,
    get_project_plan,
    parse_data_mode,
    record_claim,
    record_evidence,
    record_plan,
    verify_project,
)
from app.errors import AppError
from app.models.project import Project

router = APIRouter()


def _project(db: Session, project_id: int) -> Project:
    row = db.get(Project, project_id)
    if row is None:
        raise AppError("Project not found.", code="not_found", status_code=404)
    return row


@router.get("/projects/{project_id}/plan", response_model=PlanRead)
def get_plan(
    project_id: int,
    data_mode: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> PlanRead:
    project = _project(db, project_id)
    mode = parse_data_mode(data_mode, project)
    return PlanRead.from_assembled(get_project_plan(db, project, mode))


@router.post("/projects/{project_id}/plan", response_model=PlanRead)
def post_plan(
    project_id: int,
    body: PlanWrite,
    data_mode: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> PlanRead:
    project = _project(db, project_id)
    mode = parse_data_mode(body.data_mode or data_mode, project)
    plan = record_plan(db, project, body.model_dump(), mode)
    db.commit()
    return PlanRead.from_assembled(plan)


@router.get("/projects/{project_id}/claims", response_model=ClaimListResponse)
def get_claims(
    project_id: int,
    data_mode: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> ClaimListResponse:
    project = _project(db, project_id)
    mode = parse_data_mode(data_mode, project)
    items = []
    for row in list_claims(db, project_id):
        assembled = assembled_claim_from_row(project, row)
        if mode.value == "REAL" and str(assembled.data_mode) != "REAL":
            continue
        items.append(ClaimRead.from_assembled(assembled))
    return ClaimListResponse(project_id=project_id, items=items)


@router.post("/projects/{project_id}/claims", response_model=ClaimRead)
def post_claim(
    project_id: int,
    body: ClaimWrite,
    data_mode: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> ClaimRead:
    project = _project(db, project_id)
    mode = parse_data_mode(body.data_mode or data_mode, project)
    claim = record_claim(db, project, body.model_dump(), mode)
    db.commit()
    return ClaimRead.from_assembled(claim)


@router.post("/projects/{project_id}/evidence", response_model=EvidenceAttachmentRead)
def post_evidence_attachment(
    project_id: int,
    body: EvidenceAttachmentWrite,
    data_mode: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> EvidenceAttachmentRead:
    project = _project(db, project_id)
    mode = parse_data_mode(body.data_mode or data_mode, project)
    item = record_evidence(db, project, body.model_dump(), mode)
    db.commit()
    return EvidenceAttachmentRead.from_assembled(item)


@router.get("/projects/{project_id}/verification", response_model=VerificationRead)
def get_verification(
    project_id: int,
    data_mode: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> VerificationRead:
    project = _project(db, project_id)
    mode = parse_data_mode(data_mode, project)
    result = verify_project(db, project, mode, persist=True)
    db.commit()
    return VerificationRead.from_result(result)
