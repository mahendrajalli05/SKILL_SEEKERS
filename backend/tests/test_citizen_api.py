from __future__ import annotations

from app.engines.citizen.constants import (
    AGGREGATE_COMMUNITY_CONCERN,
    DUPLICATE_FLAG,
    ENGINE_VERSION,
    INCONCLUSIVE,
    LOCATION_REJECTED,
    LOCATION_VERIFIED,
    SAMPLE_INSUFFICIENT,
    STATUS_ACCEPTED,
    STATUS_INCONCLUSIVE,
    STATUS_REJECTED,
    SYNTHETIC_BADGE,
)
from app.engines.compliance.constants import ENGINE_VERSION as COMPLIANCE_VERSION
from app.engines.cost.constants import ENGINE_VERSION as COST_VERSION
from app.engines.document.constants import ENGINE_VERSION as DOCUMENT_VERSION
from app.engines.fusion.constants import ENGINE_VERSION as FUSION_VERSION
from app.engines.geo.constants import ENGINE_VERSION as GEO_VERSION
from app.engines.geo.distance import offset_north_meters
from app.engines.graph.constants import ENGINE_VERSION as GRAPH_VERSION
from app.engines.image.constants import ENGINE_VERSION as IMAGE_VERSION
from app.engines.milestone.constants import ENGINE_VERSION as MILESTONE_VERSION
from app.engines.need.constants import ENGINE_VERSION as NEED_VERSION
from app.engines.overlap.constants import ENGINE_VERSION as OVERLAP_VERSION
from app.engines.pce.constants import ENGINE_VERSION as PCE_VERSION
from app.engines.time.constants import ENGINE_VERSION as TIME_VERSION
from tests.citizen_test_support import SYNTHETIC_LABEL, patch_project_gps, project_row
from tests.geospatial_fixtures import VIZIANAGARAM_LAT, VIZIANAGARAM_LON
from tests.image_fixtures import unique_png


def test_frozen_engines_unchanged() -> None:
    assert COST_VERSION == "cost-peer-v1.1"
    assert TIME_VERSION == "time-peer-v1"
    assert OVERLAP_VERSION == "overlap-multi-v1"
    assert COMPLIANCE_VERSION == "compliance-rules-v1"
    assert FUSION_VERSION == "risk-fusion-v1.1"
    assert GRAPH_VERSION == "relationship-graph-v1"
    assert PCE_VERSION == "plan-claim-evidence-v1"
    assert DOCUMENT_VERSION == "document-blueprint-v1"
    assert IMAGE_VERSION == "image-evidence-v1"
    assert GEO_VERSION == "geospatial-consistency-v1"
    assert NEED_VERSION == "need-impact-v1"
    assert MILESTONE_VERSION == "milestone-advisor-v1"
    assert ENGINE_VERSION == "jan-sakshi-v1"


def _submit(client, project_id: int, payload: dict, *, files=None, data_mode: str = "HYBRID"):
    if files is not None:
        form = {key: str(value) for key, value in payload.items() if value is not None}
        form["data_mode"] = data_mode
        return client.post(
            f"/api/v1/projects/{project_id}/citizen-reports",
            data=form,
            files=files,
        )
    body = dict(payload)
    body["data_mode"] = data_mode
    return client.post(f"/api/v1/projects/{project_id}/citizen-reports", json=body)


def test_case1_accepted_within_180m(client, monkeypatch) -> None:
    pid, internal_id = project_row("internal:citizen:case1")
    lat2, lon2 = offset_north_meters(VIZIANAGARAM_LAT, VIZIANAGARAM_LON, 180.0)
    patch_project_gps(monkeypatch, internal_id, VIZIANAGARAM_LAT, VIZIANAGARAM_LON)
    response = _submit(
        client,
        pid,
        {
            "satisfaction_rating": 5,
            "observation_text": "The completed road is useful and in good condition for villagers.",
            "issue_category": "other",
            "latitude": lat2,
            "longitude": lon2,
            "capture_timestamp": "2026-09-10T09:15:00+00:00",
        },
        files={"file": ("site.png", unique_png(), "image/png")},
        data_mode="HYBRID",
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["submission_status"] == STATUS_ACCEPTED
    assert body["verification_result"] == LOCATION_VERIFIED
    assert body["image_id"] is not None
    assert body["original_image_preserved"] is True
    assert "latitude" not in body or body.get("latitude") is None
    assert body["location_verification"].get("latitude") is None
    assert "fraud" not in body["governance_note"].casefold()
    assert body["data_mode"] == "HYBRID"
    assert body["synthetic_badge"]
    assert body["watermark"]["generated"] is True
    evidence = client.get(f"/api/v1/projects/{pid}/evidence", params={"engine": "citizen"})
    assert evidence.status_code == 200
    types = {item["signal_type"] for item in evidence.json()["items"]}
    assert "CITIZEN_LOCATION" in types
    assert "CITIZEN_FEEDBACK" in types
    assert "CITIZEN_IMAGE" in types


def test_case2_rejected_at_1_8km(client, monkeypatch) -> None:
    pid, internal_id = project_row("internal:citizen:case2")
    lat2, lon2 = offset_north_meters(VIZIANAGARAM_LAT, VIZIANAGARAM_LON, 1800.0)
    patch_project_gps(monkeypatch, internal_id, VIZIANAGARAM_LAT, VIZIANAGARAM_LON)
    response = _submit(
        client,
        pid,
        {
            "satisfaction_rating": 3,
            "observation_text": "Work looks delayed from a distant viewpoint along the corridor.",
            "latitude": lat2,
            "longitude": lon2,
            "capture_timestamp": "2026-09-10T09:15:00+00:00",
        },
        data_mode="HYBRID",
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["submission_status"] == STATUS_REJECTED
    assert body["verification_result"] == LOCATION_REJECTED
    assert body["rejection_reason"]
    assert "outside" in (body["rejection_reason"] or "").casefold() or "outside" in " ".join(body["reasons"]).casefold()


def test_exact_500m_boundary(client, monkeypatch) -> None:
    pid, internal_id = project_row("internal:citizen:boundary")
    lat2, lon2 = offset_north_meters(VIZIANAGARAM_LAT, VIZIANAGARAM_LON, 499.5)
    patch_project_gps(monkeypatch, internal_id, VIZIANAGARAM_LAT, VIZIANAGARAM_LON)
    response = _submit(
        client,
        pid,
        {
            "satisfaction_rating": 4,
            "observation_text": "The work appears complete and is useful to the neighbourhood.",
            "latitude": lat2,
            "longitude": lon2,
            "capture_timestamp": "2026-09-10T09:15:00+00:00",
        },
        data_mode="HYBRID",
    )
    assert response.status_code == 200, response.text
    assert response.json()["verification_result"] == LOCATION_VERIFIED
    assert response.json()["submission_status"] == STATUS_ACCEPTED


def test_case3_missing_citizen_gps(client, monkeypatch) -> None:
    pid, internal_id = project_row("internal:citizen:case3")
    patch_project_gps(monkeypatch, internal_id, VIZIANAGARAM_LAT, VIZIANAGARAM_LON)
    response = _submit(
        client,
        pid,
        {
            "satisfaction_rating": 3,
            "observation_text": "Could not confirm the exact work location from this visit.",
            "capture_timestamp": "2026-09-10T09:15:00+00:00",
        },
        data_mode="HYBRID",
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["verification_result"] == INCONCLUSIVE
    assert body["submission_status"] == STATUS_INCONCLUSIVE
    assert "LOCATION_UNAVAILABLE" in " ".join(body["reasons"]) or "unavailable" in body["location_verification"]["reason"]


def test_missing_project_gps_real_mode(client, monkeypatch) -> None:
    pid, internal_id = project_row("internal:citizen:real-gps")
    patch_project_gps(monkeypatch, internal_id, VIZIANAGARAM_LAT, VIZIANAGARAM_LON)
    lat2, lon2 = offset_north_meters(VIZIANAGARAM_LAT, VIZIANAGARAM_LON, 180.0)
    response = _submit(
        client,
        pid,
        {
            "satisfaction_rating": 4,
            "observation_text": "The completed road is useful and in good condition for villagers.",
            "latitude": lat2,
            "longitude": lon2,
            "capture_timestamp": "2026-09-10T09:15:00+00:00",
        },
        data_mode="REAL",
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["data_mode"] == "REAL"
    assert body["verification_result"] == INCONCLUSIVE
    assert body["location_verification"]["project_gps_available"] is False
    assert "not invented" in body["location_verification"]["reason"].casefold() or "not invented" in " ".join(body["reasons"]).casefold()
    listed = client.get(f"/api/v1/projects/{pid}/citizen-reports", params={"data_mode": "REAL"})
    assert listed.status_code == 200
    assert "latitude" not in listed.json()["items"][0]
    assert listed.json()["items"][0].get("latitude") is None


def test_missing_timestamp_is_inconclusive(client, monkeypatch) -> None:
    pid, internal_id = project_row("internal:citizen:timestamp")
    lat2, lon2 = offset_north_meters(VIZIANAGARAM_LAT, VIZIANAGARAM_LON, 180.0)
    patch_project_gps(monkeypatch, internal_id, VIZIANAGARAM_LAT, VIZIANAGARAM_LON)
    response = _submit(
        client,
        pid,
        {
            "satisfaction_rating": 4,
            "observation_text": "The completed road is useful and in good condition for villagers.",
            "latitude": lat2,
            "longitude": lon2,
        },
        data_mode="HYBRID",
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["timestamp_status"] == "TIMESTAMP_UNAVAILABLE"
    assert body["submission_status"] == STATUS_INCONCLUSIVE


def test_missing_and_invalid_image(client, monkeypatch) -> None:
    pid, internal_id = project_row("internal:citizen:image")
    lat2, lon2 = offset_north_meters(VIZIANAGARAM_LAT, VIZIANAGARAM_LON, 180.0)
    patch_project_gps(monkeypatch, internal_id, VIZIANAGARAM_LAT, VIZIANAGARAM_LON)
    missing = _submit(
        client,
        pid,
        {
            "satisfaction_rating": 4,
            "observation_text": "The completed road is useful and in good condition for villagers.",
            "latitude": lat2,
            "longitude": lon2,
            "capture_timestamp": "2026-09-10T09:15:00+00:00",
        },
        data_mode="HYBRID",
    )
    assert missing.status_code == 200, missing.text
    assert missing.json()["image_id"] is None
    invalid = _submit(
        client,
        pid,
        {
            "satisfaction_rating": 4,
            "observation_text": "The completed road is useful and in good condition for villagers.",
            "latitude": lat2,
            "longitude": lon2,
            "capture_timestamp": "2026-09-10T09:15:00+00:00",
        },
        files={"file": ("payload.exe", b"MZ executable", "application/octet-stream")},
        data_mode="HYBRID",
    )
    assert invalid.status_code == 422


def test_case5_duplicate_image(client, monkeypatch) -> None:
    pid, internal_id = project_row("internal:citizen:dup")
    lat2, lon2 = offset_north_meters(VIZIANAGARAM_LAT, VIZIANAGARAM_LON, 180.0)
    patch_project_gps(monkeypatch, internal_id, VIZIANAGARAM_LAT, VIZIANAGARAM_LON)
    payload = {
        "satisfaction_rating": 4,
        "observation_text": "The completed road is useful and in good condition for villagers.",
        "latitude": lat2,
        "longitude": lon2,
        "capture_timestamp": "2026-09-10T09:15:00+00:00",
    }
    first = _submit(client, pid, payload, files={"file": ("a.png", unique_png(), "image/png")})
    assert first.status_code == 200, first.text
    second = _submit(client, pid, payload, files={"file": ("b.png", unique_png(), "image/png")})
    assert second.status_code == 200, second.text
    body = second.json()
    assert body["duplicate"]["flagged"] is True
    assert body["duplicate"]["flag"] == DUPLICATE_FLAG
    assert "fraud" not in (body["duplicate"]["explanation"] or "").casefold()


def test_case4_aggregate_incomplete_work(client, monkeypatch) -> None:
    pid, internal_id = project_row("internal:citizen:case4")
    patch_project_gps(monkeypatch, internal_id, VIZIANAGARAM_LAT, VIZIANAGARAM_LON)
    for index in range(3):
        lat2, lon2 = offset_north_meters(VIZIANAGARAM_LAT, VIZIANAGARAM_LON, 80.0 + index)
        response = _submit(
            client,
            pid,
            {
                "satisfaction_rating": 2,
                "observation_text": "Road remains incomplete in section X and the surface is unfinished.",
                "issue_category": "incomplete_work",
                "latitude": lat2,
                "longitude": lon2,
                "capture_timestamp": f"2026-09-10T09:1{index}:00+00:00",
            },
            data_mode="HYBRID",
        )
        assert response.status_code == 200, response.text
    summary = client.get(f"/api/v1/projects/{pid}/citizen-summary", params={"data_mode": "HYBRID"})
    assert summary.status_code == 200, summary.text
    body = summary.json()
    assert body["total_submissions"] == 3
    assert body["verified_location_submissions"] == 3
    assert body["sample_size_status"] == SAMPLE_INSUFFICIENT
    assert body["aggregate_finding"] == AGGREGATE_COMMUNITY_CONCERN
    assert body["average_satisfaction"] == 2
    assert "latitude" not in body
    assert body["investigation_priority_unchanged"] is True
    assert "fraud" not in body["explanation"].casefold()
    evidence = client.get(f"/api/v1/projects/{pid}/evidence", params={"engine": "citizen"})
    types = {item["signal_type"] for item in evidence.json()["items"]}
    assert "CITIZEN_AGGREGATE" in types


def test_privacy_and_modes_and_pce_and_fusion(client, monkeypatch) -> None:
    pid, internal_id = project_row("internal:citizen:pce")
    patch_project_gps(monkeypatch, internal_id, VIZIANAGARAM_LAT, VIZIANAGARAM_LON)
    lat2, lon2 = offset_north_meters(VIZIANAGARAM_LAT, VIZIANAGARAM_LON, 120.0)
    claim = client.post(
        f"/api/v1/projects/{pid}/claims",
        json={
            "claimed_progress_percent": 100,
            "claimed_completion_state": "Road work is complete.",
            "data_mode": "HYBRID",
        },
    )
    assert claim.status_code == 200, claim.text
    before_risk = client.get(f"/api/v1/projects/{pid}/risk", params={"data_mode": "HYBRID"})
    assert before_risk.status_code == 200
    before = before_risk.json()
    response = _submit(
        client,
        pid,
        {
            "satisfaction_rating": 1,
            "observation_text": "Road remains incomplete in section X and the surface is unfinished.",
            "issue_category": "incomplete_work",
            "latitude": lat2,
            "longitude": lon2,
            "capture_timestamp": "2026-09-10T09:15:00+00:00",
        },
        data_mode="HYBRID",
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["plan_claim_evidence"]["result"] == "CITIZEN_CONTRADICTION"
    assert body["plan_claim_evidence"]["claim_marked_false"] is False
    listed = client.get(f"/api/v1/projects/{pid}/citizen-reports", params={"data_mode": "HYBRID"})
    item = listed.json()["items"][0]
    assert "latitude" not in item or item.get("latitude") is None
    officer = client.get(
        f"/api/v1/citizen-reports/{body['citizen_report_id']}",
        params={"data_mode": "HYBRID", "include_location": True},
    )
    assert officer.status_code == 200
    assert officer.json()["latitude"] is not None
    after_risk = client.get(f"/api/v1/projects/{pid}/risk", params={"data_mode": "HYBRID"})
    after = after_risk.json()
    assert after["engine_version"] == "risk-fusion-v1.1"
    citizen_slot = next(item for item in after["unavailable_signals"] if item["signal_id"] == "citizen_evidence")
    assert citizen_slot["state"] in {"NOT_YET_INTEGRATED", "UNAVAILABLE"} or "not yet integrated" in (
        citizen_slot.get("unavailable_reason") or ""
    ).casefold()
    assert after["investigation_priority"] == before["investigation_priority"]
    assert after["evidence_confidence"] == before["evidence_confidence"]
    synthetic = project_row(
        "internal:citizen:synthetic",
        is_synthetic=True,
        synthetic_label=SYNTHETIC_LABEL,
    )[0]
    syn = _submit(
        client,
        synthetic,
        {
            "satisfaction_rating": 3,
            "observation_text": "TEST observation for a labelled synthetic project record only.",
            "capture_timestamp": "2026-09-10T09:15:00+00:00",
        },
        data_mode="SYNTHETIC",
    )
    assert syn.status_code == 200, syn.text
    assert syn.json()["data_mode"] == "SYNTHETIC"
    assert "SYNTHETIC" in (syn.json()["synthetic_badge"] or "")
    missing_project = client.post("/api/v1/projects/999999/citizen-reports", json={"satisfaction_rating": 3})
    assert missing_project.status_code == 404
