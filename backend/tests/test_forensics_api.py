from __future__ import annotations

from app.domain.enums import DataMode, SignalType
from app.engines.forensics.constants import (
    AI_GENERATION_ANALYSIS_UNAVAILABLE,
    ENGINE_VERSION,
    METADATA_ANOMALY,
    NO_STRONG_FORENSIC_SIGNAL,
    POTENTIAL_MANIPULATION,
    REVIEW_REQUIRED,
)
from app.engines.fusion.constants import ENGINE_VERSION as FUSION_VERSION
from app.engines.image.constants import ENGINE_VERSION as IMAGE_VERSION
from app.engines.image.security import sha256_bytes
from tests.forensics_fixtures import (
    TEST_FORENSIC_WATERMARK,
    copy_move_png,
    metadata_inconsistent_jpeg,
    metadata_stripped_jpeg,
    original_jpeg,
    recompressed_jpeg,
    resized_jpeg,
    synthetic_ai_like_jpeg,
    unique_png,
)
from tests.image_fixtures import near_duplicate_jpeg
from tests.image_test_support import project_id


def _upload(client, project_id: int, payload: bytes, filename: str, mime: str, data_mode: str = "REAL"):
    response = client.post(
        f"/api/v1/projects/{project_id}/images",
        files={"file": (filename, payload, mime)},
        data={"data_mode": data_mode, "source": "officer_upload"},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_original_bytes_unchanged_after_forensics(client) -> None:
    pid = project_id(client, internal_project_id="internal:forensics:api:original")
    payload = original_jpeg()
    digest = sha256_bytes(payload)
    uploaded = _upload(client, pid, payload, "original.jpg", "image/jpeg")
    image_id = uploaded["image_id"]
    before = client.get(f"/api/v1/images/{image_id}").json()
    forensic = client.post(f"/api/v1/images/{image_id}/forensics")
    assert forensic.status_code == 200, forensic.text
    body = forensic.json()
    after = client.get(f"/api/v1/images/{image_id}").json()
    assert before["content_sha256"] == digest
    assert after["content_sha256"] == digest
    assert body["content_sha256"] == digest
    assert body["bytes_unmodified"] is True
    assert body["integrity"]["bytes_unmodified"] is True
    assert "path" not in body
    assert body["external_transmission"] is False
    assert body["engine_version"] == ENGINE_VERSION
    assert after["engine_version"] == IMAGE_VERSION
    assert after["authenticity"]["capability"] == "NOT_IMPLEMENTED"
    assert after["authenticity"]["result"] == "INCONCLUSIVE"


def test_get_and_post_forensics_are_deterministic(client) -> None:
    pid = project_id(client, internal_project_id="internal:forensics:api:det")
    uploaded = _upload(client, pid, unique_png(), "unique.png", "image/png")
    first = client.post(f"/api/v1/images/{uploaded['image_id']}/forensics").json()
    second = client.get(f"/api/v1/images/{uploaded['image_id']}/forensics").json()
    assert first["overall_assessment"] == second["overall_assessment"]
    assert first["evidence_ids"] == second["evidence_ids"]
    assert first["manipulation_signal"]["result"] == second["manipulation_signal"]["result"]


def test_recompress_resize_duplicate_and_near_duplicate(client) -> None:
    pid = project_id(client, internal_project_id="internal:forensics:api:transform")
    original = original_jpeg()
    first = _upload(client, pid, original, "site.jpg", "image/jpeg")
    duplicate = _upload(client, pid, original, "site-copy.jpg", "image/jpeg")
    near = _upload(client, pid, near_duplicate_jpeg(), "near.jpg", "image/jpeg")
    recompressed = _upload(client, pid, recompressed_jpeg(original), "re.jpg", "image/jpeg")
    resized = _upload(client, pid, resized_jpeg(original), "rs.jpg", "image/jpeg")

    dup_f = client.post(f"/api/v1/images/{duplicate['image_id']}/forensics").json()
    assert dup_f["reuse_signal"]["result"] == "EXACT_DUPLICATE"
    assert dup_f["overall_assessment"] == REVIEW_REQUIRED
    assert "claim_marked_false" in dup_f["plan_claim_evidence"]
    assert dup_f["plan_claim_evidence"]["claim_marked_false"] is False

    near_f = client.post(f"/api/v1/images/{near['image_id']}/forensics").json()
    assert near_f["reuse_signal"]["result"] in {"POTENTIAL_IMAGE_REUSE", "UNIQUE", "EXACT_DUPLICATE"}

    rec_f = client.post(f"/api/v1/images/{recompressed['image_id']}/forensics").json()
    assert rec_f["transformation"]["recompression"]["low_quality_jpeg"] is True
    assert rec_f["manipulation_signal"]["result"] in {NO_STRONG_FORENSIC_SIGNAL, "INCONCLUSIVE", POTENTIAL_MANIPULATION}
    assert "definitely manipulated" not in rec_f["explanation"].casefold()

    res_f = client.post(f"/api/v1/images/{resized['image_id']}/forensics").json()
    assert res_f["transformation"]["width"] == 40
    assert res_f["manipulation_signal"]["result"] != "DEFINITELY_MANIPULATED"
    _ = first


def test_metadata_stripped_and_inconsistent(client) -> None:
    pid = project_id(client, internal_project_id="internal:forensics:api:meta")
    stripped = _upload(client, pid, metadata_stripped_jpeg(), "stripped.jpg", "image/jpeg")
    inconsistent = _upload(client, pid, metadata_inconsistent_jpeg(), "edited.jpg", "image/jpeg")
    stripped_f = client.post(f"/api/v1/images/{stripped['image_id']}/forensics").json()
    assert stripped_f["metadata_signal"]["result"] in {"INCONCLUSIVE", NO_STRONG_FORENSIC_SIGNAL}
    assert "not proof of manipulation" in stripped_f["explanation"].casefold() or "not treated as manipulation" in " ".join(
        stripped_f["metadata_signal"]["notes"]
    ).casefold()
    inconsistent_f = client.post(f"/api/v1/images/{inconsistent['image_id']}/forensics").json()
    assert inconsistent_f["metadata_signal"]["result"] == METADATA_ANOMALY
    assert inconsistent_f["overall_assessment"] == REVIEW_REQUIRED


def test_copy_move_and_ai_unavailable(client) -> None:
    pid = project_id(client, internal_project_id="internal:forensics:api:signals")
    moved = _upload(client, pid, copy_move_png(), "copymove.png", "image/png")
    ai_like = _upload(client, pid, synthetic_ai_like_jpeg(), "ai-test.jpg", "image/jpeg", data_mode="HYBRID")
    moved_f = client.post(f"/api/v1/images/{moved['image_id']}/forensics").json()
    assert moved_f["manipulation_signal"]["result"] == POTENTIAL_MANIPULATION
    assert moved_f["overall_assessment"] == REVIEW_REQUIRED
    ai_f = client.post(
        f"/api/v1/images/{ai_like['image_id']}/forensics",
        params={"data_mode": "HYBRID"},
    ).json()
    assert ai_f["ai_generation_signal"]["result"] == AI_GENERATION_ANALYSIS_UNAVAILABLE
    assert ai_f["data_mode"] == "HYBRID"
    assert "synthetic" in (ai_f.get("synthetic_label") or "").casefold() or ai_f["synthetic"] is True
    assert "definitely ai-generated" not in ai_f["explanation"].casefold()
    assert TEST_FORENSIC_WATERMARK.split("—")[0].strip().casefold() in " ".join(
        [ai_f["explanation"], ai_f.get("synthetic_label") or "", ai_f["note"]]
    ).casefold() or "synthetic" in ai_f["explanation"].casefold()


def test_evidence_objects_and_pce_do_not_mark_claim_false(client) -> None:
    pid = project_id(client, internal_project_id="internal:forensics:api:pce")
    client.post(
        f"/api/v1/projects/{pid}/claims",
        json={"claimed_completion_state": "Photo shows completed work.", "data_mode": "REAL"},
    )
    uploaded = _upload(client, pid, copy_move_png(), "progress.png", "image/png")
    forensic = client.post(f"/api/v1/images/{uploaded['image_id']}/forensics").json()
    pce = forensic["plan_claim_evidence"]
    assert pce["claim"] == "Photo shows completed work."
    assert "Potential" in pce["forensic"] or "potential" in pce["forensic"].casefold()
    assert pce["result"] == "Review required."
    assert pce["claim_marked_false"] is False
    verification = client.get(f"/api/v1/projects/{pid}/verification?data_mode=REAL")
    assert verification.status_code == 200
    assert verification.json()["overall_result"] in {"CONSISTENT", "MISMATCH", "INCONCLUSIVE"}
    evidence = client.get(f"/api/v1/projects/{pid}/evidence?engine=forensics").json()
    types = {item["signal_type"] for item in evidence["items"]}
    assert SignalType.IMAGE_FORENSIC_MANIPULATION.value in types
    assert SignalType.IMAGE_FORENSIC_AI_GENERATION.value in types
    assert SignalType.IMAGE_FORENSIC_METADATA.value in types
    for item in evidence["items"]:
        assert item["engine_version"] == ENGINE_VERSION
        assert item["project_id"] == pid
        assert any(fact["key"] == "image_id" for fact in item["evidence_facts"])
        assert item["provenance"]
        assert item["data_mode"] == "REAL"
        blob = f"{item['finding']} {item['explanation']}".casefold()
        assert "fraud" not in blob
        assert "this image is fake" not in blob
        assert "definitely ai-generated" not in blob
        assert "definitely manipulated" not in blob


def test_real_hybrid_synthetic_and_fusion_unchanged(client) -> None:
    real_id = project_id(client, internal_project_id="internal:forensics:api:real")
    hybrid_id = project_id(client, internal_project_id="internal:forensics:api:hybrid")
    synthetic_id = project_id(
        client,
        internal_project_id="internal:forensics:api:synthetic",
        is_synthetic=True,
        synthetic_label="SYNTHETIC: forensic unit test (not a government project)",
    )
    before = client.get(f"/api/v1/projects/{real_id}/risk?data_mode=REAL").json()
    real_img = _upload(client, real_id, unique_png(), "real.png", "image/png", data_mode="REAL")
    hybrid_img = _upload(client, hybrid_id, unique_png(), "hybrid.png", "image/png", data_mode="HYBRID")
    syn_img = _upload(client, synthetic_id, unique_png(), "syn.png", "image/png", data_mode="SYNTHETIC")
    real_f = client.post(f"/api/v1/images/{real_img['image_id']}/forensics").json()
    hybrid_f = client.post(f"/api/v1/images/{hybrid_img['image_id']}/forensics", params={"data_mode": "HYBRID"}).json()
    syn_f = client.post(f"/api/v1/images/{syn_img['image_id']}/forensics").json()
    assert real_f["data_mode"] == "REAL"
    assert hybrid_f["data_mode"] == "HYBRID"
    assert syn_f["data_mode"] == "SYNTHETIC"
    listed_real = client.get(f"/api/v1/projects/{hybrid_id}/images?data_mode=REAL").json()
    assert all(item["data_mode"] == "REAL" for item in listed_real["items"])
    after = client.get(f"/api/v1/projects/{real_id}/risk?data_mode=REAL").json()
    assert after["engine_version"] == FUSION_VERSION == "risk-fusion-v1.1"
    image_slot = next(item for item in after["unavailable_signals"] if item["signal_id"] == "image")
    assert image_slot["state"] in {"NOT_YET_INTEGRATED", "UNAVAILABLE"} or "not yet integrated" in (
        image_slot.get("unavailable_reason") or ""
    ).casefold()
    assert after["investigation_priority"] == before["investigation_priority"]
    assert after["evidence_confidence"] == before["evidence_confidence"]
    blob = f"{real_f['explanation']} {hybrid_f['explanation']} {syn_f['explanation']}".casefold()
    assert "fraud" not in blob
    assert "this image is fake" not in blob
