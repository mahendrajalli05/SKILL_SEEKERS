from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.copilot.service import chat, copilot_context
from app.db import get_db
from app.domain.schemas.copilot import CopilotChatRequest, CopilotChatResponse, CopilotContextResponse
from app.errors import AppError
from app.models.project import Project

router = APIRouter()


def _project(db: Session, project_id: int) -> Project:
    row = db.get(Project, project_id)
    if row is None:
        raise AppError("Project not found.", code="not_found", status_code=404)
    return row


@router.get("/projects/{project_id}/copilot/context", response_model=CopilotContextResponse)
def get_copilot_context(
    project_id: int,
    data_mode: str | None = Query(default=None),
    session_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> CopilotContextResponse:
    project = _project(db, project_id)
    payload = copilot_context(db, project, data_mode, session_id)
    return CopilotContextResponse.model_validate(payload)


@router.post("/projects/{project_id}/copilot/chat", response_model=CopilotChatResponse)
def post_copilot_chat(
    project_id: int,
    body: CopilotChatRequest,
    data_mode: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> CopilotChatResponse:
    project = _project(db, project_id)
    payload = chat(
        db,
        project,
        question=body.question,
        data_mode=body.data_mode or data_mode,
        session_id=body.session_id,
    )
    return CopilotChatResponse.model_validate(payload)
