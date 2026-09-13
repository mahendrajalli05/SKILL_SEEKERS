from __future__ import annotations

from datetime import date

from sqlalchemy import inspect, select

from app.db import get_engine, get_session_factory
from app.domain.enums import DataMode
from app.engines.fusion.service import assess_project_risk
from app.engines.pce.constants import ENGINE_VERSION
from app.models.artifacts import Document, Photo
from app.models.evidence import EvidenceObjectRow
from app.models.project import Project

SYNTHETIC_LABEL = "SYNTHETIC: pce api unit test (not a government project)"


def _insert(session, **overrides: object) -> Project:
    values: dict[str, object] = {
        "internal_project_id": "internal:synthetic:pce-api:subject",
        "internal_id_kind": "internal_surrogate_hash",
        "internal_id_scheme": "sarvsakshi_internal_work_v1",
        "source_dataset": "github_vonter_india-mplads-works_MPLADS.csv",
        "is_synthetic": False,
        "lifecycle_stage": "ONGOING",
        "state": "Andhra Pradesh",
        "constituency": "KURNOOL",
        "category": "Normal/Others",
        "work_description": "NA - Construction of community hall",
        "allocation_amount": 2_000_000,
        "recommended_date": date(2023, 6, 1),
        "status": "Ongoing",
    }
    values.update(overrides)
    row = Project(**values)
    session.add(row)
    session.flush()
    return row


def test_pce_tables_exist(client) -> None:
    inspector = inspect(get_engine())
    names = set(inspector.get_table_names())
    assert "plan" in names
    claim_cols = {column["name"] for column in inspector.get_columns("claim")}
    assert "data_mode" in claim_cols
    assert "claimed_quantity" in claim_cols
    document_cols = {column["name"] for column in inspector.get_columns("document")}
    assert "filename" in document_cols
    assert "provenance_json" in document_cols


def test_consistent_mismatch_inconclusive_api(client) -> None:
    session = get_session_factory()()
    try:
        consistent = _insert(session, internal_project_id="internal:pce:api:consistent")
        mismatch = _insert(session, internal_project_id="internal:pce:api:mismatch")
        inconclusive = _insert(session, internal_project_id="internal:pce:api:inconclusive")
        session.commit()
        cid, mid, iid = consistent.id, mismatch.id, inconclusive.id
    finally:
        session.close()

    plan_body = {
        "sanctioned_scope": "Community hall 2,000 sq.ft",
        "budget_estimate": 2_000_000,
        "dimensions_value": 2000,
        "dimensions_unit": "sq.ft",
        "milestone_amount": 2_000_000,
        "source": "officer_recorded",
        "data_mode": "REAL",
    }
    assert client.post(f"/api/v1/projects/{cid}/plan", json=plan_body).status_code == 200
    assert client.post(
        f"/api/v1/projects/{cid}/claims",
        json={
            "claimed_progress_percent": 100,
            "claimed_expenditure": 1_900_000,
            "claimed_completion_state": "completed",
            "claimed_quantity": 1950,
            "claimed_quantity_unit": "sq.ft",
            "claimant_source": "implementing_agency",
            "data_mode": "REAL",
        },
    ).status_code == 200
    attached = client.post(
        f"/api/v1/projects/{cid}/evidence",
        json={
            "document_type": "pdf",
            "filename": "completion.pdf",
            "observed_quantity": 1940,
            "observed_quantity_unit": "sq.ft",
            "observed_expenditure": 1_900_000,
            "source": "officer_upload",
            "data_mode": "REAL",
        },
    )
    assert attached.status_code == 200
    assert attached.json()["document_id"] is not None
    assert attached.json()["evidence_id"]
    verified = client.get(f"/api/v1/projects/{cid}/verification?data_mode=REAL")
    assert verified.status_code == 200
    body = verified.json()
    assert body["overall_result"] == "CONSISTENT"
    assert "fraud" not in str(body).casefold()
    assert body["provenance"]
    assert body["evidence_confidence"] > 0

    client.post(f"/api/v1/projects/{mid}/plan", json=plan_body)
    client.post(
        f"/api/v1/projects/{mid}/claims",
        json={
            "claimed_progress_percent": 100,
            "claimed_expenditure": 2_000_000,
            "claimed_completion_state": "completed",
            "claimed_quantity": 2000,
            "claimed_quantity_unit": "sq.ft",
            "data_mode": "REAL",
        },
    )
    client.post(
        f"/api/v1/projects/{mid}/evidence",
        json={
            "document_type": "image",
            "filename": "site.jpg",
            "observed_quantity": 800,
            "observed_quantity_unit": "sq.ft",
            "latitude": 15.83,
            "longitude": 78.04,
            "hash": "deadbeef",
            "timestamp": "2024-06-01T10:00:00+00:00",
            "data_mode": "REAL",
        },
    )
    mismatched = client.get(f"/api/v1/projects/{mid}/verification?data_mode=REAL").json()
    assert mismatched["overall_result"] == "MISMATCH"
    assert mismatched["mismatches"]
    assert "fraud" not in mismatched["explanation"].casefold()

    empty = client.get(f"/api/v1/projects/{iid}/verification?data_mode=REAL").json()
    assert empty["overall_result"] == "INCONCLUSIVE"
    assert empty["missing_information"]


def test_synthetic_vs_real_and_provenance(client) -> None:
    session = get_session_factory()()
    try:
        real = _insert(session, internal_project_id="internal:pce:api:real-mode")
        hybrid = _insert(session, internal_project_id="internal:pce:api:hybrid-mode")
        synthetic = _insert(
            session,
            internal_project_id="internal:pce:api:synthetic-mode",
            is_synthetic=True,
            synthetic_label=SYNTHETIC_LABEL,
        )
        session.commit()
        rid, hid, sid = real.id, hybrid.id, synthetic.id
    finally:
        session.close()

    real_plan = client.get(f"/api/v1/projects/{rid}/plan?data_mode=REAL").json()
    assert real_plan["budget_estimate"] == 2_000_000
    assert real_plan["dimensions_value"] is None
    dim_field = next(item for item in real_plan["fields"] if item["name"] == "dimensions_value")
    assert dim_field["available"] is False
    assert dim_field["synthetic"] is False
    assert dim_field["unavailable_reason"]

    hybrid_plan = client.post(
        f"/api/v1/projects/{hid}/plan",
        json={
            "dimensions_value": 1200,
            "dimensions_unit": "sq.ft",
            "milestone_amount": 800_000,
            "data_mode": "HYBRID",
        },
    ).json()
    assert hybrid_plan["data_mode"] == "HYBRID"
    assert hybrid_plan["dimensions_value"] == 1200
    real_view = client.get(f"/api/v1/projects/{hid}/plan?data_mode=REAL").json()
    assert real_view["dimensions_value"] is None
    assert real_view["budget_estimate"] == 2_000_000

    client.post(
        f"/api/v1/projects/{sid}/claims",
        json={"claimed_progress_percent": 40, "data_mode": "SYNTHETIC"},
    )
    syn_claims = client.get(f"/api/v1/projects/{sid}/claims").json()
    assert syn_claims["items"][0]["data_mode"] == "SYNTHETIC"
    assert "SYNTHETIC" in str(syn_claims["items"][0]["provenance"]).upper()

    real_claims = client.get(f"/api/v1/projects/{rid}/claims?data_mode=REAL").json()
    assert real_claims["items"] == []


def test_evidence_document_image_linking_and_deterministic(client) -> None:
    session = get_session_factory()()
    try:
        project = _insert(session, internal_project_id="internal:pce:api:link")
        session.commit()
        project_id = project.id
    finally:
        session.close()

    doc = client.post(
        f"/api/v1/projects/{project_id}/evidence",
        json={"document_type": "blueprint", "filename": "plan.pdf", "data_mode": "REAL"},
    ).json()
    img = client.post(
        f"/api/v1/projects/{project_id}/evidence",
        json={
            "document_type": "image",
            "filename": "site.jpg",
            "latitude": 15.1,
            "longitude": 77.2,
            "hash": "cafebabe",
            "data_mode": "REAL",
        },
    ).json()
    assert doc["document_id"]
    assert img["photo_id"]
    listed = client.get(f"/api/v1/projects/{project_id}/evidence").json()
    kinds = {item["signal_type"] for item in listed["items"]}
    assert "document" in kinds
    assert "image" in kinds
    first = client.get(f"/api/v1/projects/{project_id}/verification?data_mode=REAL").json()
    second = client.get(f"/api/v1/projects/{project_id}/verification?data_mode=REAL").json()
    assert first["overall_result"] == second["overall_result"]
    assert first["explanation"] == second["explanation"]
    pce_ids = [item["evidence_id"] for item in listed["items"] if item["engine_name"] == "pce"]
    listed_again = client.get(f"/api/v1/projects/{project_id}/evidence").json()
    pce_ids_again = [item["evidence_id"] for item in listed_again["items"] if item["engine_name"] == "pce"]
    assert pce_ids_again
    assert len(pce_ids_again) == 1

    session = get_session_factory()()
    try:
        assert session.get(Document, doc["document_id"]) is not None
        assert session.get(Photo, img["photo_id"]) is not None
        evidence_rows = session.scalars(
            select(EvidenceObjectRow).where(EvidenceObjectRow.project_id == project_id)
        ).all()
        engines = {row.engine for row in evidence_rows}
        assert "document" in engines
        assert "image" in engines
        assert "pce" in engines
    finally:
        session.close()


def test_fraud_language_rejected_and_fusion_untouched(client) -> None:
    session = get_session_factory()()
    try:
        project = _insert(session, internal_project_id="internal:pce:api:nofraud")
        session.commit()
        project_id = project.id
    finally:
        session.close()

    denied = client.post(
        f"/api/v1/projects/{project_id}/claims",
        json={"claimed_progress": "this is fraud", "data_mode": "REAL"},
    )
    assert denied.status_code == 422

    client.post(
        f"/api/v1/projects/{project_id}/plan",
        json={"dimensions_value": 100, "dimensions_unit": "sq.ft", "data_mode": "REAL"},
    )
    client.post(
        f"/api/v1/projects/{project_id}/claims",
        json={"claimed_quantity": 100, "claimed_quantity_unit": "sq.ft", "data_mode": "REAL"},
    )
    client.post(
        f"/api/v1/projects/{project_id}/evidence",
        json={"document_type": "pdf", "filename": "ok.pdf", "observed_quantity": 100, "data_mode": "REAL"},
    )
    verification = client.get(f"/api/v1/projects/{project_id}/verification?data_mode=REAL").json()
    assert "fraud" not in verification["explanation"].casefold()
    assert verification["overall_result"] in {"CONSISTENT", "MISMATCH", "INCONCLUSIVE"}

    session = get_session_factory()()
    try:
        fused = assess_project_risk(session, project_id, data_mode=DataMode.REAL, persist=True)
        session.commit()
        future = [item.signal_id for item in fused.unavailable_signals]
        assert "document" in future or any(item.state.value == "NOT_YET_INTEGRATED" for item in fused.unavailable_signals)
        assert fused.engine_version == "risk-fusion-v1.1"
    finally:
        session.close()


def test_missing_endpoints_404(client) -> None:
    assert client.get("/api/v1/projects/999999/plan").status_code == 404
    assert client.get("/api/v1/projects/999999/verification").status_code == 404
    assert ENGINE_VERSION == "plan-claim-evidence-v1"
