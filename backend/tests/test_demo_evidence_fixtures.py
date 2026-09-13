"""Demo Evidence Fixtures V1 tests. Controlled HYBRID fixtures only."""

from __future__ import annotations

import json
from datetime import date

from app.db import get_session_factory
from app.demo.constants import CASE_IDS, FIXTURE_LAYER, FIXTURE_SOURCE, internal_project_id_for
from app.demo.evidence_fixtures import ensure_all_demo_evidence, ensure_demo_case_evidence
from app.domain.enums import DataMode, LifecycleStage
from app.engines.fusion_v2.service import assess_project_risk_v2
from app.evidence.repository import list_project_evidence
from app.models.project import Project
from demo_fixtures import insert_all_demo_cases, insert_demo_project


def _blob(value: object) -> str:
    return json.dumps(value, default=str).casefold()


def _seed(session):
    extra = Project(
        internal_project_id="internal:demo-evidence-fixtures-control",
        internal_id_kind="internal_surrogate_hash",
        internal_id_scheme="sarvsakshi_internal_work_v1",
        source_dataset="github_vonter_india-mplads-works_MPLADS.csv",
        is_synthetic=False,
        state="Andhra Pradesh",
        constituency="GUNTUR",
        category="Normal/Others",
        work_description="NA - Control row for REAL unchanged check",
        status="Ongoing",
        lifecycle_stage=LifecycleStage.ONGOING.value,
        allocation_amount=250_000,
        recommended_date=date(2023, 1, 1),
        mp_name="Example MP",
        house="Lok Sabha",
    )
    session.add(extra)
    session.flush()
    rows = insert_all_demo_cases(session)
    session.commit()
    return extra, rows


def test_four_cases_have_traceable_hybrid_evidence(client) -> None:
    session = get_session_factory()()
    try:
        extra, rows = _seed(session)
        extra_id = extra.id
        extra_desc = extra.work_description
        extra_alloc = extra.allocation_amount
        extra_status = extra.status
        extra_evidence = list_project_evidence(session, extra_id)
    finally:
        session.close()

    assert extra_evidence == []
    for case_id in CASE_IDS:
        body = client.get(f"/api/v1/demo-cases/{case_id}", params={"data_mode": "HYBRID"}).json()
        ids = body["available_evidence"]["evidence_ids"]
        assert ids, case_id
        assert all(item.startswith("ev:") for item in ids)
        modes = {item["data_mode"] for item in body["available_evidence"]["items"]}
        assert "HYBRID" in modes or "REAL" in modes
        assert "CONTROLLED PROTOTYPE" in body["demo_notice"] or "controlled prototype" in body["demo_notice"].casefold()
        assert body["demo_evidence_fixtures"]["fixture_layer"] == FIXTURE_LAYER
        assert body["demo_evidence_fixtures"]["official_mplads_evidence"] is False
        assert "fraud confirmed" not in _blob(body)
        assert body["automatic_sanction"] is False
        assert body["automatic_payment"] is False
        assert body["pfms_integrated"] is False
        fused = set(body["risk_fusion_v2"]["evidence_ids"] or [])
        assert fused <= set(ids)

    session = get_session_factory()()
    try:
        control = session.get(Project, extra_id)
        assert control is not None
        assert control.work_description == extra_desc
        assert control.allocation_amount == extra_alloc
        assert control.status == extra_status
        assert list_project_evidence(session, extra_id) == []
        for case_id, project in rows.items():
            reloaded = session.get(Project, project.id)
            assert reloaded is not None
            assert reloaded.internal_project_id == internal_project_id_for(case_id)
            assert reloaded.is_synthetic is False
    finally:
        session.close()


def test_ghost_has_image_geo_and_v2_consumes_it(client) -> None:
    session = get_session_factory()()
    try:
        _seed(session)
    finally:
        session.close()
    body = client.get("/api/v1/demo-cases/GHOST", params={"data_mode": "HYBRID"}).json()
    engines = {item["engine_name"] for item in body["available_evidence"]["items"]}
    assert "image" in engines
    assert "geo" in engines
    assert "forensics" in engines or "satellite" in engines
    assert body["risk_fusion_v2"]["investigation_priority"] is not None
    assert body["risk_fusion_v2"]["formula_unchanged"] is True


def test_overbill_has_financial_evidence(client) -> None:
    session = get_session_factory()()
    try:
        _seed(session)
    finally:
        session.close()
    body = client.get("/api/v1/demo-cases/OVERBILL", params={"data_mode": "HYBRID"}).json()
    engines = {item["engine_name"] for item in body["available_evidence"]["items"]}
    assert "compliance" in engines
    assert "pce" in engines or "milestone" in engines
    assert "cost" in engines
    assert body["available_claim"]["claimed_expenditure"] is not None


def test_stuck_has_time_and_milestone_evidence(client) -> None:
    session = get_session_factory()()
    try:
        _seed(session)
    finally:
        session.close()
    body = client.get("/api/v1/demo-cases/STUCK", params={"data_mode": "HYBRID"}).json()
    engines = {item["engine_name"] for item in body["available_evidence"]["items"]}
    assert "time" in engines
    assert "milestone" in engines
    assert body["available_claim"]["claimed_progress_percent"] is not None


def test_clean_has_supporting_evidence_and_is_not_forced_to_zero(client) -> None:
    session = get_session_factory()()
    try:
        rows = insert_all_demo_cases(session)
        session.commit()
        clean_id = rows["CLEAN"].id
        computed = assess_project_risk_v2(session, clean_id, data_mode=DataMode.HYBRID, persist=False)
    finally:
        session.close()
    body = client.get("/api/v1/demo-cases/CLEAN", params={"data_mode": "HYBRID"}).json()
    engines = {item["engine_name"] for item in body["available_evidence"]["items"]}
    assert "image" in engines or "citizen" in engines or "geo" in engines
    priority = body["risk_fusion_v2"]["investigation_priority"]
    assert priority == computed.investigation_priority
    assert priority is not None


def test_ensure_is_idempotent_and_skips_missing_projects(client) -> None:
    session = get_session_factory()()
    try:
        missing = ensure_all_demo_evidence(session)
        assert missing["official_mplads_evidence"] is False
        assert all(item["available"] is False for item in missing["cases"].values())
        project = insert_demo_project(session, "GHOST")
        first = ensure_demo_case_evidence(session, project, "GHOST")
        second = ensure_demo_case_evidence(session, project, "GHOST")
        session.commit()
        assert first["applied"] is True
        assert second["applied"] is False
        assert first["evidence_ids"]
        assert set(second["evidence_ids"]) == set(first["evidence_ids"])
    finally:
        session.close()
    body = client.get("/api/v1/demo-cases/GHOST", params={"data_mode": "HYBRID"}).json()
    assert body["available_evidence"]["count"] >= 1
    from app.engines.image.repository import list_project_photos

    session = get_session_factory()()
    try:
        sources = {photo.source for photo in list_project_photos(session, body["project_id"])}
        assert FIXTURE_SOURCE in sources
    finally:
        session.close()


def test_no_payment_or_fraud_wording_in_fixtures(client) -> None:
    session = get_session_factory()()
    try:
        insert_all_demo_cases(session)
        session.commit()
    finally:
        session.close()
    for case_id in CASE_IDS:
        body = client.get(f"/api/v1/demo-cases/{case_id}", params={"data_mode": "HYBRID"}).json()
        blob = _blob(body)
        assert "fraud confirmed" not in blob
        assert '"automatic_sanction": true' not in json.dumps(body).casefold()
        assert '"automatic_payment": true' not in json.dumps(body).casefold()
        assert body["pfms_integrated"] is False
        for item in body["available_evidence"]["items"]:
            assert "fraud confirmed" not in str(item.get("finding") or "").casefold()
            assert "fraud confirmed" not in str(item.get("explanation") or "").casefold()
