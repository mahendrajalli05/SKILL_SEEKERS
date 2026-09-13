from __future__ import annotations

from app.db import get_session_factory
from app.engines.need.constants import ENGINE_VERSION, HIGH_PRIORITY, INCONCLUSIVE, LOW_PRIORITY
from app.engines.need.types import SyntheticNeedImpactEnrichment
from tests.need_test_support import high_need_enrichment, insert_project, low_need_enrichment


def _create(internal_project_id: str, **overrides: object) -> int:
    session = get_session_factory()()
    try:
        row = insert_project(session, internal_project_id=internal_project_id, **overrides)
        session.commit()
        return row.id
    finally:
        session.close()


def _overlay(*items: SyntheticNeedImpactEnrichment) -> dict[str, SyntheticNeedImpactEnrichment]:
    return {item.internal_project_id: item for item in items}


def test_real_mode_need_impact_is_inconclusive(client) -> None:
    pid = _create("internal:need-impact:api-real")
    response = client.get(f"/api/v1/projects/{pid}/need-impact", params={"data_mode": "REAL"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["data_mode"] == "REAL"
    assert body["priority_class"] == INCONCLUSIVE
    assert body["need_score"] is None
    assert body["priority_score"] is None
    assert body["automatic_sanction"] is False
    assert body["sanction_decision"] is None
    assert "not invented" in body["need"]["explanation"].casefold() or "unavailable" in body["need"]["explanation"].casefold()
    assert "fraud" not in body["explanation"].casefold()
    assert "sanction approved" not in body["explanation"].casefold()
    assert body["engine_version"] == ENGINE_VERSION
    assert body["constituency_context"]["used_as_need_score"] is False
    evidence = client.get(f"/api/v1/projects/{pid}/evidence").json()
    engines = {item["engine_name"] for item in evidence["items"]}
    assert "need" in engines


def test_hybrid_mode_uses_labelled_enrichment(client, monkeypatch) -> None:
    internal_id = "internal:need-impact:api-hybrid"
    pid = _create(internal_id)
    lookup = _overlay(high_need_enrichment(internal_id))
    monkeypatch.setattr(
        "app.engines.need.service.enrichment_for",
        lambda internal_project_id, overlay=None, path=None, lookup=lookup: lookup.get(internal_project_id),
    )
    response = client.get(f"/api/v1/projects/{pid}/need-impact", params={"data_mode": "HYBRID"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["data_mode"] == "HYBRID"
    assert body["priority_class"] == HIGH_PRIORITY
    assert body["need_score"] is not None
    assert body["enrichment_label"] == "TEST/SYNTHETIC"
    assert body["automatic_sanction"] is False


def test_rank_budget_and_inconclusive(client, monkeypatch) -> None:
    high_id = "internal:need-impact:rank-high"
    low_id = "internal:need-impact:rank-low"
    real_id = "internal:need-impact:rank-real"
    high_pid = _create(high_id, allocation_amount=3_000_000)
    low_pid = _create(
        low_id,
        allocation_amount=3_000_000,
        category="Normal/Others",
        work_description="Installation of commemorative statue",
    )
    real_pid = _create(real_id, allocation_amount=1_000_000)
    overlay = _overlay(high_need_enrichment(high_id), low_need_enrichment(low_id))
    monkeypatch.setattr(
        "app.engines.need.service.enrichment_for",
        lambda internal_project_id, overlay=None, path=None, lookup=overlay: lookup.get(internal_project_id),
    )
    response = client.post(
        "/api/v1/need-impact/rank",
        json={
            "project_ids": [low_pid, real_pid, high_pid],
            "available_budget": 4_000_000,
            "data_mode": "HYBRID",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["planning_simulation"] is True
    assert body["automatic_sanction"] is False
    assert body["sanction_decision"] is None
    assert [item["project_id"] for item in body["items"]] == [high_pid, low_pid]
    assert body["items"][0]["priority_class"] == HIGH_PRIORITY
    assert body["items"][1]["priority_class"] == LOW_PRIORITY
    assert body["items"][0]["within_hypothetical_budget"] is True
    assert body["items"][1]["within_hypothetical_budget"] is False
    assert body["unranked"][0]["project_id"] == real_pid
    assert body["unranked"][0]["priority_class"] == INCONCLUSIVE
    assert "not a sanction" in body["items"][0]["budget_note"].casefold()


def test_rank_rejects_unknown_project(client) -> None:
    response = client.post("/api/v1/need-impact/rank", json={"project_ids": [999999], "data_mode": "REAL"})
    assert response.status_code == 404


def test_no_sanction_endpoint_exists(client) -> None:
    assert client.post("/api/v1/need-impact/sanction", json={}).status_code == 404
    assert client.post("/api/v1/need-impact/payment", json={}).status_code == 404
