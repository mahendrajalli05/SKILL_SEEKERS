from __future__ import annotations

from app.copilot.intent import parse_intent
from app.copilot.types import CopilotIntent
from app.db import get_session_factory
from app.domain.enums import DataMode
from lifecycle_fixtures import insert_project


def test_lifecycle_copilot_intents() -> None:
    assert parse_intent("Where is this project in its lifecycle?") == CopilotIntent.LIFECYCLE_WHERE
    assert parse_intent("What remains to be verified?") == CopilotIntent.LIFECYCLE_REMAINING
    assert parse_intent("What was the last milestone decision?") == CopilotIntent.LIFECYCLE_LAST_MILESTONE
    assert parse_intent("What evidence is missing?") == CopilotIntent.MISSING_INFORMATION


def test_copilot_explains_lifecycle(client) -> None:
    session = get_session_factory()()
    try:
        project = insert_project(
            session,
            internal_project_id="internal:lifecycle:copilot",
            is_synthetic=True,
            synthetic_label="SYNTHETIC: lifecycle copilot test (not a government project)",
        )
        session.commit()
        project_id = project.id
    finally:
        session.close()

    where = client.post(
        f"/api/v1/projects/{project_id}/copilot/chat",
        json={"question": "Where is this project in its lifecycle?", "data_mode": "SYNTHETIC"},
    ).json()
    assert where["intent"] == "LIFECYCLE_WHERE"
    assert "workflow state" in where["answer"].casefold() or "lifecycle" in where["answer"].casefold()
    assert "fraud" not in where["answer"].casefold() or "not" in where["answer"].casefold()
    assert "sanction" not in where["answer"].casefold() or "not" in where["answer"].casefold()

    remaining = client.post(
        f"/api/v1/projects/{project_id}/copilot/chat",
        json={"question": "What remains to be verified?", "data_mode": "SYNTHETIC"},
    ).json()
    assert remaining["intent"] == "LIFECYCLE_REMAINING"
    assert "remaining" in remaining["answer"].casefold() or "not available" in remaining["answer"].casefold()

    missing = client.post(
        f"/api/v1/projects/{project_id}/copilot/chat",
        json={"question": "What evidence is missing?", "data_mode": "SYNTHETIC"},
    ).json()
    assert missing["intent"] == "MISSING_INFORMATION"

    last = client.post(
        f"/api/v1/projects/{project_id}/copilot/chat",
        json={"question": "What was the last milestone decision?", "data_mode": "SYNTHETIC"},
    ).json()
    assert last["intent"] == "LIFECYCLE_LAST_MILESTONE"
