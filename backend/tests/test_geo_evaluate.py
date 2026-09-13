from __future__ import annotations

from app.domain.enums import DataMode
from app.engines.geo.constants import (
    DEFAULT_THRESHOLD_METERS,
    GPS_METADATA_UNAVAILABLE,
    INCONCLUSIVE,
    LOCATION_CONSISTENT,
    LOCATION_MISMATCH,
    LOCATION_UNAVAILABLE,
)
from app.engines.geo.distance import offset_north_meters
from app.engines.geo.evaluate import evaluate_image, evaluate_project, overall_result, summarize
from app.engines.geo.types import ImageLocation, ProjectLocation


def _project(lat: float | None, lon: float | None, *, synthetic: bool = True) -> ProjectLocation:
    available = lat is not None and lon is not None
    return ProjectLocation(
        project_id=1,
        latitude=lat,
        longitude=lon,
        source="SYNTHETIC hybrid enrichment coordinates. Not official MPLADS GPS."
        if synthetic
        else "Project coordinates are unavailable in the current public MPLADS extract.",
        data_mode=DataMode.HYBRID if synthetic else DataMode.REAL,
        confidence=0.35 if available else 0.18,
        timestamp=None,
        provenance={"notes": "SYNTHETIC" if synthetic else "real extract"},
        available=available,
        unavailable_reason=None if available else LOCATION_UNAVAILABLE,
        synthetic=synthetic,
    )


def _image(image_id: int, lat: float | None, lon: float | None) -> ImageLocation:
    available = lat is not None and lon is not None
    return ImageLocation(
        image_id=image_id,
        latitude=lat,
        longitude=lon,
        source="Reported GPS metadata from uploaded file",
        extraction_method="exif" if available else "unavailable",
        confidence=0.45 if available else 0.18,
        data_mode=DataMode.HYBRID,
        gps_status="GPS_METADATA_PRESENT" if available else GPS_METADATA_UNAVAILABLE,
        gps_available=available,
        unavailable_reason=None if available else GPS_METADATA_UNAVAILABLE,
    )


def test_exact_match_is_consistent() -> None:
    item = evaluate_image(
        image=_image(1, 15.9, 80.0),
        project_location=_project(15.9, 80.0),
        threshold_meters=DEFAULT_THRESHOLD_METERS,
        data_mode=DataMode.HYBRID,
    )
    assert item.result == LOCATION_CONSISTENT
    assert item.distance_meters == 0.0
    assert item.distance_km == 0.0
    assert item.score == 0.0
    assert "prototype threshold" in item.explanation
    assert "fraud" not in item.explanation.casefold()


def test_within_threshold() -> None:
    lat2, lon2 = offset_north_meters(15.9, 80.0, 148.0)
    item = evaluate_image(
        image=_image(2, lat2, lon2),
        project_location=_project(15.9, 80.0),
        threshold_meters=DEFAULT_THRESHOLD_METERS,
        data_mode=DataMode.HYBRID,
    )
    assert item.result == LOCATION_CONSISTENT
    assert item.distance_meters is not None
    assert 147.0 < item.distance_meters < 149.0
    assert "148 meters" in item.explanation
    assert "500 meter" in item.explanation


def test_just_outside_threshold() -> None:
    lat2, lon2 = offset_north_meters(15.9, 80.0, 501.0)
    item = evaluate_image(
        image=_image(3, lat2, lon2),
        project_location=_project(15.9, 80.0),
        threshold_meters=DEFAULT_THRESHOLD_METERS,
        data_mode=DataMode.HYBRID,
    )
    assert item.result == LOCATION_MISMATCH
    assert item.distance_meters is not None
    assert item.distance_meters > 500
    assert item.score is not None and item.score > 0


def test_missing_project_or_image_gps_is_inconclusive() -> None:
    missing_project = evaluate_image(
        image=_image(4, 15.9, 80.0),
        project_location=_project(None, None, synthetic=False),
        threshold_meters=DEFAULT_THRESHOLD_METERS,
        data_mode=DataMode.REAL,
    )
    assert missing_project.result == INCONCLUSIVE
    assert missing_project.distance_meters is None
    assert LOCATION_UNAVAILABLE in missing_project.finding
    assert "mismatch" not in missing_project.finding
    missing_image = evaluate_image(
        image=_image(5, None, None),
        project_location=_project(15.9, 80.0),
        threshold_meters=DEFAULT_THRESHOLD_METERS,
        data_mode=DataMode.HYBRID,
    )
    assert missing_image.result == INCONCLUSIVE
    assert missing_image.finding == GPS_METADATA_UNAVAILABLE
    assert "not inferred" in missing_image.explanation


def test_mixed_images_do_not_collapse_to_consistent() -> None:
    lat_near, lon_near = offset_north_meters(18.1, 83.4, 100.0)
    lat_far, lon_far = offset_north_meters(18.1, 83.4, 8_000.0)
    result = evaluate_project(
        project_id=9,
        internal_project_id="internal:geo:mixed",
        data_mode=DataMode.HYBRID,
        project_location=_project(18.1, 83.4),
        image_locations=[
            _image(1, lat_near, lon_near),
            _image(2, lat_far, lon_far),
            _image(3, None, None),
        ],
    )
    assert result.summary.image_count == 3
    assert result.summary.gps_available_count == 2
    assert result.summary.gps_unavailable_count == 1
    assert result.summary.consistent_count == 1
    assert result.summary.mismatch_count == 1
    assert result.summary.mixed_results is True
    assert result.overall_result == LOCATION_MISMATCH
    assert "does not make every other image trustworthy" in result.explanation
    assert result.plan_claim_evidence is not None
    assert result.plan_claim_evidence.result == LOCATION_MISMATCH
    assert "does not prove the photograph depicts" in result.plan_claim_evidence.note


def test_one_match_and_missing_gps_is_inconclusive() -> None:
    result = evaluate_project(
        project_id=10,
        internal_project_id="internal:geo:partial",
        data_mode=DataMode.HYBRID,
        project_location=_project(18.1, 83.4),
        image_locations=[
            _image(1, 18.1, 83.4),
            _image(2, None, None),
        ],
    )
    summary = summarize(result.images)
    assert overall_result(summary, True) == INCONCLUSIVE
    assert result.overall_result == INCONCLUSIVE
    assert result.summary.consistent_count == 1
    assert result.summary.gps_unavailable_count == 1
