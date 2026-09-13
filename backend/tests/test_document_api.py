from __future__ import annotations

from datetime import date

from app.db import get_session_factory
from app.engines.document.constants import ENGINE_VERSION, MAX_FILE_BYTES
from app.models.project import Project
from tests.document_fixtures import PNG_1X1, consistent_blueprint_pdf

SYNTHETIC_LABEL = "SYNTHETIC: document api unit test (not a government project)"


def _insert(session, **overrides: object) -> Project:
    values: dict[str, object] = {
        "internal_project_id": "internal:synthetic:document-api:subject",
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


def _project_id(client, **overrides: object) -> int:
    session = get_session_factory()()
    try:
        row = _insert(session, **overrides)
        session.commit()
        return row.id
    finally:
        session.close()


def test_pdf_and_image_upload_and_metadata(client) -> None:
    project_id = _project_id(client, internal_project_id="internal:doc:api:upload")
    pdf = consistent_blueprint_pdf()
    uploaded = client.post(
        f"/api/v1/projects/{project_id}/documents",
        files={"file": ("hall.pdf", pdf, "application/pdf")},
        data={"document_type": "BLUEPRINT", "data_mode": "REAL"},
    )
    assert uploaded.status_code == 200, uploaded.text
    body = uploaded.json()
    assert body["document_type"] == "BLUEPRINT"
    assert body["mime_type"] == "application/pdf"
    assert body["filename"] == "hall.pdf"
    assert body["content_sha256"]
    assert body["file_size"] == len(pdf)
    assert body["data_mode"] == "REAL"
    assert body["extraction_status"] == "NOT_RUN"
    assert body["provenance"]
    assert ENGINE_VERSION == "document-blueprint-v1"

    listed = client.get(f"/api/v1/projects/{project_id}/documents?data_mode=REAL")
    assert listed.status_code == 200
    assert listed.json()["items"][0]["document_id"] == body["document_id"]
    fetched = client.get(f"/api/v1/documents/{body['document_id']}")
    assert fetched.status_code == 200
    assert fetched.json()["content_sha256"] == body["content_sha256"]

    image = client.post(
        f"/api/v1/projects/{project_id}/documents",
        files={"file": ("site.png", PNG_1X1, "image/png")},
        data={"document_type": "OTHER", "data_mode": "REAL"},
    )
    assert image.status_code == 200
    assert image.json()["mime_type"] == "image/png"


def test_user_selected_type_not_filename(client) -> None:
    project_id = _project_id(client, internal_project_id="internal:doc:api:type")
    uploaded = client.post(
        f"/api/v1/projects/{project_id}/documents",
        files={"file": ("blueprint.pdf", consistent_blueprint_pdf(), "application/pdf")},
        data={"document_type": "BOQ_ESTIMATE", "data_mode": "REAL"},
    )
    assert uploaded.status_code == 200
    assert uploaded.json()["document_type"] == "BOQ_ESTIMATE"


def test_invalid_and_oversized_rejected(client) -> None:
    project_id = _project_id(client, internal_project_id="internal:doc:api:reject")
    exe = client.post(
        f"/api/v1/projects/{project_id}/documents",
        files={"file": ("payload.exe", b"MZ executable", "application/octet-stream")},
        data={"document_type": "OTHER", "data_mode": "REAL"},
    )
    assert exe.status_code == 422
    html = client.post(
        f"/api/v1/projects/{project_id}/documents",
        files={"file": ("note.html", b"<html><body>hi</body></html>", "text/html")},
        data={"document_type": "OTHER", "data_mode": "REAL"},
    )
    assert html.status_code == 422
    huge = client.post(
        f"/api/v1/projects/{project_id}/documents",
        files={"file": ("big.pdf", b"%PDF" + b"a" * (MAX_FILE_BYTES + 10), "application/pdf")},
        data={"document_type": "OTHER", "data_mode": "REAL"},
    )
    assert huge.status_code == 422
    unsafe = client.post(
        f"/api/v1/projects/{project_id}/documents",
        files={"file": ("..\\windows\\system32\\hall.pdf", consistent_blueprint_pdf(), "application/pdf")},
        data={"document_type": "BLUEPRINT", "data_mode": "REAL"},
    )
    assert unsafe.status_code == 200
    assert ".." not in (unsafe.json()["filename"] or "")
    assert "\\" not in (unsafe.json()["filename"] or "")


def test_duplicate_hash_and_missing_document(client) -> None:
    project_id = _project_id(client, internal_project_id="internal:doc:api:dup")
    pdf = consistent_blueprint_pdf()
    first = client.post(
        f"/api/v1/projects/{project_id}/documents",
        files={"file": ("a.pdf", pdf, "application/pdf")},
        data={"document_type": "BLUEPRINT", "data_mode": "REAL"},
    ).json()
    second = client.post(
        f"/api/v1/projects/{project_id}/documents",
        files={"file": ("b.pdf", pdf, "application/pdf")},
        data={"document_type": "BLUEPRINT", "data_mode": "REAL"},
    ).json()
    assert first["content_sha256"] == second["content_sha256"]
    assert second["integrity_status"] == "DUPLICATE_FILE"
    assert second["duplicate_of_id"] == first["document_id"]
    assert client.get("/api/v1/documents/999999").status_code == 404
    assert client.get("/api/v1/projects/999999/documents").status_code == 404
