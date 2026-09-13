"""Final End-to-End Demo Cases V1 tests. Controlled fixtures only."""

from __future__ import annotations

import json

from app.db import get_session_factory

from app.demo.catalog import list_catalog, normalize_case_id
from app.demo.constants import (
    CASE_IDS,
    DEMO_NOTICE,
    assert_fusion_v2_unchanged,
    internal_project_id_for,
)
from app.engines.fusion_v2.constants import ENGINE_VERSION as FUSION_V2_VERSION
from app.engines.fusion_v2.constants import GROUP_WEIGHTS
from app.engines.fusion_v2.service import assess_project_risk_v2
from app.engines.lifecycle.constants import FROZEN_FUSION_V2_VERSION, FROZEN_FUSION_V2_WEIGHTS
from app.models.fusion_v2 import FusionScoreV2
from demo_fixtures import insert_all_demo_cases, insert_demo_project
from sqlalchemy import select


def _seed(session):
    rows = insert_all_demo_cases(session)
    session.commit()
    return {key: row.id for key, row in rows.items()}


def _blob(value: object) -> str:
    return json.dumps(value, default=str).casefold()


def test_fusion_v2_remains_frozen() -> None:
    assert_fusion_v2_unchanged()
    assert FUSION_V2_VERSION == FROZEN_FUSION_V2_VERSION
    assert GROUP_WEIGHTS == FROZEN_FUSION_V2_WEIGHTS


def test_catalog_uses_existing_internal_ids() -> None:
    assert CASE_IDS == ("GHOST", "OVERBILL", "STUCK", "CLEAN")
    assert normalize_case_id("over-bill") == "OVERBILL"
    catalog = {item["case_id"]: item for item in list_catalog()}
    for case_id in CASE_IDS:
        assert catalog[case_id]["internal_project_id"] == internal_project_id_for(case_id)
        assert "fraud" not in catalog[case_id]["short_description"].casefold()


def test_unknown_case_is_404(client) -> None:
    response = client.get("/api/v1/demo-cases/unknown")
    assert response.status_code == 404


def test_list_marks_missing_projects(client) -> None:
    body = client.get("/api/v1/demo-cases").json()
    assert body["count"] == 4
    assert body["fusion_v2_unchanged"] is True
    assert body["automatic_sanction"] is False
    assert DEMO_NOTICE in body["demo_notice"]
    assert {item["case_id"] for item in body["items"]} == set(CASE_IDS)
    assert all(item["available"] is False for item in body["items"])


def test_four_cases_end_to_end(client) -> None:
    session = get_session_factory()()
    try:
        ids = _seed(session)
    finally:
        session.close()

    listing = client.get("/api/v1/demo-cases").json()
    assert all(item["available"] is True for item in listing["items"])
    assert listing["journey_steps"][:5] == ["PROJECT", "PASSPORT", "LIFECYCLE", "PLAN", "CLAIM"]

    expected_lifecycle = {
        "GHOST": "COMPLETED",
        "OVERBILL": "COMPLETED",
        "STUCK": "ONGOING",
        "CLEAN": "FUTURE",
    }
    for case_id in CASE_IDS:
        response = client.get(f"/api/v1/demo-cases/{case_id}", params={"data_mode": "HYBRID"})
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["case_id"] == case_id
        assert body["project_id"] == ids[case_id]
        assert body["internal_project_id"] == internal_project_id_for(case_id)
        assert body["scheme_id"]
        assert body["lifecycle_state"] == expected_lifecycle[case_id]
        assert body["data_mode"] == "HYBRID"
        assert body["data_reliability"] in {"HYBRID", "REAL", "SYNTHETIC"}
        assert DEMO_NOTICE in body["demo_notice"]
        assert body["fusion_v2_unchanged"] is True
        assert body["automatic_sanction"] is False
        assert body["automatic_payment"] is False
        assert body["fraud_conclusion"] is False
        assert body["pfms_integrated"] is False
        assert body["copilot"]["hardcoded_answers"] is False
        assert body["copilot"]["grounded_retrieval"] is True
        assert body["suggested_questions"]
        assert body["risk_fusion_v2"]["formula_unchanged"] is True
        assert body["available_evidence"]["evidence_ids"]
        assert body["available_plan"]["plan_recorded"] is True
        assert body["available_claim"]["claim_recorded"] is True
        assert "DEMO" in (body["demo_evidence_fixtures"]["labels"] or [])
        assert "SYNTHETIC" in body["demo_evidence_fixtures"]["labels"]
        assert "CONTROLLED PROTOTYPE" in body["demo_evidence_fixtures"]["labels"]
        assert body["demo_evidence_fixtures"]["official_mplads_evidence"] is False
        fused_ids = set(body["risk_fusion_v2"]["evidence_ids"] or [])
        stored_ids = set(body["available_evidence"]["evidence_ids"])
        assert stored_ids
        assert fused_ids <= stored_ids
        summary = body["final_case_summary"]
        assert summary["project"]["scheme_id"] == body["scheme_id"]
        assert summary["lifecycle"] == expected_lifecycle[case_id]
        assert summary["evidence"]
        assert summary["scores_mutated"] is False
        assert "fraud confirmed" not in _blob(body)
        assert '"automatic_sanction": true' not in json.dumps(body).casefold()
        assert '"fraud_conclusion": true' not in json.dumps(body).casefold()
        search = client.get(
            "/api/v1/projects",
            params={"internal_project_id": body["internal_project_id"], "apply_pilot_scope": "false"},
        ).json()
        assert search["total"] >= 1
        assert search["items"][0]["id"] == body["project_id"]
        passport = client.get(f"/api/v1/projects/{body['project_id']}", params={"mode": "hybrid"})
        assert passport.status_code == 200
        lifecycle = client.get(
            f"/api/v2/projects/{body['project_id']}/lifecycle",
            params={"data_mode": "HYBRID"},
        )
        assert lifecycle.status_code == 200
        risk = client.get(
            f"/api/v2/projects/{body['project_id']}/risk",
            params={"data_mode": "HYBRID"},
        )
        assert risk.status_code == 200
        evidence = client.get(f"/api/v1/projects/{body['project_id']}/evidence")
        assert evidence.status_code == 200
        pce = client.get(
            f"/api/v1/projects/{body['project_id']}/verification",
            params={"data_mode": "HYBRID"},
        )
        assert pce.status_code == 200


def test_ghost_location_and_copilot(client) -> None:
    session = get_session_factory()()
    try:
        ids = _seed(session)
    finally:
        session.close()
    body = client.get("/api/v1/demo-cases/GHOST", params={"data_mode": "HYBRID"}).json()
    engines = {item["engine_name"] for item in body["available_evidence"]["items"]}
    assert "geo" in engines or any("geo" in str(item["engine_name"]) for item in body["available_evidence"]["items"])
    assert body["geospatial"] is not None
    assert body["images"] is not None
    assert body["satellite"] is not None
    assert "inspect" in " ".join(body["suggested_questions"]).casefold()
    chat = client.post(
        f"/api/v1/projects/{ids['GHOST']}/copilot/chat",
        json={
            "question": body["suggested_questions"][0],
            "data_mode": "HYBRID",
        },
    )
    assert chat.status_code == 200, chat.text
    answer = chat.json()
    assert answer["evidence_ids"]
    assert "fraud confirmed" not in answer["answer"].casefold()
    assert answer["used_llm"] is False


def test_overbill_financial_modules(client) -> None:
    session = get_session_factory()()
    try:
        _seed(session)
    finally:
        session.close()
    body = client.get("/api/v1/demo-cases/OVERBILL", params={"data_mode": "HYBRID"}).json()
    engines = {item["engine_name"] for item in body["available_evidence"]["items"]}
    assert "cost" in engines
    assert "compliance" in engines
    assert body["pce"] is not None
    assert body["milestone"] is not None
    assert body["available_plan"]["plan_recorded"] is True
    assert "financial" in " ".join(body["suggested_questions"]).casefold()
    chat = client.post(
        f"/api/v1/projects/{body['project_id']}/copilot/chat",
        json={"question": "What evidence supports the financial concern?", "data_mode": "HYBRID"},
    )
    assert chat.status_code == 200, chat.text
    answer = chat.json()
    assert answer["evidence_ids"]
    assert "fraud confirmed" not in answer["answer"].casefold()
    assert answer["used_llm"] is False


def test_stuck_schedule_and_milestone(client) -> None:
    session = get_session_factory()()
    try:
        _seed(session)
    finally:
        session.close()
    body = client.get("/api/v1/demo-cases/STUCK", params={"data_mode": "HYBRID"}).json()
    engines = {item["engine_name"] for item in body["available_evidence"]["items"]}
    assert "time" in engines or "milestone" in engines
    assert body["lifecycle_state"] == "ONGOING"
    assert body["milestone"] is not None
    assert body["pce"] is not None
    assert "HOLD" in body["officer_actions"] or "INSPECT" in body["officer_actions"]
    chat = client.post(
        f"/api/v1/projects/{body['project_id']}/copilot/chat",
        json={"question": "Why is this milestone being held?", "data_mode": "HYBRID"},
    )
    assert chat.status_code == 200, chat.text
    answer = chat.json()
    assert "fraud confirmed" not in answer["answer"].casefold()
    assert answer["used_llm"] is False


def test_clean_is_not_forced_to_zero(client) -> None:
    session = get_session_factory()()
    try:
        ids = _seed(session)
    finally:
        session.close()
    body = client.get("/api/v1/demo-cases/CLEAN", params={"data_mode": "HYBRID"}).json()
    assert body["lifecycle_state"] == "FUTURE"
    priority = body["risk_fusion_v2"]["investigation_priority"]
    assert priority is not None
    session = get_session_factory()()
    try:
        computed = assess_project_risk_v2(session, ids["CLEAN"], data_mode="HYBRID", persist=False)
        assert computed.investigation_priority == priority
    finally:
        session.close()
        assert body["pce"] is not None
        engines = {item["engine_name"] for item in body["available_evidence"]["items"]}
        assert "citizen" in engines or "image" in engines
        assert "not escalated" in " ".join(body["suggested_questions"]).casefold()
        chat = client.post(
            f"/api/v1/projects/{ids['CLEAN']}/copilot/chat",
            json={"question": "Why was this project not escalated?", "data_mode": "HYBRID"},
        )
        assert chat.status_code == 200, chat.text
        answer = chat.json()
        assert answer["evidence_ids"]
        assert "fraud confirmed" not in answer["answer"].casefold()
        assert "automatic sanction" not in answer["answer"].casefold()
        assert answer["used_llm"] is False


def test_officer_decision_does_not_mutate_scores(client) -> None:
    session = get_session_factory()()
    try:
        ids = _seed(session)
        ghost_id = ids["GHOST"]
        before = assess_project_risk_v2(session, ghost_id, data_mode="HYBRID", persist=True)
        session.commit()
        before_ip = before.investigation_priority
        before_ec = before.evidence_confidence
    finally:
        session.close()

    decision = client.post(
        f"/api/v1/projects/{ghost_id}/decisions",
        json={"decision_type": "confirm_concern", "reason": "Location evidence requires inspection."},
    )
    assert decision.status_code == 200, decision.text
    payload = decision.json()
    assert payload["scores_unchanged"] is True

    after = client.get("/api/v1/demo-cases/GHOST", params={"data_mode": "HYBRID"}).json()
    assert after["risk_fusion_v2"]["investigation_priority"] == before_ip
    assert after["risk_fusion_v2"]["evidence_confidence"] == before_ec
    assert after["officer_decision"] in {"confirm_concern", "CONFIRM CONCERN"}
    assert after["final_case_summary"]["officer_decision"] in {"confirm_concern", "CONFIRM CONCERN"}
    assert after["automatic_sanction"] is False

    session = get_session_factory()()
    try:
        stored = session.scalars(select(FusionScoreV2).where(FusionScoreV2.project_id == ghost_id)).all()
        assert stored
        assert stored[0].investigation_priority == before_ip
    finally:
        session.close()


def test_missing_loaded_project_is_404(client) -> None:
    session = get_session_factory()()
    try:
        insert_demo_project(session, "CLEAN")
        session.commit()
    finally:
        session.close()
    response = client.get("/api/v1/demo-cases/GHOST")
    assert response.status_code == 404
