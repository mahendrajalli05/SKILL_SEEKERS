from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain.schemas.compliance import ComplianceIntelligenceResponse
from app.engines.compliance.service import assess_project_compliance
from app.engines.compliance.types import ComplianceMode
from app.errors import AppError
from app.models.project import Project

router = APIRouter()


@router.get(
    "/projects/{project_id}/compliance",
    response_model=ComplianceIntelligenceResponse,
)
def get_compliance(
    project_id: int,
    db: Session = Depends(get_db),
    mode: Literal["real", "hybrid-test"] = Query(
        default="real",
        description="REAL uses observed extract fields only. hybrid-test uses synthetic execution/expenditure fields for controlled testing.",
    ),
) -> ComplianceIntelligenceResponse:
    """MPLADS guideline-rule evaluation. Investigation Priority is not assigned here."""
    row = db.get(Project, project_id)
    if row is None:
        raise AppError("Project not found.", code="not_found", status_code=404)
    compliance_mode = ComplianceMode.HYBRID_TEST if mode == "hybrid-test" else ComplianceMode.REAL
    result = assess_project_compliance(db, project_id, mode=compliance_mode, persist=True)
    return ComplianceIntelligenceResponse.from_result(result)
