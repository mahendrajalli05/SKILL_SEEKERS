from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain.enums import DataMode
from app.domain.schemas.risk import ProjectRiskResponse
from app.engines.fusion.service import assess_project_risk
from app.errors import AppError
from app.models.project import Project

router = APIRouter()


@router.get(
    "/projects/{project_id}/risk",
    response_model=ProjectRiskResponse,
)
def get_project_risk(
    project_id: int,
    db: Session = Depends(get_db),
    data_mode: Literal["REAL", "HYBRID", "SYNTHETIC"] = Query(
        default="REAL",
        description=(
            "REAL fuses observed MPLADS evidence only. HYBRID includes "
            "synthetic enrichment evidence. Investigation Priority is not a "
            "fraud probability."
        ),
    ),
) -> ProjectRiskResponse:
    """Fused Investigation Priority and Evidence Confidence. Not a fraud score."""
    row = db.get(Project, project_id)
    if row is None:
        raise AppError("Project not found.", code="not_found", status_code=404)
    result = assess_project_risk(db, project_id, data_mode=DataMode(data_mode), persist=True)
    return ProjectRiskResponse.from_result(result)
