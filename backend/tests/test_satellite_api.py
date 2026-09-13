from __future__ import annotations

from app.db import get_session_factory
from app.engines.fusion.constants import ENGINE_VERSION as FUSION_VERSION
from app.engines.satellite.constants import (
    ENGINE_VERSION,
    RESOLUTION_INSUFFICIENT_TEXT,
    SATELLITE_CONSISTENT,
    SATELLITE_INCONCLUSIVE,
    SATELLITE_INCONSISTENT,
    SATELLITE_UNAVAILABLE,
    SCENARIO_AVAILABLE,
    SCENARIO_CHANGE_DETECTED,
    SCENARIO_INSUFFICIENT_RESOLUTION,
    SCENARIO_MATCHING_LOCATION,
    SCENARIO_NO_CHANGE,
    SCENARIO_UNAVAILABLE,
    SCENARIO_WRONG_DATE,
    SCENARIO_WRONG_LOCATION,
)
from tests.geo_test_support import SYNTHETIC_LABEL, insert_project
from tests.geospatial_fixtures import VIZIANAGARAM_LAT, VIZIANAGARAM_LON, jpeg_with_gps


def _create_project(internal_project_id: str, **overrides: object) -> tuple[int, str]:
    session = get_session_factory()()
    try:
        row = insert_project(session, internal_project_id=internal_project_id, **overrides)
        session.commit()
        return row.id, row.internal_project_id
    finally:
        session.close()


def _patch_coords(monkeypatch, internal_project_id: str, lat: float, lon: float) -> None:
    monkeypatch.setattr(
        "app.engines.geo.location.load_hybrid_coordinates",
        lambda path=None: {internal_project_id: (lat, lon)},
    )


def _check(client, project_id: int, scenario: str, data_mode: str = "HYBRID", **extra: object):
    body = {"data_mode": data_mode, "provider": "mock", "test_scenario": scenario, **extra}
    response = client.post(f"/api/v1/projects/{project_id}/satellite/check", json=body)
    assert response.status_code == 200, response.text
    return response.json()


def test_real_mode_no_provider_unavailable(client, monkeypatch) -> None:
    pid, internal_id = _create_project("internal:sat:api:real")
    _patch_coords(monkeypatch, internal_id, VIZIANAGARAM_LAT, VIZIANAGARAM_LON)
    response = client.get(f"/api/v1/projects/{pid}/satellite", params={"data_mode": "REAL"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["data_mode"] == "REAL"
    assert body["overall_result"] == SATELLITE_UNAVAILABLE
    assert body["imagery_available"] is False
    assert body["scenes"] == []
    assert body["map_available"] is False
    assert body["official_imagery"] is False
    assert body["engine_version"] == ENGINE_VERSION
    assert "fabricated" in body["explanation"].casefold() or "unavailable" in body["explanation"].casefold()
    assert "fraud" not in body["explanation"].casefold()
    mocked = client.post(
        f"/api/v1/projects/{pid}/satellite/check",
        json={"data_mode": "REAL", "provider": "mock", "test_scenario": SCENARIO_AVAILABLE},
    )
    assert mocked.status_code == 200
    assert mocked.json()["overall_result"] == SATELLITE_UNAVAILABLE
    assert mocked.json()["labelled_synthetic"] is False


def test_hybrid_scenarios(client, monkeypatch) -> None:
    pid, internal_id = _create_project(
        "internal:sat:api:hybrid",
        work_description="NA - Construction of cement concrete road",
    )
    _patch_coords(monkeypatch, internal_id, VIZIANAGARAM_LAT, VIZIANAGARAM_LON)
    client.post(
        f"/api/v1/projects/{pid}/claims",
        json={
            "claimed_progress_percent": 100,
            "claimed_completion_state": "Site development completed by October 2025.",
            "data_mode": "HYBRID",
        },
    )
    unavailable = _check(client, pid, SCENARIO_UNAVAILABLE)
    available = _check(client, pid, SCENARIO_AVAILABLE)
    matching = _check(client, pid, SCENARIO_MATCHING_LOCATION)
    wrong = _check(client, pid, SCENARIO_WRONG_LOCATION)
    changed = _check(client, pid, SCENARIO_CHANGE_DETECTED)
    none = _check(client, pid, SCENARIO_NO_CHANGE)
    coarse = _check(client, pid, SCENARIO_INSUFFICIENT_RESOLUTION)
    dated = _check(client, pid, SCENARIO_WRONG_DATE)

    assert unavailable["overall_result"] == SATELLITE_UNAVAILABLE
    assert available["imagery_available"] is True
    assert matching["overall_result"] == SATELLITE_CONSISTENT
    assert matching["location_analysis"]["covers_claimed_site"] is True
    assert wrong["overall_result"] == SATELLITE_INCONSISTENT
    assert changed["overall_result"] == SATELLITE_CONSISTENT
    assert changed["change_analysis"]["visible_site_change"] is True
    assert none["change_analysis"]["visible_site_change"] is False
    assert none["overall_result"] == SATELLITE_INCONSISTENT
    assert dated["overall_result"] == SATELLITE_INCONCLUSIVE
    assert dated["temporal_analysis"]["window_matches_claim"] is False
    assert available["labelled_synthetic"] is True
    assert available["official_imagery"] is False
    assert "TEST/SYNTHETIC" in available["availability"]["reason"] or available["labelled_synthetic"]
    for body in (available, matching, wrong, changed, none, dated):
        assert "fraud" not in body["explanation"].casefold()
        assert body["plan_claim_evidence"]["claim_marked_false"] is False
        assert body["map_available"] is False

    toilet_pid, toilet_id = _create_project(
        "internal:sat:api:toilet",
        work_description="NA - Construction of toilet block",
    )
    _patch_coords(monkeypatch, toilet_id, VIZIANAGARAM_LAT, VIZIANAGARAM_LON)
    small = _check(client, toilet_pid, SCENARIO_INSUFFICIENT_RESOLUTION)
    assert small["overall_result"] == SATELLITE_INCONCLUSIVE
    assert RESOLUTION_INSUFFICIENT_TEXT in small["explanation"]
    assert coarse["work_scale"] == "LARGE_LINEAR"


def test_missing_project_gps_api(client) -> None:
    pid, _internal = _create_project("internal:sat:api:nogps")
    body = _check(client, pid, SCENARIO_AVAILABLE)
    assert body["overall_result"] == SATELLITE_UNAVAILABLE
    assert body["project_location"]["available"] is False
    assert body["imagery_available"] is False


def test_image_gps_is_separate_signal(client, monkeypatch) -> None:
    pid, internal_id = _create_project("internal:sat:api:imagegps")
    _patch_coords(monkeypatch, internal_id, VIZIANAGARAM_LAT, VIZIANAGARAM_LON)
    upload = client.post(
        f"/api/v1/projects/{pid}/images",
        files={"file": ("site.jpg", jpeg_with_gps(VIZIANAGARAM_LAT, VIZIANAGARAM_LON), "image/jpeg")},
        data={"data_mode": "HYBRID", "source": "officer_upload"},
    )
    assert upload.status_code == 200, upload.text
    body = _check(client, pid, SCENARIO_MATCHING_LOCATION)
    assert body["image_gps_signals"]
    note = body["image_gps_signals"][0]["note"].casefold()
    assert "separate signals" in note
    assert "combined" in note


def test_evidence_objects_and_pce_and_fusion_unchanged(client, monkeypatch) -> None:
    pid, internal_id = _create_project("internal:sat:api:evidence")
    _patch_coords(monkeypatch, internal_id, VIZIANAGARAM_LAT, VIZIANAGARAM_LON)
    client.post(
        f"/api/v1/projects/{pid}/claims",
        json={
            "claimed_completion_state": "Site development completed by October 2025.",
            "data_mode": "HYBRID",
        },
    )
    first = _check(client, pid, SCENARIO_CHANGE_DETECTED)
    second = _check(client, pid, SCENARIO_CHANGE_DETECTED)
    assert first["evidence_ids"]
    assert first["evidence_ids"] == second["evidence_ids"]
    listed = client.get(f"/api/v1/projects/{pid}/evidence", params={"engine": "satellite", "data_mode": "HYBRID"})
    assert listed.status_code == 200, listed.text
    items = listed.json()["items"]
    types = {item["signal_type"] for item in items}
    assert "SATELLITE_AVAILABILITY" in types
    assert "SATELLITE_LOCATION" in types
    assert "SATELLITE_CHANGE" in types
    assert "SATELLITE_TEMPORAL" in types
    for item in items:
        assert item["engine_name"] == "satellite"
        assert item["engine_version"] == ENGINE_VERSION
        assert item["data_mode"] == "HYBRID"
        assert item["provenance"]
        assert "SYNTHETIC" in item["provenance"]["notes"] or "TEST" in item["provenance"]["notes"]
        assert "fraud" not in item["explanation"].casefold()
        assert item["provenance"]["enrichment_used"] is True

    verify = client.get(f"/api/v1/projects/{pid}/verification", params={"data_mode": "HYBRID"})
    assert verify.status_code == 200
    assert verify.json()["overall_result"] in {"CONSISTENT", "MISMATCH", "INCONCLUSIVE"}
    assert first["plan_claim_evidence"]["claim_marked_false"] is False
    assert "October 2025" in (first["plan_claim_evidence"]["claim"] or "")

    before_risk = client.get(f"/api/v1/projects/{pid}/risk", params={"data_mode": "HYBRID"})
    assert before_risk.status_code == 200
    risk = before_risk.json()
    assert risk["engine_version"] == FUSION_VERSION == "risk-fusion-v1.1"
    unavailable = {item["signal_id"]: item["state"] for item in risk["unavailable_signals"]}
    assert unavailable.get("geospatial") == "NOT_YET_INTEGRATED"
    assert "satellite" not in unavailable
    assert all(item["signal_id"] != "satellite" for item in risk["contributing_signals"])


def test_synthetic_project_labelled(client, monkeypatch) -> None:
    pid, internal_id = _create_project(
        "internal:sat:api:synthetic",
        is_synthetic=True,
        synthetic_label=SYNTHETIC_LABEL,
        work_description="NA - Construction of cement concrete road",
    )
    _patch_coords(monkeypatch, internal_id, VIZIANAGARAM_LAT, VIZIANAGARAM_LON)
    body = _check(client, pid, SCENARIO_AVAILABLE, data_mode="SYNTHETIC")
    assert body["data_mode"] == "SYNTHETIC"
    assert body["labelled_synthetic"] is True
    assert body["official_imagery"] is False
