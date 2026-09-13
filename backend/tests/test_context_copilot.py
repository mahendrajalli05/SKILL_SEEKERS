from __future__ import annotations

from app.copilot.intent import parse_intent
from app.copilot.types import CopilotIntent
from app.db import get_session_factory
from tests.need_test_support import insert_project


def test_external_context_intents() -> None:
    assert parse_intent("What external context is available for this project?") == CopilotIntent.EXTERNAL_CONTEXT
    assert parse_intent("What source supports this cost context?") == CopilotIntent.EXTERNAL_CONTEXT
    assert parse_intent("What year is this development indicator from?") == CopilotIntent.EXTERNAL_CONTEXT
    assert parse_intent("Is this project-specific evidence?") == CopilotIntent.EXTERNAL_CONTEXT


def test_copilot_describes_external_context_not_fraud(client) -> None:
    session = get_session_factory()()
    try:
        row = insert_project(session, internal_project_id="internal:context:copilot")
        session.commit()
        pid = row.id
    finally:
        session.close()

    client.get(f"/api/v2/projects/{pid}/context", params={"data_mode": "REAL"})
    body = client.post(
        f"/api/v1/projects/{pid}/copilot/chat",
        json={"question": "What external context is available for this project?", "data_mode": "REAL"},
    ).json()
    assert body["intent"] == "EXTERNAL_CONTEXT"
    text = (body["answer"] + body["sections"]["why"]).casefold()
    assert "external context" in text
    assert "not a project-specific fact" in text or "not a project-specific" in text
    assert "guilty" not in text
    assert "wrongdoing probability" not in text
