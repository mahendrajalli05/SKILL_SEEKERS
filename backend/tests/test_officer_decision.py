from __future__ import annotations

from datetime import date

from app.db import get_session_factory
from app.domain.enums import DataMode, EvidenceDisposition
from app.engines.fusion.service import assess_project_risk
from app.evidence.repository import persist_evidence_object
from app.models.fusion import FusionScore
from app.models.project import Project
from fusion_fixtures import make_signal_evidence
from sqlalchemy import func, select

from app.models.audit import AuditEvent
from app.models.review import OfficerDecision

SYNTHETIC_LABEL = "SYNTHETIC: officer-decision unit test (not a government project)"


def _insert(session, **overrides: object) -> Project:
    values: dict[str, object] = {
        "internal_project_id": "internal:synthetic:decision:subject",
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


def test_officer_decision_is_persisted_and_does_not_change_scores(client) -> None:
    session = get_session_factory()()
    try:
        subject = _insert(session)
        cost = make_signal_evidence(
            "cost",
            project_id=subject.id,
            score=100,
            disposition=EvidenceDisposition.WHY_FLAGGED,
            data_mode=DataMode.SYNTHETIC,
        )
        persist_evidence_object(session, cost)
        session.commit()
        project_id = subject.id
        fused = assess_project_risk(session, project_id, data_mode=DataMode.SYNTHETIC, persist=True)
        before_priority = fused.investigation_priority
        before_confidence = fused.evidence_confidence
    finally:
        session.close()

    created = client.post(
        f"/api/v1/projects/{project_id}/decisions",
        json={
            "decision_type": "confirm_concern",
            "reason": "Documents and comparables need field inspection.",
            "actor_role": "officer",
        },
    )
    assert created.status_code == 200
    body = created.json()
    assert body["decision_type"] == "confirm_concern"
    assert body["scores_unchanged"] is True
    assert "fraud" not in str(body).casefold()

    listed = client.get(f"/api/v1/projects/{project_id}/decisions")
    assert listed.status_code == 200
    listed_body = listed.json()
    assert listed_body["items"][0]["decision_type"] == "confirm_concern"
    assert "confirm_concern" in listed_body["allowed_actions"]
    assert "fraud_confirmed" in listed_body["disallowed_actions"]
    assert "legal fraud" in listed_body["note"].casefold()

    session = get_session_factory()()
    try:
        fusion = session.scalars(select(FusionScore).where(FusionScore.project_id == project_id)).one()
        assert fusion.investigation_priority == before_priority
        assert fusion.evidence_confidence == before_confidence
        decisions = session.scalars(select(func.count()).select_from(OfficerDecision)).one()
        audits = session.scalars(
            select(func.count()).select_from(AuditEvent).where(AuditEvent.action == "officer_decision")
        ).one()
        assert decisions == 1
        assert audits == 1
    finally:
        session.close()


def test_officer_actions_cover_mvp_set(client) -> None:
    session = get_session_factory()()
    try:
        subject = _insert(session, internal_project_id="internal:synthetic:decision:actions")
        session.commit()
        project_id = subject.id
    finally:
        session.close()

    for action in ("confirm_concern", "dismiss", "need_more_info"):
        response = client.post(
            f"/api/v1/projects/{project_id}/decisions",
            json={"decision_type": action, "reason": "Recorded for prototype review."},
        )
        assert response.status_code == 200
        assert response.json()["decision_type"] == action


def test_rejects_fraud_confirmed_wording(client) -> None:
    session = get_session_factory()()
    try:
        subject = _insert(session, internal_project_id="internal:synthetic:decision:fraud")
        session.commit()
        project_id = subject.id
    finally:
        session.close()

    response = client.post(
        f"/api/v1/projects/{project_id}/decisions",
        json={"decision_type": "fraud_confirmed", "reason": "not used"},
    )
    assert response.status_code == 422
    assert "fraud" in str(response.json()).casefold()

    note_rejected = client.post(
        f"/api/v1/projects/{project_id}/decisions",
        json={"decision_type": "confirm_concern", "reason": "This is fraud confirmed."},
    )
    assert note_rejected.status_code == 422
