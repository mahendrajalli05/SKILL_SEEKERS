from __future__ import annotations

from app.db import get_session_factory
from app.engines.geo.constants import (
    ENGINE_VERSION,
    GPS_METADATA_UNAVAILABLE,
    INCONCLUSIVE,
    LOCATION_CONSISTENT,
    LOCATION_MISMATCH,
    LOCATION_UNAVAILABLE,
    SATELLITE_VERIFICATION_NOT_AVAILABLE,
)
from app.engines.geo.distance import offset_north_meters
from tests.geo_test_support import SYNTHETIC_LABEL, insert_project
from tests.geospatial_fixtures import (
    DEMO_GHOST_LAT,
    DEMO_GHOST_LON,
    VIZIANAGARAM_LAT,
    VIZIANAGARAM_LON,
    jpeg_with_gps,
    jpeg_without_gps,
)


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


def _upload(client, project_id: int, payload: bytes, filename: str, data_mode: str = "HYBRID"):
    response = client.post(
        f"/api/v1/projects/{project_id}/images",
        files={"file": (filename, payload, "image/jpeg")},
        data={"data_mode": data_mode, "source": "officer_upload"},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_real_mode_project_gps_unavailable(client, monkeypatch) -> None:
    pid, internal_id = _create_project("internal:geo:api:real")
    _patch_coords(monkeypatch, internal_id, VIZIANAGARAM_LAT, VIZIANAGARAM_LON)
    _upload(
        client,
        pid,
        jpeg_with_gps(VIZIANAGARAM_LAT, VIZIANAGARAM_LON),
        "real.jpg",
        data_mode="REAL",
    )
    response = client.get(f"/api/v1/projects/{pid}/geospatial", params={"data_mode": "REAL"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["data_mode"] == "REAL"
    assert body["overall_result"] == INCONCLUSIVE
    assert body["location_consistency"] == INCONCLUSIVE
    assert body["project_location"]["available"] is False
    assert body["project_location"]["unavailable_reason"] == LOCATION_UNAVAILABLE
    assert body["project_location"]["latitude"] is None
    assert body["project_location"]["synthetic"] is False
    assert "LOCATION UNAVAILABLE" in body["explanation"]
    assert "not invented" in body["explanation"] or "were not invented" in body["explanation"]
    assert body["satellite"]["result"] == SATELLITE_VERIFICATION_NOT_AVAILABLE
    assert body["satellite"]["imagery"] is None
    assert "fraud" not in body["explanation"].casefold()
    assert body["engine_version"] == ENGINE_VERSION
    assert body["evidence_confidence"] <= 0.50


def test_hybrid_within_500m(client, monkeypatch) -> None:
    pid, internal_id = _create_project("internal:geo:api:within")
    lat2, lon2 = offset_north_meters(VIZIANAGARAM_LAT, VIZIANAGARAM_LON, 148.0)
    _patch_coords(monkeypatch, internal_id, VIZIANAGARAM_LAT, VIZIANAGARAM_LON)
    _upload(client, pid, jpeg_with_gps(lat2, lon2, tint=90), "near.jpg")
    response = client.post(
        f"/api/v1/projects/{pid}/geospatial/check",
        json={"data_mode": "HYBRID"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["data_mode"] == "HYBRID"
    assert body["overall_result"] == LOCATION_CONSISTENT
    assert body["project_location"]["available"] is True
    assert body["project_location"]["synthetic"] is True
    assert body["project_location"]["label"] == "SYNTHETIC"
    assert "Not official MPLADS GPS" in body["project_location"]["source"]
    image = body["images"][0]
    assert image["result"] == LOCATION_CONSISTENT
    assert image["distance_meters"] is not None
    assert 147.0 < image["distance_meters"] < 149.0
    assert "148 meters" in image["explanation"]
    assert body["threshold_meters"] == 500.0
    assert body["plan_claim_evidence"]["result"] == LOCATION_CONSISTENT
    assert "does not prove the photograph depicts" in body["plan_claim_evidence"]["note"]
    assert "official" not in body["project_location"]["source"] or "Not official" in body["project_location"]["source"]


def test_hybrid_outside_500m(client, monkeypatch) -> None:
    pid, internal_id = _create_project("internal:geo:api:outside")
    lat2, lon2 = offset_north_meters(VIZIANAGARAM_LAT, VIZIANAGARAM_LON, 620.0)
    _patch_coords(monkeypatch, internal_id, VIZIANAGARAM_LAT, VIZIANAGARAM_LON)
    _upload(client, pid, jpeg_with_gps(lat2, lon2, tint=120), "far.jpg")
    body = client.post(
        f"/api/v1/projects/{pid}/geospatial/check",
        json={"data_mode": "HYBRID", "threshold_meters": 500},
    ).json()
    assert body["overall_result"] == LOCATION_MISMATCH
    assert body["images"][0]["distance_meters"] > 500
    assert body["images"][0]["result"] == LOCATION_MISMATCH


def test_missing_image_gps(client, monkeypatch) -> None:
    pid, internal_id = _create_project("internal:geo:api:nogps")
    _patch_coords(monkeypatch, internal_id, VIZIANAGARAM_LAT, VIZIANAGARAM_LON)
    _upload(client, pid, jpeg_without_gps(), "plain.jpg")
    body = client.get(f"/api/v1/projects/{pid}/geospatial", params={"data_mode": "HYBRID"}).json()
    assert body["overall_result"] == INCONCLUSIVE
    assert body["images"][0]["finding"] == GPS_METADATA_UNAVAILABLE
    assert body["summary"]["gps_unavailable_count"] == 1
    assert "not a location mismatch" in body["explanation"].casefold() or "not treated as a location mismatch" in body["explanation"]


def test_mixed_multiple_images(client, monkeypatch) -> None:
    pid, internal_id = _create_project("internal:geo:api:mixed")
    _patch_coords(monkeypatch, internal_id, VIZIANAGARAM_LAT, VIZIANAGARAM_LON)
    _upload(client, pid, jpeg_with_gps(VIZIANAGARAM_LAT, VIZIANAGARAM_LON, tint=60), "match.jpg")
    lat_far, lon_far = offset_north_meters(VIZIANAGARAM_LAT, VIZIANAGARAM_LON, 12_000)
    _upload(client, pid, jpeg_with_gps(lat_far, lon_far, tint=160), "mismatch.jpg")
    _upload(client, pid, jpeg_without_gps(tint=20), "none.jpg")
    body = client.get(f"/api/v1/projects/{pid}/geospatial", params={"data_mode": "HYBRID"}).json()
    assert body["summary"]["image_count"] == 3
    assert body["summary"]["consistent_count"] == 1
    assert body["summary"]["mismatch_count"] == 1
    assert body["summary"]["gps_unavailable_count"] == 1
    assert body["summary"]["mixed_results"] is True
    assert body["overall_result"] == LOCATION_MISMATCH
    assert "does not make every other image trustworthy" in body["explanation"]


def test_demo_ghost_inconsistent_location(client, monkeypatch) -> None:
    pid, internal_id = _create_project("internal:geo:api:ghost")
    _patch_coords(monkeypatch, internal_id, DEMO_GHOST_LAT, DEMO_GHOST_LON)
    _upload(
        client,
        pid,
        jpeg_with_gps(VIZIANAGARAM_LAT, VIZIANAGARAM_LON, tint=200),
        "ghost.jpg",
    )
    body = client.get(f"/api/v1/projects/{pid}/geospatial", params={"data_mode": "HYBRID"}).json()
    assert body["project_location"]["latitude"] == DEMO_GHOST_LAT
    assert body["project_location"]["synthetic"] is True
    assert body["overall_result"] == LOCATION_MISMATCH
    assert body["images"][0]["distance_meters"] > 1_000_000
    assert "SYNTHETIC" in body["project_location"]["source"] or body["project_location"]["label"] == "SYNTHETIC"
    assert "official MPLADS GPS" in body["project_location"]["source"]


def test_threshold_override_and_deterministic(client, monkeypatch) -> None:
    pid, internal_id = _create_project("internal:geo:api:threshold")
    lat2, lon2 = offset_north_meters(VIZIANAGARAM_LAT, VIZIANAGARAM_LON, 200.0)
    _patch_coords(monkeypatch, internal_id, VIZIANAGARAM_LAT, VIZIANAGARAM_LON)
    _upload(client, pid, jpeg_with_gps(lat2, lon2, tint=45), "mid.jpg")
    wide = client.post(
        f"/api/v1/projects/{pid}/geospatial/check",
        json={"data_mode": "HYBRID", "threshold_meters": 500},
    ).json()
    tight = client.post(
        f"/api/v1/projects/{pid}/geospatial/check",
        json={"data_mode": "HYBRID", "threshold_meters": 100},
    ).json()
    again = client.post(
        f"/api/v1/projects/{pid}/geospatial/check",
        json={"data_mode": "HYBRID", "threshold_meters": 100},
    ).json()
    assert wide["overall_result"] == LOCATION_CONSISTENT
    assert tight["overall_result"] == LOCATION_MISMATCH
    assert tight["evidence_ids"] == again["evidence_ids"]
    assert tight["images"][0]["distance_meters"] == again["images"][0]["distance_meters"]


def test_pce_verification_remains_independent(client, monkeypatch) -> None:
    pid, internal_id = _create_project("internal:geo:api:pce")
    _patch_coords(monkeypatch, internal_id, VIZIANAGARAM_LAT, VIZIANAGARAM_LON)
    _upload(client, pid, jpeg_with_gps(VIZIANAGARAM_LAT, VIZIANAGARAM_LON, tint=55), "pce.jpg")
    geo = client.get(f"/api/v1/projects/{pid}/geospatial", params={"data_mode": "HYBRID"}).json()
    verify = client.get(f"/api/v1/projects/{pid}/verification", params={"data_mode": "HYBRID"})
    assert verify.status_code == 200, verify.text
    body = verify.json()
    assert body["overall_result"] in {"CONSISTENT", "MISMATCH", "INCONCLUSIVE"}
    assert "fraud" not in body["explanation"].casefold()
    assert geo["plan_claim_evidence"]["result"] == LOCATION_CONSISTENT
    assert geo["plan_claim_evidence"]["claim"]
    risk = client.get(f"/api/v1/projects/{pid}/risk", params={"data_mode": "HYBRID"})
    assert risk.status_code == 200
    unavailable = {item["signal_id"]: item["state"] for item in risk.json()["unavailable_signals"]}
    assert unavailable.get("geospatial") == "NOT_YET_INTEGRATED"


def test_synthetic_project_is_labelled(client, monkeypatch) -> None:
    pid, internal_id = _create_project(
        "internal:geo:api:synthetic",
        is_synthetic=True,
        synthetic_label=SYNTHETIC_LABEL,
    )
    _patch_coords(monkeypatch, internal_id, VIZIANAGARAM_LAT, VIZIANAGARAM_LON)
    body = client.get(f"/api/v1/projects/{pid}/geospatial").json()
    assert body["data_mode"] == "SYNTHETIC"
    assert "SYNTHETIC" in body["project_location"]["source"] or body["project_location"]["label"] == "SYNTHETIC"
    assert body["satellite"]["result"] == SATELLITE_VERIFICATION_NOT_AVAILABLE
