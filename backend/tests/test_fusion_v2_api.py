from __future__ import annotations

from datetime import date

from app.db import get_session_factory
from app.domain.enums import DataMode, EvidenceDisposition
from app.engines.fusion.service import assess_project_risk
from app.engines.fusion_v2.constants import ENGINE_VERSION, GOVERNANCE_NOTE
from app.engines.fusion_v2.service import assess_project_risk_v2
from app.evidence.repository import persist_evidence_object
from app.models.fusion import FusionScore
from app.models.project import Project
from fusion_v2_fixtures import make_group_evidence
from sqlalchemy import select


SYNTHETIC_LABEL = "SYNTHETIC: risk-fusion-v2 api test (not a government project)"


def _insert_project(session, **overrides: object) -> Project:
    values: dict[str, object] = {
        "internal_project_id": "internal:synthetic:fusion-v2:api",
        "internal_id_kind": "internal_surrogate_hash",
        "internal_id_scheme": "sarvsakshi_internal_work_v1",
        "source_dataset": "github_vonter_india-mplads-works_MPLADS.csv",
        "is_synthetic": True,
        "synthetic_label": SYNTHETIC_LABEL,
        "lifecycle_stage": "FUTURE",
        "state": "Andhra Pradesh",
        "constituency": "KURNOOL",
        "category": "Normal/Others",
        "work_description": "NA - Construction of water tanks",
        "allocation_amount": 500_000,
        "recommended_date": date(2023, 6, 1),
        "status": "Unsanctioned",
    }
    values.update(overrides)
    row = Project(**values)
    session.add(row)
    session.flush()
    return row


def test_v1_risk_endpoint_remains_available(client) -> None:
    session = get_session_factory()()
    try:
        subject = _insert_project(session, internal_project_id="internal:synthetic:fusion-v2:v1compat")
        session.commit()
        project_id = subject.id
    finally:
        session.close()
    response = client.get(f"/api/v1/projects/{project_id}/risk", params={"data_mode": "SYNTHETIC"})
    assert response.status_code == 200
    body = response.json()
    assert body["engine_version"] == "risk-fusion-v1.1"
    assert "fraud_probability" not in body


def test_v2_risk_api_missing_project(client) -> None:
    response = client.get("/api/v2/projects/999999/risk")
    assert response.status_code == 404


def test_v2_risk_api_returns_fused_result(client) -> None:
    session = get_session_factory()()
    try:
        subject = _insert_project(session)
        session.commit()
        project_id = subject.id
        persist_evidence_object(
            session,
            make_group_evidence(
                "cost",
                project_id=project_id,
                score=100,
                disposition=EvidenceDisposition.WHY_FLAGGED,
                data_mode=DataMode.SYNTHETIC,
            ),
        )
        persist_evidence_object(
            session,
            make_group_evidence(
                "overlap",
                project_id=project_id,
                score=90,
                disposition=EvidenceDisposition.WHY_FLAGGED,
                data_mode=DataMode.SYNTHETIC,
            ),
        )
        session.commit()
    finally:
        session.close()

    response = client.get(
        f"/api/v2/projects/{project_id}/risk",
        params={"data_mode": "SYNTHETIC"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["engine_version"] == ENGINE_VERSION
    assert 0 <= body["investigation_priority"] <= 100
    assert 0 <= body["evidence_confidence"] <= 100
    assert body["data_mode"] == "SYNTHETIC"
    assert "contributing_evidence_groups" in body
    assert "discounted_correlated_evidence" in body
    assert "unavailable_evidence" in body
    assert "conflicting_evidence" in body
    assert "evidence_contribution_breakdown" in body
    assert "evidence_ids" in body
    assert "fraud_probability" not in body
    assert "this project is fraudulent" not in body["explanation"].casefold()
    assert GOVERNANCE_NOTE.split(".")[0] in body["note"]
    assert body["recommended_action"] in {
        "MONITOR",
        "REVIEW",
        "INSPECT",
        "NEED_MORE_INFORMATION",
        "INVESTIGATE",
    }


def test_officer_decision_does_not_change_v2_score(client) -> None:
    session = get_session_factory()()
    try:
        subject = _insert_project(session, internal_project_id="internal:synthetic:fusion-v2:officer")
        persist_evidence_object(
            session,
            make_group_evidence(
                "cost",
                project_id=subject.id,
                score=100,
                disposition=EvidenceDisposition.WHY_FLAGGED,
                data_mode=DataMode.SYNTHETIC,
            ),
        )
        session.commit()
        project_id = subject.id
        v2 = assess_project_risk_v2(session, project_id, data_mode=DataMode.SYNTHETIC, persist=True)
        v1 = assess_project_risk(session, project_id, data_mode=DataMode.SYNTHETIC, persist=True)
        before_v2 = (v2.investigation_priority, v2.evidence_confidence)
        before_v1 = (v1.investigation_priority, v1.evidence_confidence)
    finally:
        session.close()

    created = client.post(
        f"/api/v1/projects/{project_id}/decisions",
        json={
            "decision_type": "confirm_concern",
            "reason": "Documents need field inspection.",
            "actor_role": "officer",
        },
    )
    assert created.status_code == 200
    assert created.json()["scores_unchanged"] is True
    assert "fraud" not in str(created.json()).casefold()

    after = client.get(f"/api/v2/projects/{project_id}/risk", params={"data_mode": "SYNTHETIC"}).json()
    assert after["investigation_priority"] == before_v2[0]
    assert after["evidence_confidence"] == before_v2[1]
    session = get_session_factory()()
    try:
        v1_row = session.scalars(select(FusionScore).where(FusionScore.project_id == project_id)).first()
        assert v1_row is not None
        assert v1_row.investigation_priority == before_v1[0]
        assert v1_row.evidence_confidence == before_v1[1]
    finally:
        session.close()
