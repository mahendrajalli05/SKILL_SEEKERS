from __future__ import annotations

from app.engines.image.constants import (
    ENGINE_VERSION,
    EXACT_DUPLICATE,
    GPS_UNAVAILABLE_MESSAGE,
    MAX_FILE_BYTES,
    METADATA_UNAVAILABLE,
    POTENTIAL_IMAGE_REUSE,
)
from tests.image_fixtures import (
    TEST_LATITUDE,
    corrupt_jpeg,
    different_png,
    hybrid_png,
    jpeg_with_exif_gps,
    near_duplicate_jpeg,
    unique_png,
)
from tests.image_test_support import project_id


def test_image_upload_and_project_link(client) -> None:
    pid = project_id(client, internal_project_id="internal:image:api:upload")
    payload = unique_png()
    uploaded = client.post(
        f"/api/v1/projects/{pid}/images",
        files={"file": ("site.png", payload, "image/png")},
        data={"data_mode": "REAL", "source": "officer_upload"},
    )
    assert uploaded.status_code == 200, uploaded.text
    body = uploaded.json()
    assert body["project_id"] == pid
    assert body["filename"] == "site.png"
    assert body["mime_type"] == "image/png"
    assert body["file_size"] == len(payload)
    assert body["content_sha256"]
    assert body["data_mode"] == "REAL"
    assert body["thumbnail_data_url"]
    assert "path" not in body
    assert ENGINE_VERSION == "image-evidence-v1"
    listed = client.get(f"/api/v1/projects/{pid}/images?data_mode=REAL")
    assert listed.status_code == 200
    assert listed.json()["items"][0]["image_id"] == body["image_id"]
    fetched = client.get(f"/api/v1/images/{body['image_id']}")
    assert fetched.status_code == 200
    assert fetched.json()["content_sha256"] == body["content_sha256"]
    analyzed = client.post(f"/api/v1/images/{body['image_id']}/analyze")
    assert analyzed.status_code == 200
    assert analyzed.json()["content_sha256"] == body["content_sha256"]


def test_invalid_and_oversized_rejected(client) -> None:
    pid = project_id(client, internal_project_id="internal:image:api:reject")
    exe = client.post(
        f"/api/v1/projects/{pid}/images",
        files={"file": ("payload.exe", b"MZ executable", "application/octet-stream")},
        data={"data_mode": "REAL"},
    )
    assert exe.status_code == 422
    html = client.post(
        f"/api/v1/projects/{pid}/images",
        files={"file": ("note.html", b"<html>hi</html>", "text/html")},
        data={"data_mode": "REAL"},
    )
    assert html.status_code == 422
    huge = client.post(
        f"/api/v1/projects/{pid}/images",
        files={"file": ("big.jpg", b"\xff\xd8\xff" + b"a" * (MAX_FILE_BYTES + 10), "image/jpeg")},
        data={"data_mode": "REAL"},
    )
    assert huge.status_code == 422
    unsafe = client.post(
        f"/api/v1/projects/{pid}/images",
        files={"file": ("..\\windows\\system32\\site.png", unique_png(), "image/png")},
        data={"data_mode": "REAL"},
    )
    assert unsafe.status_code == 200
    assert ".." not in (unsafe.json()["filename"] or "")
    assert "\\" not in (unsafe.json()["filename"] or "")


def test_exact_duplicate_and_near_duplicate(client) -> None:
    pid = project_id(client, internal_project_id="internal:image:api:dup")
    first = client.post(
        f"/api/v1/projects/{pid}/images",
        files={"file": ("unique.png", unique_png(), "image/png")},
        data={"data_mode": "REAL"},
    )
    assert first.status_code == 200, first.text
    assert first.json()["exact_duplicate"] is False
    dup = client.post(
        f"/api/v1/projects/{pid}/images",
        files={"file": ("copy.png", unique_png(), "image/png")},
        data={"data_mode": "REAL"},
    )
    assert dup.status_code == 200, dup.text
    assert dup.json()["exact_duplicate"] is True
    assert dup.json()["integrity_status"] == EXACT_DUPLICATE
    assert dup.json()["duplicate_of_id"] == first.json()["image_id"]
    assert dup.json()["exact_matches"]
    assert EXACT_DUPLICATE in dup.json()["exact_matches"][0]["explanation"]
    assert "fraud" not in dup.text.casefold()

    other_project = project_id(client, internal_project_id="internal:image:api:near")
    client.post(
        f"/api/v1/projects/{other_project}/images",
        files={"file": ("unique.png", unique_png(), "image/png")},
        data={"data_mode": "REAL"},
    )
    near = client.post(
        f"/api/v1/projects/{other_project}/images",
        files={"file": ("near.jpg", near_duplicate_jpeg(), "image/jpeg")},
        data={"data_mode": "REAL"},
    )
    assert near.status_code == 200, near.text
    assert near.json()["potential_reuse"] is True
    assert near.json()["integrity_status"] == POTENTIAL_IMAGE_REUSE
    assert near.json()["reuse_matches"]
    match = near.json()["reuse_matches"][0]
    assert match["matched_image_id"]
    assert "distance" in match
    assert POTENTIAL_IMAGE_REUSE in match["explanation"]
    assert "fraud" not in match["explanation"].casefold()

    different = client.post(
        f"/api/v1/projects/{other_project}/images",
        files={"file": ("other.png", different_png(), "image/png")},
        data={"data_mode": "REAL"},
    )
    assert different.status_code == 200
    assert different.json()["potential_reuse"] is False
    assert different.json()["exact_duplicate"] is False


def test_exif_and_missing_metadata_api(client) -> None:
    pid = project_id(client, internal_project_id="internal:image:api:exif")
    missing = client.post(
        f"/api/v1/projects/{pid}/images",
        files={"file": ("plain.png", unique_png(), "image/png")},
        data={"data_mode": "REAL"},
    )
    assert missing.status_code == 200
    assert missing.json()["metadata_status"] == METADATA_UNAVAILABLE
    assert missing.json()["gps_available"] is False
    assert missing.json()["gps_message"] == GPS_UNAVAILABLE_MESSAGE

    gps = client.post(
        f"/api/v1/projects/{pid}/images",
        files={"file": ("gps.jpg", jpeg_with_exif_gps(), "image/jpeg")},
        data={"data_mode": "REAL"},
    )
    assert gps.status_code == 200, gps.text
    body = gps.json()
    assert body["gps_available"] is True
    assert abs(body["latitude"] - TEST_LATITUDE) < 0.01
    assert body["capture_timestamp"]
    assert any(item["available"] for item in body["metadata_fields"])
    assert all(
        "reported metadata from uploaded file" in (item["source"] or "")
        for item in body["metadata_fields"]
        if item["available"]
    )


def test_corrupt_and_hybrid_and_summary(client) -> None:
    pid = project_id(client, internal_project_id="internal:image:api:modes")
    corrupt = client.post(
        f"/api/v1/projects/{pid}/images",
        files={"file": ("bad.jpg", corrupt_jpeg(), "image/jpeg")},
        data={"data_mode": "REAL"},
    )
    assert corrupt.status_code == 200, corrupt.text
    assert corrupt.json()["quality"]["readable"] is False
    assert corrupt.json()["authenticity"]["result"] == "INCONCLUSIVE"
    assert corrupt.json()["authenticity"]["capability"] == "NOT_IMPLEMENTED"

    hybrid = client.post(
        f"/api/v1/projects/{pid}/images",
        files={"file": ("hybrid.png", hybrid_png(), "image/png")},
        data={"data_mode": "HYBRID"},
    )
    assert hybrid.status_code == 200, hybrid.text
    assert hybrid.json()["data_mode"] == "HYBRID"
    notes = hybrid.json()["provenance"].get("notes") or ""
    assert "SYNTHETIC" in notes or "synthetic" in notes
    assert "not an official government photograph" in notes.casefold()

    real_list = client.get(f"/api/v1/projects/{pid}/images?data_mode=REAL")
    assert all(item["data_mode"] == "REAL" for item in real_list.json()["items"])
    hybrid_list = client.get(f"/api/v1/projects/{pid}/images?data_mode=HYBRID")
    modes = {item["data_mode"] for item in hybrid_list.json()["items"]}
    assert "HYBRID" in modes
    summary = real_list.json()["summary"]
    assert summary["images_submitted"] >= 1
    assert summary["advanced_authenticity_analysis"] == "INCONCLUSIVE"
    assert "fraud" not in real_list.text.casefold()


def test_attach_evidence_and_pce_integration(client) -> None:
    pid = project_id(client, internal_project_id="internal:image:api:pce")
    uploaded = client.post(
        f"/api/v1/projects/{pid}/images",
        files={"file": ("progress.png", unique_png(), "image/png")},
        data={"data_mode": "REAL"},
    )
    assert uploaded.status_code == 200
    image_id = uploaded.json()["image_id"]
    attached = client.post(f"/api/v1/images/{image_id}/attach-evidence")
    assert attached.status_code == 200
    assert attached.json()["attached_to_evidence"] is True
    assert attached.json()["evidence_ids"]

    evidence = client.get(f"/api/v1/projects/{pid}/evidence?engine=image")
    assert evidence.status_code == 200
    signals = {item["signal_type"] for item in evidence.json()["items"]}
    assert "IMAGE_QUALITY" in signals
    assert "IMAGE_METADATA" in signals
    assert any(item in signals for item in {"IMAGE_EXACT_DUPLICATE", "IMAGE_POTENTIAL_REUSE"})
    for item in evidence.json()["items"]:
        assert "fraud" not in item["finding"].casefold()
        assert "fraud" not in item["explanation"].casefold()
        assert item["engine_version"] == ENGINE_VERSION
        assert item["provenance"]
        assert item["data_mode"] == "REAL"

    client.post(
        f"/api/v1/projects/{pid}/claims",
        json={"claimed_progress": "Work completed", "data_mode": "REAL"},
    )
    verification = client.get(f"/api/v1/projects/{pid}/verification?data_mode=REAL")
    assert verification.status_code == 200
    body = verification.json()
    assert any("image" in finding.casefold() or "photo" in finding.casefold() or "evidence" in finding.casefold() for finding in body["evidence_findings"]) or body["evidence_findings"]
    assert "fraud" not in body["explanation"].casefold()
    assert body["overall_result"] in {"CONSISTENT", "MISMATCH", "INCONCLUSIVE"}
