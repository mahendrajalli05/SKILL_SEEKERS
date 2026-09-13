from __future__ import annotations

from datetime import date

from sqlalchemy import inspect, select

from app.db import get_engine, get_session_factory
from app.engines.cost.service import assess_project_cost
from app.engines.time.service import assess_project_time
from app.engines.time.types import TimeMode
from app.evidence.repository import list_project_evidence, row_to_evidence
from app.models.evidence import EvidenceObjectRow
from app.models.project import Project

TANKS = "NA - Construction of water tanks"
SYNTHETIC_LABEL = "SYNTHETIC: evidence-layer unit test (not a government project)"


def _insert_project(session, **overrides: object) -> Project:
    values: dict[str, object] = {
        "internal_project_id": "internal:synthetic:evidence:subject",
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


def test_evidence_tables_have_canonical_columns(client) -> None:
    inspector = inspect(get_engine())
    object_columns = {column["name"] for column in inspector.get_columns("evidence_object")}
    fact_columns = {column["name"] for column in inspector.get_columns("evidence_fact")}
    assert {
        "id",
        "evidence_id",
        "project_id",
        "engine",
        "engine_version",
        "signal_type",
        "finding",
        "score",
        "confidence",
        "source_type",
        "source_ids_json",
        "explanation",
        "data_mode",
        "provenance_json",
        "disposition",
    }.issubset(object_columns)
    assert {"fact_kind", "statement", "key", "value", "source"}.issubset(fact_columns)


def test_api_returns_empty_evidence(client) -> None:
    session = get_session_factory()()
    try:
        subject = _insert_project(session)
        session.commit()
        project_id = subject.id
    finally:
        session.close()

    missing = client.get("/api/v1/projects/999999/evidence")
    assert missing.status_code == 404

    response = client.get(f"/api/v1/projects/{project_id}/evidence")
    assert response.status_code == 200
    body = response.json()
    assert body["project_id"] == project_id
    assert body["items"] == []
    assert "Investigation Priority" in body["note"]


def test_api_returns_persisted_cost_and_time_evidence(client) -> None:
    session = get_session_factory()()
    try:
        subject = _insert_project(session)
        for i in range(8):
            _insert_project(
                session,
                internal_project_id=f"internal:synthetic:evidence:peer:{i}",
                allocation_amount=480_000 + i * 1_000,
            )
        session.commit()
        project_id = subject.id
        assess_project_cost(session, project_id, persist=True)
        assess_project_time(session, project_id, mode=TimeMode.REAL, persist=True)
        stored = session.scalars(
            select(EvidenceObjectRow).where(EvidenceObjectRow.project_id == project_id)
        ).all()
        assert len(stored) == 2
        for row in stored:
            obj = row_to_evidence(row)
            assert obj.evidence_id
            assert obj.provenance.source_ids
            assert obj.provenance.notes
            assert "fraud" not in obj.finding.casefold()
            assert obj.data_mode.value == "SYNTHETIC"
        items = list_project_evidence(session, project_id)
        engines = {item.engine_name for item in items}
        assert engines == {"cost", "time"}
    finally:
        session.close()

    response = client.get(f"/api/v1/projects/{project_id}/evidence")
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    for item in body["items"]:
        assert item["evidence_id"]
        assert item["provenance"]["internal_project_id"]
        assert item["source_ids"]
        assert item["data_mode"] == "SYNTHETIC"
        assert "fraud" not in str(item).casefold()

    cost_only = client.get(f"/api/v1/projects/{project_id}/evidence", params={"engine": "cost"})
    assert cost_only.status_code == 200
    assert len(cost_only.json()["items"]) == 1
    assert cost_only.json()["items"][0]["engine_name"] == "cost"


def test_roundtrip_preserves_source_references(client) -> None:
    session = get_session_factory()()
    try:
        subject = _insert_project(
            session,
            internal_project_id="internal:synthetic:evidence:roundtrip",
        )
        session.commit()
        assess_project_time(session, subject.id, mode=TimeMode.REAL, persist=True)
        row = session.scalars(
            select(EvidenceObjectRow).where(EvidenceObjectRow.project_id == subject.id)
        ).one()
        obj = row_to_evidence(row)
        assert subject.internal_project_id in obj.source_ids
        assert obj.provenance.internal_project_id == subject.internal_project_id
        assert row.provenance_json
        assert row.evidence_id == obj.evidence_id
    finally:
        session.close()
