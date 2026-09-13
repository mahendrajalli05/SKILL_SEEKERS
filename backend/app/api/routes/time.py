from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain.schemas.time import TimeIntelligenceResponse
from app.engines.time.service import assess_project_time
from app.engines.time.types import TimeMode
from app.errors import AppError
from app.models.project import Project

router = APIRouter()


@router.get(
    "/projects/{project_id}/time-intelligence",
    response_model=TimeIntelligenceResponse,
)
def get_time_intelligence(
    project_id: int,
    db: Session = Depends(get_db),
    mode: Literal["real", "hybrid-test"] = Query(
        default="real",
        description="REAL uses observed recommendation date and status only. hybrid-test uses synthetic dates for controlled testing.",
    ),
) -> TimeIntelligenceResponse:
    """Time Anomaly evidence. Investigation Priority is not assigned here."""
    row = db.get(Project, project_id)
    if row is None:
        raise AppError("Project not found.", code="not_found", status_code=404)
    time_mode = TimeMode.HYBRID_TEST if mode == "hybrid-test" else TimeMode.REAL
    result = assess_project_time(db, project_id, mode=time_mode, persist=True)
    return TimeIntelligenceResponse.from_result(result)
