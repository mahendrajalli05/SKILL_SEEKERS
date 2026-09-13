from __future__ import annotations

from app.config import reset_settings_cache
from app.db import get_session_factory
from app.scope import current_pilot_label, current_pilot_state
from tests.test_search_api import insert_project


def test_scope_endpoint_describes_ap_pilot_without_deleting_other_states(client) -> None:
    session = get_session_factory()()
    try:
        insert_project(session, internal_project_id="internal:synthetic:scope:ap")
        insert_project(
            session,
            internal_project_id="internal:synthetic:scope:tn",
            state="Tamil Nadu",
            constituency="CHENNAI SOUTH",
        )
        session.commit()
    finally:
        session.close()

    response = client.get("/api/v1/scope")
    assert response.status_code == 200
    body = response.json()
    assert body["current_pilot"] == "Andhra Pradesh"
    assert body["pilot_label"] == "Current Pilot: Andhra Pradesh"
    assert body["default_state"] == "Andhra Pradesh"
    assert body["default_data_mode"] == "HYBRID"
    assert body["scope_configurable"] is True
    assert body["database_retains_all_states"] is True
    assert current_pilot_state() == "Andhra Pradesh"
    assert current_pilot_label() == "Current Pilot: Andhra Pradesh"

    scoped = client.get("/api/v1/projects")
    assert scoped.json()["total"] == 1
    assert scoped.json()["items"][0]["state"] == "Andhra Pradesh"

    retained = client.get("/api/v1/projects", params={"apply_pilot_scope": False})
    states = {item["state"] for item in retained.json()["items"]}
    assert "Andhra Pradesh" in states
    assert "Tamil Nadu" in states


def test_pilot_state_is_configurable(client, monkeypatch) -> None:
    monkeypatch.setenv("SARVSAKSHI_PILOT_STATE", "Kerala")
    reset_settings_cache()
    session = get_session_factory()()
    try:
        insert_project(session, internal_project_id="internal:synthetic:scope:ap2")
        insert_project(
            session,
            internal_project_id="internal:synthetic:scope:kl",
            state="Kerala",
            constituency="THIRUVANANTHAPURAM",
        )
        session.commit()
    finally:
        session.close()

    body = client.get("/api/v1/scope").json()
    assert body["current_pilot"] == "Kerala"
    results = client.get("/api/v1/projects")
    assert results.json()["effective_state"] == "Kerala"
    assert results.json()["items"][0]["state"] == "Kerala"
    reset_settings_cache()
