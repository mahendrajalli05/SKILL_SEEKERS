from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain.schemas.cost import CostIntelligenceResponse
from app.engines.cost.service import assess_project_cost
from app.errors import AppError
from app.models.project import Project

router = APIRouter()


@router.get(
    "/projects/{project_id}/cost-intelligence",
    response_model=CostIntelligenceResponse,
)
def get_cost_intelligence(
    project_id: int,
    db: Session = Depends(get_db),
) -> CostIntelligenceResponse:
    """Peer-based Allocation Cost Anomaly evidence. Investigation Priority is not assigned here."""
    row = db.get(Project, project_id)
    if row is None:
        raise AppError("Project not found.", code="not_found", status_code=404)
    result = assess_project_cost(db, project_id, persist=True)
    return CostIntelligenceResponse.from_result(result)
