"""Project-scoped short conversation memory for Investigation Copilot V1.

Stores recent questions and answers for the current investigation session.
Does not create unrestricted personal memory.
"""

from __future__ import annotations

import json
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.copilot.constants import MAX_SESSION_TURNS
from app.copilot.types import CopilotTurnRecord
from app.models.copilot import CopilotTurn


def new_session_id() -> str:
    return str(uuid.uuid4())


def list_session_turns(
    session: Session,
    project_id: int,
    session_id: str,
    *,
    limit: int = MAX_SESSION_TURNS,
) -> list[CopilotTurnRecord]:
    rows = session.scalars(
        select(CopilotTurn)
        .where(
            CopilotTurn.project_id == project_id,
            CopilotTurn.session_id == session_id,
        )
        .order_by(CopilotTurn.id.desc())
        .limit(limit)
    ).all()
    records: list[CopilotTurnRecord] = []
    for row in reversed(list(rows)):
        evidence_ids = []
        if row.evidence_ids_json:
            try:
                loaded = json.loads(row.evidence_ids_json)
                if isinstance(loaded, list):
                    evidence_ids = [str(item) for item in loaded]
            except json.JSONDecodeError:
                evidence_ids = []
        records.append(
            CopilotTurnRecord(
                session_id=row.session_id or session_id,
                question=row.question or "",
                answer=row.answer or "",
                intent=row.intent or "",
                data_mode=row.data_mode or "",
                evidence_ids=evidence_ids,
                recommended_action=row.recommended_action,
                provider=row.model_name or row.mode,
                created_at=row.created_at.isoformat() if row.created_at else None,
            )
        )
    return records


def persist_turn(
    session: Session,
    *,
    project_id: int,
    session_id: str,
    question: str,
    answer: str,
    intent: str,
    data_mode: str,
    evidence_ids: list[str],
    recommended_action: str | None,
    provider: str,
    used_llm: bool,
) -> CopilotTurn:
    row = CopilotTurn(
        project_id=project_id,
        session_id=session_id,
        question=question[:2000],
        answer=answer[:8000],
        mode="llm" if used_llm else "template",
        data_mode=data_mode,
        intent=intent,
        evidence_ids_json=json.dumps(evidence_ids, sort_keys=True),
        recommended_action=recommended_action,
        evidence_set_version="investigation-copilot-v1",
        prompt_version="investigation-copilot-v1",
        model_name=provider,
    )
    session.add(row)
    session.flush()
    existing = session.scalars(
        select(CopilotTurn)
        .where(CopilotTurn.project_id == project_id, CopilotTurn.session_id == session_id)
        .order_by(CopilotTurn.id.asc())
    ).all()
    overflow = len(existing) - MAX_SESSION_TURNS
    if overflow > 0:
        for stale in existing[:overflow]:
            session.delete(stale)
    return row
