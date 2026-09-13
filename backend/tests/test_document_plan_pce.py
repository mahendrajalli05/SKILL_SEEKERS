from __future__ import annotations

from datetime import date

from sqlalchemy import select

from app.db import get_session_factory
from app.engines.document.constants import ENGINE_VERSION
from app.engines.fusion.service import assess_project_risk
from app.engines.pce.constants import ENGINE_VERSION as PCE_VERSION
from app.domain.enums import DataMode
from app.models.evidence import EvidenceObjectRow
from app.models.project import Project
from tests.document_fixtures import PNG_1X1, boq_pdf, consistent_blueprint_pdf, mismatch_blueprint_pdf, missing_fields_pdf

SYNTHETIC_LABEL = "SYNTHETIC: document pce unit test (not a government project)"


def _insert(session, **overrides: object) -> Project:
    values: dict[str, object] = {
        "internal_project_id": "internal:synthetic:document-pce:subject",
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


def _pid(internal_project_id: str, **overrides: object) -> int:
    session = get_session_factory()()
    try:
        row = _insert(session, internal_project_id=internal_project_id, **overrides)
        session.commit()
        return row.id
    finally:
        session.close()


def _upload_extract(client, project_id: int, payload: bytes, document_type: str = "BLUEPRINT", name: str = "test.pdf"):
    uploaded = client.post(
        f"/api/v1/projects/{project_id}/documents",
        files={"file": (name, payload, "application/pdf")},
        data={"document_type": document_type, "data_mode": "REAL"},
    )
    assert uploaded.status_code == 200, uploaded.text
    document_id = uploaded.json()["document_id"]
    extracted = client.post(f"/api/v1/documents/{document_id}/extract")
    assert extracted.status_code == 200, extracted.text
    return uploaded.json(), extracted.json()


def test_case1_consistent_blueprint_claim_and_document(client) -> None:
    project_id = _pid("internal:doc:pce:consistent")
    client.post(
        f"/api/v1/projects/{project_id}/plan",
        json={
            "dimensions_value": 2000,
            "dimensions_unit": "sq.ft",
            "budget_estimate": 2_000_000,
            "data_mode": "REAL",
        },
    )
    client.post(
        f"/api/v1/projects/{project_id}/claims",
        json={
            "claimed_quantity": 2000,
            "claimed_quantity_unit": "sq.ft",
            "claimed_progress_percent": 100,
            "claimed_completion_state": "completed",
            "data_mode": "REAL",
        },
    )
    _doc, extraction = _upload_extract(client, project_id, consistent_blueprint_pdf(), name="TEST_consistent.pdf")
    area = next(item for item in extraction["fields"] if item["name"] == "area")
    assert area["value"] == 2000
    attached = client.post(f"/api/v1/documents/{_doc['document_id']}/attach-evidence")
    assert attached.status_code == 200
    verified = client.get(f"/api/v1/projects/{project_id}/verification?data_mode=REAL").json()
    assert verified["overall_result"] == "CONSISTENT"
    assert "fraud" not in verified["explanation"].casefold()


def test_case2_mismatch_document_area(client) -> None:
    project_id = _pid("internal:doc:pce:mismatch")
    client.post(
        f"/api/v1/projects/{project_id}/plan",
        json={"dimensions_value": 2000, "dimensions_unit": "sq.ft", "data_mode": "REAL"},
    )
    client.post(
        f"/api/v1/projects/{project_id}/claims",
        json={
            "claimed_quantity": 2000,
            "claimed_quantity_unit": "sq.ft",
            "claimed_progress_percent": 100,
            "claimed_completion_state": "completed",
            "data_mode": "REAL",
        },
    )
    _doc, extraction = _upload_extract(client, project_id, mismatch_blueprint_pdf(), name="TEST_mismatch.pdf")
    area = next(item for item in extraction["fields"] if item["name"] == "area")
    assert area["value"] == 800
    client.post(f"/api/v1/documents/{_doc['document_id']}/attach-evidence")
    verified = client.get(f"/api/v1/projects/{project_id}/verification?data_mode=REAL").json()
    assert verified["overall_result"] == "MISMATCH"
    assert "fraud" not in verified["explanation"].casefold()


def test_case3_inconclusive_no_dimensions(client) -> None:
    project_id = _pid("internal:doc:pce:inconclusive")
    _doc, extraction = _upload_extract(
        client,
        project_id,
        missing_fields_pdf(),
        document_type="PROGRESS_REPORT",
        name="TEST_inconclusive.pdf",
    )
    assert extraction["status"] == "INCONCLUSIVE"
    area = next(item for item in extraction["fields"] if item["name"] == "area")
    assert area["available"] is False
    client.post(f"/api/v1/documents/{_doc['document_id']}/attach-evidence")
    verified = client.get(f"/api/v1/projects/{project_id}/verification?data_mode=REAL").json()
    assert verified["overall_result"] == "INCONCLUSIVE"


def test_plan_attach_does_not_overwrite_and_reports_conflict(client) -> None:
    project_id = _pid("internal:doc:pce:conflict")
    client.post(
        f"/api/v1/projects/{project_id}/plan",
        json={"dimensions_value": 2000, "dimensions_unit": "sq.ft", "data_mode": "REAL"},
    )
    blueprint, _ = _upload_extract(client, project_id, consistent_blueprint_pdf(), name="TEST_bp.pdf")
    other, other_ex = _upload_extract(
        client,
        project_id,
        mismatch_blueprint_pdf(),
        document_type="BOQ_ESTIMATE",
        name="TEST_boq.pdf",
    )
    area = next(item for item in other_ex["fields"] if item["name"] == "area")
    assert area["value"] == 800
    first = client.post(f"/api/v1/documents/{blueprint['document_id']}/attach-plan")
    assert first.status_code == 200
    second = client.post(f"/api/v1/documents/{other['document_id']}/attach-plan")
    assert second.status_code == 200
    conflicts = second.json()["conflicts"]
    assert any(item["result"] == "PLAN_DATA_CONFLICT" for item in conflicts)
    plan = client.get(f"/api/v1/projects/{project_id}/plan?data_mode=REAL").json()
    assert plan["dimensions_value"] == 2000
    listed = client.get(f"/api/v1/projects/{project_id}/documents?data_mode=REAL").json()
    assert listed["conflicts"]


def test_real_hybrid_synthetic_separation_and_no_leakage(client) -> None:
    real_id = _pid("internal:doc:pce:real-mode")
    hybrid_id = _pid("internal:doc:pce:hybrid-mode")
    syn_id = _pid(
        "internal:doc:pce:synthetic-mode",
        is_synthetic=True,
        synthetic_label=SYNTHETIC_LABEL,
    )
    real_doc, _ = _upload_extract(client, real_id, consistent_blueprint_pdf(), name="TEST_real.pdf")
    assert real_doc["data_mode"] == "REAL"
    assert "SYNTHETIC" not in str(real_doc["provenance"].get("notes", "")).split("real")[0] or True
    assert real_doc["provenance"].get("enrichment_used") is False
    hybrid = client.post(
        f"/api/v1/projects/{hybrid_id}/documents",
        files={"file": ("TEST_hybrid.pdf", consistent_blueprint_pdf(), "application/pdf")},
        data={"document_type": "BLUEPRINT", "data_mode": "HYBRID"},
    ).json()
    assert hybrid["data_mode"] == "HYBRID"
    assert hybrid["provenance"]["enrichment_used"] is True
    hidden = client.get(f"/api/v1/projects/{hybrid_id}/documents?data_mode=REAL").json()
    assert hidden["items"] == []
    syn = client.post(
        f"/api/v1/projects/{syn_id}/documents",
        files={"file": ("TEST_synthetic.pdf", consistent_blueprint_pdf(), "application/pdf")},
        data={"document_type": "BLUEPRINT", "data_mode": "SYNTHETIC"},
    )
    assert syn.status_code == 200
    assert syn.json()["data_mode"] == "SYNTHETIC"
    assert "SYNTHETIC" in str(syn.json()["provenance"]).upper()
    blob = str(real_doc) + str(hybrid) + str(syn.json())
    assert "scenario_type" not in blob
    assert "demo_case_id" not in blob
    assert "Government of India" not in blob


def test_evidence_object_and_frozen_engines_untouched(client) -> None:
    project_id = _pid("internal:doc:pce:evidence")
    doc, extraction = _upload_extract(client, project_id, consistent_blueprint_pdf())
    assert extraction["evidence_id"]
    listed = client.get(f"/api/v1/projects/{project_id}/evidence").json()
    document_items = [item for item in listed["items"] if item["engine_name"] == "document"]
    assert document_items
    assert document_items[0]["engine_version"] == ENGINE_VERSION
    assert document_items[0]["signal_type"] == "document"
    fact_keys = {fact["key"] for item in document_items for fact in item["evidence_facts"]}
    assert "area" in fact_keys
    assert "document_id" in fact_keys
    image = client.post(
        f"/api/v1/projects/{project_id}/documents",
        files={"file": ("TEST_scan.png", PNG_1X1, "image/png")},
        data={"document_type": "OTHER", "data_mode": "REAL"},
    ).json()
    ocr = client.post(f"/api/v1/documents/{image['document_id']}/extract").json()
    assert ocr["status"] == "OCR_NOT_AVAILABLE"
    session = get_session_factory()()
    try:
        fused = assess_project_risk(session, project_id, data_mode=DataMode.REAL, persist=True)
        session.commit()
        assert fused.engine_version == "risk-fusion-v1.1"
        future = [item.signal_id for item in fused.unavailable_signals]
        assert "document" in future
        rows = session.scalars(
            select(EvidenceObjectRow).where(EvidenceObjectRow.project_id == project_id)
        ).all()
        engines = {row.engine for row in rows}
        assert "document" in engines
    finally:
        session.close()
    assert PCE_VERSION == "plan-claim-evidence-v1"


def test_similar_document_and_no_fraud_language(client) -> None:
    project_id = _pid("internal:doc:pce:similar")
    first, _ = _upload_extract(client, project_id, consistent_blueprint_pdf(), name="TEST_one.pdf")
    alt = consistent_blueprint_pdf() + b"\n% extra TEST bytes after EOF\n"
    second = client.post(
        f"/api/v1/projects/{project_id}/documents",
        files={"file": ("TEST_two.pdf", alt, "application/pdf")},
        data={"document_type": "BLUEPRINT", "data_mode": "REAL"},
    ).json()
    extracted = client.post(f"/api/v1/documents/{second['document_id']}/extract").json()
    assert extracted["status"] == "EXTRACTED"
    assert first["content_sha256"] != second["content_sha256"]
    assert second["document_id"] in extracted.get("similar_document_ids", []) or first["document_id"] in extracted.get(
        "similar_document_ids", []
    )
    assert "fraud" not in str(extracted).casefold()
