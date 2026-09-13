from __future__ import annotations

from sqlalchemy import inspect, select

from app.db import get_engine, get_session_factory
from app.domain.enums import DataMode, EvidenceDisposition, SignalType
from app.engines.fusion.service import assess_project_risk
from app.engines.milestone.constants import ENGINE_VERSION, GOVERNANCE_NOTE, HYBRID_NOTICE
from app.evidence.repository import persist_evidence_object
from app.models.audit import AuditEvent
from app.models.fusion import FusionScore
from app.models.milestone import MilestoneDecision
from app.models.project import Project
from fusion_fixtures import make_signal_evidence
from milestone_fixtures import insert_project, make_engine_evidence

PLAN_BODY = {
    "sanctioned_scope": "Community hall 2,000 sq.ft",
    "budget_estimate": 2_000_000,
    "dimensions_value": 2000,
    "dimensions_unit": "sq.ft",
    "milestone_amount": 2_000_000,
    "source": "officer_recorded",
    "data_mode": "REAL",
}


def _create(internal_project_id: str, **overrides: object) -> int:
    session = get_session_factory()()
    try:
        row = insert_project(session, internal_project_id=internal_project_id, **overrides)
        session.commit()
        return row.id
    finally:
        session.close()


def _seed_consistent(client, project_id: int, data_mode: str = "REAL") -> None:
    body = dict(PLAN_BODY)
    body["data_mode"] = data_mode
    assert client.post(f"/api/v1/projects/{project_id}/plan", json=body).status_code == 200
    assert client.post(
        f"/api/v1/projects/{project_id}/claims",
        json={
            "claimed_progress_percent": 100,
            "claimed_expenditure": 1_900_000,
            "claimed_completion_state": "completed",
            "claimed_quantity": 1950,
            "claimed_quantity_unit": "sq.ft",
            "milestone_claimed": "M1",
            "claimant_source": "implementing_agency",
            "data_mode": data_mode,
        },
    ).status_code == 200
    assert client.post(
        f"/api/v1/projects/{project_id}/evidence",
        json={
            "document_type": "pdf",
            "filename": "completion.pdf",
            "observed_quantity": 1940,
            "observed_quantity_unit": "sq.ft",
            "observed_expenditure": 1_900_000,
            "source": "officer_upload",
            "data_mode": data_mode,
        },
    ).status_code == 200


def _seed_mismatch(client, project_id: int) -> None:
    assert client.post(f"/api/v1/projects/{project_id}/plan", json=PLAN_BODY).status_code == 200
    assert client.post(
        f"/api/v1/projects/{project_id}/claims",
        json={
            "claimed_progress_percent": 100,
            "claimed_expenditure": 2_000_000,
            "claimed_completion_state": "completed",
            "claimed_quantity": 2000,
            "claimed_quantity_unit": "sq.ft",
            "data_mode": "REAL",
        },
    ).status_code == 200
    assert client.post(
        f"/api/v1/projects/{project_id}/evidence",
        json={
            "document_type": "image",
            "filename": "site.jpg",
            "observed_quantity": 800,
            "observed_quantity_unit": "sq.ft",
            "data_mode": "REAL",
        },
    ).status_code == 200


def test_milestone_tables_exist(client) -> None:
    inspector = inspect(get_engine())
    names = set(inspector.get_table_names())
    assert "milestone" in names
    assert "milestone_decision" in names
    cols = {column["name"] for column in inspector.get_columns("milestone")}
    for name in (
        "milestone_number",
        "milestone_name",
        "planned_amount",
        "cumulative_amount",
        "target_date",
        "completion_claimed",
        "claimed_progress",
        "status",
        "data_mode",
        "provenance_json",
    ):
        assert name in cols


def test_create_ordering_status_and_amounts(client) -> None:
    pid = _create("internal:milestone:api:order")
    first = client.post(
        f"/api/v1/projects/{pid}/milestones",
        json={"milestone_number": 1, "planned_amount": 100_000, "data_mode": "REAL"},
    )
    second = client.post(
        f"/api/v1/projects/{pid}/milestones",
        json={"milestone_number": 2, "planned_amount": 150_000, "data_mode": "REAL"},
    )
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json()["status"] == "PLANNED"
    assert first.json()["cumulative_amount"] == 100_000
    assert second.json()["cumulative_amount"] == 250_000
    assert second.json()["remaining_planned_amount"] == 0
    listed = client.get(f"/api/v1/projects/{pid}/milestones", params={"data_mode": "REAL"})
    assert listed.status_code == 200
    body = listed.json()
    numbers = [item["milestone_number"] for item in body["items"]]
    assert numbers == [1, 2]
    assert body["current_milestone_id"] == first.json()["milestone_id"]
    assert body["timeline"][-1]["slot"] == "COMPLETION"
    assert body["funds_released"] is False
    assert body["automatic_sanction"] is False
    assert GOVERNANCE_NOTE.split(".")[0] in body["governance_note"]
    duplicate = client.post(
        f"/api/v1/projects/{pid}/milestones",
        json={"milestone_number": 1, "planned_amount": 10, "data_mode": "REAL"},
    )
    assert duplicate.status_code == 422


def test_case_proceed(client) -> None:
    pid = _create("internal:milestone:api:proceed")
    _seed_consistent(client, pid)
    created = client.post(
        f"/api/v1/projects/{pid}/milestones",
        json={
            "milestone_number": 1,
            "milestone_name": "M1",
            "planned_amount": 2_000_000,
            "claimed_progress": 100,
            "completion_claimed": True,
            "data_mode": "REAL",
        },
    )
    assert created.status_code == 200, created.text
    mid = created.json()["milestone_id"]
    assessed = client.post(f"/api/v1/milestones/{mid}/assess", params={"data_mode": "REAL"})
    assert assessed.status_code == 200, assessed.text
    body = assessed.json()
    assert body["recommendation"] == "PROCEED"
    assert body["evidence_status"] == "SUPPORTED"
    assert body["assessment"]["pce_result"] == "CONSISTENT"
    assert "fraud" not in body["assessment"]["explanation"].casefold()
    assert body["funds_released"] is False
    fetched = client.get(f"/api/v1/milestones/{mid}")
    assert fetched.status_code == 200
    assert fetched.json()["recommendation"] == "PROCEED"


def test_case_hold(client) -> None:
    pid = _create("internal:milestone:api:hold")
    _seed_mismatch(client, pid)
    created = client.post(
        f"/api/v1/projects/{pid}/milestones",
        json={
            "milestone_number": 1,
            "claimed_progress": 100,
            "completion_claimed": True,
            "planned_amount": 2_000_000,
            "data_mode": "REAL",
        },
    ).json()
    body = client.post(
        f"/api/v1/milestones/{created['milestone_id']}/assess",
        params={"data_mode": "REAL"},
    ).json()
    assert body["recommendation"] == "HOLD"
    assert body["assessment"]["pce_result"] == "MISMATCH"
    assert body["assessment"]["conflicting_evidence"]


def test_case_inspect(client) -> None:
    pid = _create("internal:milestone:api:inspect")
    _seed_mismatch(client, pid)
    session = get_session_factory()()
    try:
        project = session.get(Project, pid)
        assert project is not None
        geo = make_engine_evidence(
            engine="geo",
            engine_version="geospatial-consistency-v1",
            signal_type=SignalType.GEOSPATIAL_LOCATION_MISMATCH,
            project_id=pid,
            internal_id=project.internal_project_id,
            disposition=EvidenceDisposition.WHY_FLAGGED,
            finding="Uploaded image GPS is outside the 500 metre prototype threshold.",
        )
        image = make_engine_evidence(
            engine="image",
            engine_version="image-evidence-v1",
            signal_type=SignalType.IMAGE_POTENTIAL_REUSE,
            project_id=pid,
            internal_id=project.internal_project_id,
            disposition=EvidenceDisposition.WHY_FLAGGED,
            finding="Potential visual reuse was detected against a stored image.",
        )
        persist_evidence_object(session, geo)
        persist_evidence_object(session, image)
        session.commit()
    finally:
        session.close()
    created = client.post(
        f"/api/v1/projects/{pid}/milestones",
        json={"milestone_number": 1, "claimed_progress": 100, "completion_claimed": True, "data_mode": "REAL"},
    ).json()
    body = client.post(
        f"/api/v1/milestones/{created['milestone_id']}/assess",
        params={"data_mode": "REAL"},
    ).json()
    assert body["recommendation"] == "INSPECT"
    assert "geo_mismatch" in body["assessment"]["independent_concerns"]
    assert "image_reuse" in body["assessment"]["independent_concerns"]


def test_case_inconclusive_and_real_missing_finance(client) -> None:
    pid = _create("internal:milestone:api:inconclusive")
    created = client.post(
        f"/api/v1/projects/{pid}/milestones",
        json={"milestone_number": 1, "data_mode": "REAL"},
    ).json()
    body = client.post(
        f"/api/v1/milestones/{created['milestone_id']}/assess",
        params={"data_mode": "REAL"},
    ).json()
    assert body["recommendation"] == "INCONCLUSIVE"
    assert body["amounts"]["claimed_expenditure"] is None
    assert body["amounts"]["claimed_expenditure_available"] is False
    assert "unavailable" in (body["amounts"]["note"] or "").casefold()
    listed = client.get(f"/api/v1/projects/{pid}/milestones", params={"data_mode": "REAL"}).json()
    assert listed["hybrid_notice"] is None


def test_case_hybrid_synthetic_labels(client) -> None:
    pid = _create("internal:milestone:api:hybrid")
    created = client.post(
        f"/api/v1/projects/{pid}/milestones",
        json={
            "milestone_number": 2,
            "planned_amount": 56_783,
            "claimed_progress": 40,
            "claimed_expenditure": 40_000,
            "synthetic": True,
            "data_mode": "HYBRID",
        },
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["data_mode"] == "HYBRID"
    assert body["synthetic"] is True
    assert body["hybrid_notice"] == HYBRID_NOTICE
    assert "SYNTHETIC" in str(body["provenance"]).upper() or body["synthetic"] is True
    listed_real = client.get(f"/api/v1/projects/{pid}/milestones", params={"data_mode": "REAL"}).json()
    assert listed_real["items"] == []
    listed_hybrid = client.get(f"/api/v1/projects/{pid}/milestones", params={"data_mode": "HYBRID"}).json()
    assert listed_hybrid["items"]
    assert listed_hybrid["hybrid_notice"] == HYBRID_NOTICE


def test_officer_decision_need_more_information_and_score_immutability(client) -> None:
    pid = _create("internal:milestone:api:officer")
    _seed_consistent(client, pid)
    session = get_session_factory()()
    try:
        cost = make_signal_evidence(
            "cost",
            project_id=pid,
            score=40,
            disposition=EvidenceDisposition.WHY_NOT_FLAGGED,
            data_mode=DataMode.REAL,
        )
        persist_evidence_object(session, cost)
        fused = assess_project_risk(session, pid, data_mode=DataMode.REAL, persist=True)
        before_ip = fused.investigation_priority
        before_ec = fused.evidence_confidence
        session.commit()
    finally:
        session.close()
    created = client.post(
        f"/api/v1/projects/{pid}/milestones",
        json={"milestone_number": 1, "claimed_progress": 100, "completion_claimed": True, "data_mode": "REAL"},
    ).json()
    mid = created["milestone_id"]
    assessed = client.post(f"/api/v1/milestones/{mid}/assess", params={"data_mode": "REAL"}).json()
    assert assessed["recommendation"] == "PROCEED"
    decided = client.post(
        f"/api/v1/milestones/{mid}/decision",
        json={"action": "NEED_MORE_INFORMATION", "reason": "Need the completion certificate.", "actor_role": "officer"},
    )
    assert decided.status_code == 200, decided.text
    body = decided.json()
    assert body["officer_action"] == "NEED_MORE_INFORMATION"
    assert body["status"] == "UNDER_REVIEW"
    assert body["recommendation"] == "PROCEED"
    assert body["decisions"][0]["scores_unchanged"] is True
    assert body["funds_released"] is False
    session = get_session_factory()()
    try:
        fusion = session.scalars(select(FusionScore).where(FusionScore.project_id == pid)).first()
        assert fusion is not None
        assert fusion.investigation_priority == before_ip
        assert fusion.evidence_confidence == before_ec
        decisions = session.scalars(select(MilestoneDecision).where(MilestoneDecision.milestone_id == mid)).all()
        assert decisions
        audits = session.scalars(select(AuditEvent).where(AuditEvent.action == "milestone_decision")).all()
        assert audits
    finally:
        session.close()
    hold = client.post(
        f"/api/v1/milestones/{mid}/decision",
        json={"action": "HOLD", "reason": "Wait for the missing certificate."},
    ).json()
    assert hold["officer_action"] == "HOLD"
    assert hold["status"] == "HOLD"
    fraud = client.post(
        f"/api/v1/milestones/{mid}/decision",
        json={"action": "PROCEED", "reason": "This is fraud."},
    )
    assert fraud.status_code == 422


def test_no_payment_or_pfms_routes_and_no_fraud_wording(client) -> None:
    openapi_paths = " ".join(client.app.openapi().get("paths", {})).casefold()
    assert "/api/v1/projects/{project_id}/milestones" in openapi_paths
    assert "/api/v1/milestones/{milestone_id}/assess" in openapi_paths
    assert "/payment" not in openapi_paths
    assert "/pfms" not in openapi_paths
    assert "release-funds" not in openapi_paths
    pid = _create("internal:milestone:api:no-wrongdoing")
    created = client.post(
        f"/api/v1/projects/{pid}/milestones",
        json={"milestone_number": 1, "data_mode": "REAL"},
    ).json()
    assessed = client.post(f"/api/v1/milestones/{created['milestone_id']}/assess").json()
    explanation = str(assessed.get("assessment", {}).get("explanation", "")).casefold()
    assert "fraud" not in explanation
    assert "fraud probability" not in explanation
    assert assessed["funds_released"] is False
    assert assessed["payment_executed"] is False
    assert assessed["pfms_integrated"] is False
    assert assessed["engine_version"] == ENGINE_VERSION
    evidence = client.get(f"/api/v1/projects/{pid}/evidence").json()
    engines = {item["engine_name"] for item in evidence["items"]}
    assert "milestone" in engines


def test_missing_amount_and_progress(client) -> None:
    pid = _create("internal:milestone:api:missing")
    created = client.post(
        f"/api/v1/projects/{pid}/milestones",
        json={"milestone_number": 3, "milestone_name": "M3", "data_mode": "REAL"},
    ).json()
    assert created["planned_amount"] is None
    assert created["cumulative_amount"] is None
    assert created["claimed_progress"] is None
    assessed = client.post(f"/api/v1/milestones/{created['milestone_id']}/assess").json()
    assert assessed["progress"]["claimed_progress_available"] is False
    assert assessed["amounts"]["planned_amount_available"] is False
