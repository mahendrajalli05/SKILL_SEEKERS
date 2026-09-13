from __future__ import annotations

from datetime import date

import pytest

from app.db import get_session_factory
from app.domain.enums import DataMode, EvidenceDisposition
from app.engines.fusion.constants import GOVERNANCE_NOTE
from app.evidence.repository import persist_evidence_object
from app.models.project import Project
from fusion_fixtures import make_signal_evidence

TANKS = "NA - Construction of water tanks"
SYNTHETIC_LABEL = "SYNTHETIC: risk-fusion unit test (not a government project)"


def _insert_project(session, **overrides: object) -> Project:
    values: dict[str, object] = {
        "internal_project_id": "internal:synthetic:fusion:subject",
        "internal_id_kind": "internal_surrogate_hash",
        "internal_id_scheme": "sarvsakshi_internal_work_v1",
        "source_dataset": "github_vonter_india-mplads-works_MPLADS.csv",
        "is_synthetic": True,
        "synthetic_label": SYNTHETIC_LABEL,
        "lifecycle_stage": "FUTURE",
        "state": "Andhra Pradesh",
        "constituency": "KURNOOL",
        "category": "Normal/Others",
        "work_description": TANKS,
        "allocation_amount": 500_000,
        "recommended_date": date(2023, 6, 1),
        "status": "Unsanctioned",
    }
    values.update(overrides)
    row = Project(**values)
    session.add(row)
    session.flush()
    return row


def test_risk_api_missing_project(client) -> None:
    response = client.get("/api/v1/projects/999999/risk")
    assert response.status_code == 404


def test_risk_api_with_no_evidence(client) -> None:
    session = get_session_factory()()
    try:
        subject = _insert_project(session)
        session.commit()
        project_id = subject.id
    finally:
        session.close()

    response = client.get(f"/api/v1/projects/{project_id}/risk")
    assert response.status_code == 200
    body = response.json()
    assert body["investigation_priority"] == 0
    assert body["evidence_confidence"] == 0
    assert body["explanation_type"] == "INSUFFICIENT_EVIDENCE"
    assert body["recommended_action"] == "MONITOR"
    assert "fraud_probability" not in body
    assert "fraud_score" not in body
    assert "unavailable_signals" in body
    assert "evidence_ids" in body
    assert "data_mode" in body
    assert GOVERNANCE_NOTE.split(".")[0] in body["note"] or "not a fraud" in body["note"].lower()


def test_risk_api_returns_fused_result(client) -> None:
    session = get_session_factory()()
    try:
        subject = _insert_project(
            session,
            internal_project_id="internal:synthetic:fusion:api",
        )
        session.commit()
        project_id = subject.id
        cost = make_signal_evidence(
            "cost",
            project_id=project_id,
            score=100,
            disposition=EvidenceDisposition.WHY_FLAGGED,
            data_mode=DataMode.SYNTHETIC,
        )
        overlap = make_signal_evidence(
            "overlap",
            project_id=project_id,
            score=100,
            disposition=EvidenceDisposition.WHY_FLAGGED,
            data_mode=DataMode.SYNTHETIC,
        )
        persist_evidence_object(session, cost)
        persist_evidence_object(session, overlap)
        session.commit()
    finally:
        session.close()

    response = client.get(
        f"/api/v1/projects/{project_id}/risk",
        params={"data_mode": "SYNTHETIC"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["investigation_priority"] == 57
    assert body["investigation_priority_0_100"] == pytest.approx(57.1)
    assert body["raw_risk"] == pytest.approx(40)
    assert body["available_signal_weight"] == pytest.approx(0.40)
    assert body["unavailable_signal_weight"] == pytest.approx(0.30)
    assert body["evidence_coverage"] == pytest.approx(0.40 / 0.70, rel=1e-3)
    assert body["recommended_action"] == "INSPECT"
    assert body["data_mode"] == "SYNTHETIC"
    assert body["contributing_signals"]
    ids = {item["signal_id"] for item in body["contributing_signals"]}
    assert ids == {"cost", "overlap"}
    unavailable = {item["signal_id"] for item in body["unavailable_signals"]}
    assert "schedule" in unavailable
    assert "relationship_graph" in unavailable
    assert body["evidence_ids"]
    assert "this project is fraudulent" not in body["explanation"].casefold()
    assert "fraud_probability" not in body
    assert "Prototype weights" in body["weight_note"]
