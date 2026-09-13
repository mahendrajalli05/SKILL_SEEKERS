from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain.enums import DataMode
from app.domain.schemas.risk_v2 import ProjectRiskV2Response
from app.engines.fusion_v2.service import assess_project_risk_v2
from app.errors import AppError
from app.models.project import Project

router = APIRouter()


@router.get(
    "/projects/{project_id}/risk",
    response_model=ProjectRiskV2Response,
)
def get_project_risk_v2(
    project_id: int,
    db: Session = Depends(get_db),
    data_mode: Literal["REAL", "HYBRID", "SYNTHETIC"] = Query(
        default="REAL",
        description=(
            "REAL fuses observed MPLADS evidence only. HYBRID includes "
            "synthetic enrichment evidence. Investigation Priority is not a "
            "fraud probability. V1.1 remains at GET /api/v1/projects/{id}/risk."
        ),
    ),
) -> ProjectRiskV2Response:
    """Risk Fusion V2. Not a fraud score, sanction, or payment release."""
    row = db.get(Project, project_id)
    if row is None:
        raise AppError("Project not found.", code="not_found", status_code=404)
    result = assess_project_risk_v2(db, project_id, data_mode=DataMode(data_mode), persist=True)
    return ProjectRiskV2Response.from_result(result)
