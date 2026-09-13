from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain.schemas.graph import GraphIntelligenceResponse
from app.engines.graph.service import assess_project_graph
from app.engines.graph.types import GraphMode
from app.errors import AppError
from app.models.project import Project

router = APIRouter()


@router.get(
    "/projects/{project_id}/graph",
    response_model=GraphIntelligenceResponse,
)
def get_project_graph(
    project_id: int,
    db: Session = Depends(get_db),
    mode: Literal["real", "hybrid-test"] = Query(
        default="real",
        description=(
            "REAL uses observed MP, constituency, category, IDA, state, and "
            "Overlap Intelligence SIMILAR_TO. hybrid-test may attach synthetic "
            "GPS only inside Overlap similarity scoring."
        ),
    ),
) -> GraphIntelligenceResponse:
    """Relationship Graph neighborhood. Investigation Priority is not assigned here."""
    row = db.get(Project, project_id)
    if row is None:
        raise AppError("Project not found.", code="not_found", status_code=404)
    graph_mode = GraphMode.HYBRID_TEST if mode == "hybrid-test" else GraphMode.REAL
    result = assess_project_graph(db, project_id, mode=graph_mode, persist=True)
    return GraphIntelligenceResponse.from_result(result)
