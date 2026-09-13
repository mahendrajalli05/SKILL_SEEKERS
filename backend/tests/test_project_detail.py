from __future__ import annotations

from datetime import date

from app.db import get_session_factory
from app.models.project import Project
from app.scope import HYBRID_DEMO_NOTICE, REAL_DATA_NOTICE, SCHEME_ID_NOTE, UNAVAILABLE_REAL_LABEL
from app.search.availability import TIME_UNAVAILABLE_MESSAGE
from app.search.enrichment_display import SyntheticEnrichmentDisplay

SYNTHETIC_LABEL = "SYNTHETIC: project-detail unit test (not a government project)"


def _insert(session, **overrides: object) -> Project:
    values: dict[str, object] = {
        "internal_project_id": "internal:synthetic:detail:subject",
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
        "mp_name": "Test MP",
        "allocation_amount": 500_000,
        "recommended_date": date(2023, 6, 1),
        "status": "Unsanctioned",
        "ida": "Kurnool_IDA",
        "house": "Lok Sabha",
    }
    values.update(overrides)
    row = Project(**values)
    session.add(row)
    session.flush()
    return row


def test_project_detail_lists_unavailable_fields(client) -> None:
    session = get_session_factory()()
    try:
        row = _insert(session)
        session.commit()
        project_id = row.id
    finally:
        session.close()

    response = client.get(f"/api/v1/projects/{project_id}", params={"mode": "real"})
    assert response.status_code == 200
    body = response.json()
    assert body["internal_project_id"] == "internal:synthetic:detail:subject"
    assert body["scheme_id"]
    assert body["scheme_id"].startswith("SVK-AP-")
    assert SCHEME_ID_NOTE in body["scheme_id_note"]
    assert body["internal_id_kind"] == "internal_surrogate_hash"
    assert body["internal_id_scheme"] == "sarvsakshi_internal_work_v1"
    assert "Source amount unit is unspecified" in body["amount_unit_note"]
    fields = {item["field"]: item for item in body["unavailable_fields"]}
    for name in (
        "district",
        "vendor",
        "expenditure",
        "gps",
        "sanction_date",
        "completion_date",
        "start_date",
        "physical_progress",
        "milestones",
    ):
        assert fields[name]["status"] == "UNAVAILABLE"
        assert fields[name]["reason"]
        assert fields[name]["display"] == UNAVAILABLE_REAL_LABEL
    assert body.get("district") is None
    assert body["synthetic_enrichment"] is None
    assert "fraud" not in str(body).casefold()


def test_project_detail_marks_hybrid_enrichment(client, monkeypatch) -> None:
    session = get_session_factory()()
    try:
        row = _insert(session, internal_project_id="internal:synthetic:detail:hybrid")
        session.commit()
        project_id = row.id
        internal_id = row.internal_project_id
    finally:
        session.close()

    fake = SyntheticEnrichmentDisplay(
        internal_project_id=internal_id,
        implementing_district="Kurnool",
        implementing_agency="Synthetic IDA",
        vendor_name="Prototype Vendor",
        sanction_date="2023-07-01",
        planned_start_date="2023-07-15",
        planned_completion_date="2024-01-15",
        actual_start_date="2023-07-20",
        actual_completion_date=None,
        expenditure_amount=120000,
        latitude=15.8,
        longitude=78.0,
        physical_progress_percent=40,
        milestone_number=2,
        milestone_amount=60000,
        milestone_total_amount=120000,
    )
    monkeypatch.setattr(
        "app.api.routes.projects.has_hybrid_enrichment",
        lambda value: value == internal_id,
    )
    monkeypatch.setattr("app.api.routes.projects.enrichment_for", lambda _value: fake)
    response = client.get(f"/api/v1/projects/{project_id}", params={"mode": "hybrid"})
    assert response.status_code == 200
    body = response.json()
    assert body["has_hybrid_enrichment"] is True
    assert body["data_mode"] == "HYBRID"
    assert body["hybrid_notice"] == HYBRID_DEMO_NOTICE
    assert "SYNTHETIC" in body["hybrid_notice"]
    assert "not official MPLADS records" in body["hybrid_notice"]
    assert body["synthetic_enrichment"]["label"] == "SYNTHETIC"
    assert body["synthetic_enrichment"]["implementing_district"] == "Kurnool"
    assert body["synthetic_enrichment"]["vendor_name"] == "Prototype Vendor"
    assert TIME_UNAVAILABLE_MESSAGE.startswith("Time Intelligence unavailable")


def test_real_mode_never_returns_synthetic_enrichment(client, monkeypatch) -> None:
    session = get_session_factory()()
    try:
        row = _insert(session, internal_project_id="internal:synthetic:detail:real-mode")
        session.commit()
        project_id = row.id
        internal_id = row.internal_project_id
    finally:
        session.close()

    fake = SyntheticEnrichmentDisplay(
        internal_project_id=internal_id,
        implementing_district="ShouldNotAppear",
        implementing_agency=None,
        vendor_name="ShouldNotAppear",
        sanction_date="2020-01-01",
        planned_start_date=None,
        planned_completion_date=None,
        actual_start_date=None,
        actual_completion_date=None,
        expenditure_amount=1,
        latitude=1.0,
        longitude=1.0,
        physical_progress_percent=0,
        milestone_number=None,
        milestone_amount=None,
        milestone_total_amount=None,
    )
    monkeypatch.setattr("app.api.routes.projects.has_hybrid_enrichment", lambda _value: True)
    monkeypatch.setattr("app.api.routes.projects.enrichment_for", lambda _value: fake)
    body = client.get(f"/api/v1/projects/{project_id}", params={"mode": "real"}).json()
    assert body["data_mode"] == "REAL"
    assert body["synthetic_enrichment"] is None
    assert body["hybrid_notice"] == REAL_DATA_NOTICE
    assert "ShouldNotAppear" not in str(body)
    assert body["has_hybrid_enrichment"] is True


def test_real_project_without_enrichment_is_not_hybrid(client, monkeypatch) -> None:
    session = get_session_factory()()
    try:
        row = _insert(session, internal_project_id="internal:synthetic:detail:real")
        session.commit()
        project_id = row.id
    finally:
        session.close()

    monkeypatch.setattr("app.api.routes.projects.has_hybrid_enrichment", lambda _value: False)
    response = client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["has_hybrid_enrichment"] is False
    assert body["data_mode_default"] == "HYBRID"
    assert body["data_mode"] == "HYBRID"
    assert body["hybrid_notice"] is None
    assert body["synthetic_enrichment"] is None
    assert body["is_synthetic"] is True
    assert body["synthetic_label"]
