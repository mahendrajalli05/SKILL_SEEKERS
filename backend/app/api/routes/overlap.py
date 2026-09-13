from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain.schemas.overlap import OverlapIntelligenceResponse
from app.engines.overlap.service import assess_project_overlap
from app.engines.overlap.types import OverlapMode
from app.errors import AppError
from app.models.project import Project

router = APIRouter()


@router.get(
    "/projects/{project_id}/overlap-intelligence",
    response_model=OverlapIntelligenceResponse,
)
def get_overlap_intelligence(
    project_id: int,
    db: Session = Depends(get_db),
    mode: Literal["real", "hybrid-test"] = Query(
        default="real",
        description=(
            "REAL uses observed text, category, constituency, amount, date, and "
            "sparse place text only. hybrid-test attaches synthetic GPS for controlled tests."
        ),
    ),
) -> OverlapIntelligenceResponse:
    """Potential Overlap evidence. Investigation Priority is not assigned here."""
    row = db.get(Project, project_id)
    if row is None:
        raise AppError("Project not found.", code="not_found", status_code=404)
    overlap_mode = OverlapMode.HYBRID_TEST if mode == "hybrid-test" else OverlapMode.REAL
    result = assess_project_overlap(db, project_id, mode=overlap_mode, persist=True)
    return OverlapIntelligenceResponse.from_result(result)
