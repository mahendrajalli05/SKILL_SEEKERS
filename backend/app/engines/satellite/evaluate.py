"""Combine provider metadata into a satellite assessment.

Does not download or fabricate official imagery. Does not fuse Risk Fusion.
"""

from __future__ import annotations

from datetime import date

from app.domain.enums import DataMode
from app.engines.geo.distance import haversine_m
from app.engines.geo.types import ImageLocation, ProjectLocation
from app.engines.satellite.analysis import analyze_change, analyze_coverage, analyze_resolution
from app.engines.satellite.confidence import confidence_label, satellite_confidence
from app.engines.satellite.constants import (
    DEFAULT_AOI_RADIUS_M,
    ENGINE_VERSION,
    GOVERNANCE_NOTE,
    LIMITATIONS,
    SATELLITE_CONSISTENT,
    SATELLITE_INCONCLUSIVE,
    SATELLITE_INCONSISTENT,
    SATELLITE_UNAVAILABLE,
    UNAVAILABLE_NO_COORDINATES,
    UNAVAILABLE_NO_SCENES,
)
from app.engines.satellite.dates import analyze_temporal
from app.engines.satellite.explain import build_explanation, overall_finding
from app.engines.satellite.types import (
    ImageGpsSignal,
    ImageryAvailability,
    SatelliteResult,
)


def _coverage_label(location_result: str, covers: bool | None) -> str:
    if covers is True:
        return "Covers claimed site"
    if covers is False:
        return "Does not cover claimed site"
    if location_result == SATELLITE_UNAVAILABLE:
        return "Unavailable"
    return "Inconclusive"


def _image_gps_signals(
    *,
    project_location: ProjectLocation,
    image_locations: list[ImageLocation],
    covers_project: bool | None,
    aoi_radius_m: float,
    scene_lat: float | None,
    scene_lon: float | None,
) -> list[ImageGpsSignal]:
    signals: list[ImageGpsSignal] = []
    for image in image_locations:
        covers_image: bool | None = None
        if (
            image.gps_available
            and image.latitude is not None
            and image.longitude is not None
            and scene_lat is not None
            and scene_lon is not None
        ):
            distance = haversine_m(
                float(image.latitude),
                float(image.longitude),
                float(scene_lat),
                float(scene_lon),
            )
            covers_image = distance <= aoi_radius_m
        signals.append(
            ImageGpsSignal(
                image_id=image.image_id,
                image_gps_available=bool(image.gps_available),
                project_location_available=bool(project_location.available),
                satellite_covers_project=covers_project,
                satellite_covers_image_gps=covers_image,
                note=(
                    "Project location, image GPS, and satellite coverage are separate signals. "
                    "They are not combined into a single unsupported conclusion."
                ),
            )
        )
    return signals


def _decide_overall(
    *,
    unavailable: bool,
    location_result: str | None,
    resolution_sufficient: bool | None,
    temporal_mismatch: bool,
    change_result: str | None,
    change_assessed: bool,
) -> str:
    if unavailable:
        return SATELLITE_UNAVAILABLE
    if location_result == SATELLITE_INCONSISTENT:
        return SATELLITE_INCONSISTENT
    if resolution_sufficient is not True:
        return SATELLITE_INCONCLUSIVE
    if temporal_mismatch:
        return SATELLITE_INCONCLUSIVE
    if change_assessed and change_result == SATELLITE_INCONSISTENT:
        return SATELLITE_INCONSISTENT
    if change_assessed and change_result == SATELLITE_CONSISTENT:
        return SATELLITE_CONSISTENT
    if location_result == SATELLITE_CONSISTENT:
        return SATELLITE_CONSISTENT
    return SATELLITE_INCONCLUSIVE


def evaluate_satellite(
    *,
    project_id: int,
    internal_project_id: str,
    data_mode: DataMode,
    project_location: ProjectLocation,
    availability: ImageryAvailability,
    image_locations: list[ImageLocation],
    work_scale: str,
    planned_date: date | None,
    claimed_completion: date | None,
    milestone_date: date | None,
    aoi_radius_m: float = DEFAULT_AOI_RADIUS_M,
) -> SatelliteResult:
    coords_ok = (
        project_location.available
        and project_location.latitude is not None
        and project_location.longitude is not None
    )
    scenes = list(availability.scenes)
    unavailable_reason: str | None = None
    if not coords_ok:
        unavailable_reason = UNAVAILABLE_NO_COORDINATES
        scenes = []
    elif not availability.available or not scenes:
        unavailable_reason = availability.reason or UNAVAILABLE_NO_SCENES

    location = None
    resolution = None
    temporal = None
    change = None
    if scenes:
        location = analyze_coverage(project_location, scenes, aoi_radius_m)
        resolution = analyze_resolution(scenes, work_scale)
        temporal = analyze_temporal(
            scenes,
            planned_date=planned_date,
            claimed_completion=claimed_completion,
            milestone_date=milestone_date,
        )
        change = analyze_change(scenes, resolution)

    overall = _decide_overall(
        unavailable=unavailable_reason is not None,
        location_result=None if location is None else location.result,
        resolution_sufficient=None if resolution is None else resolution.sufficient,
        temporal_mismatch=bool(temporal is not None and temporal.window_matches_claim is False),
        change_result=None if change is None else change.result,
        change_assessed=bool(change is not None and change.assessed),
    )

    labelled = bool(availability.labelled_synthetic) or any(
        item.labelled_synthetic for item in scenes
    )
    official = bool(scenes) and all(item.official_imagery for item in scenes) and not labelled
    acquisition = None
    resolution_m = None
    if scenes:
        dated = [item.acquisition_date for item in scenes if item.acquisition_date]
        if dated:
            acquisition = max(dated)
        vals = [item.spatial_resolution_m for item in scenes if item.spatial_resolution_m is not None]
        if vals:
            resolution_m = min(float(item) for item in vals)

    covers = None if location is None else location.covers_claimed_site
    scene_lat = next((item.scene_latitude for item in scenes if item.scene_latitude is not None), None)
    scene_lon = next((item.scene_longitude for item in scenes if item.scene_longitude is not None), None)
    gps_signals = _image_gps_signals(
        project_location=project_location,
        image_locations=image_locations,
        covers_project=covers,
        aoi_radius_m=aoi_radius_m,
        scene_lat=scene_lat,
        scene_lon=scene_lon,
    )
    confidence = satellite_confidence(
        data_mode=data_mode,
        overall=overall,
        imagery_available=bool(scenes) and unavailable_reason is None,
        resolution_sufficient=None if resolution is None else resolution.sufficient,
        labelled_synthetic=labelled,
        official_imagery=official,
    )
    explanation = build_explanation(
        overall=overall,
        unavailable_reason=unavailable_reason,
        location=location,
        resolution=resolution,
        temporal=temporal,
        change=change,
        labelled_synthetic=labelled,
    )
    return SatelliteResult(
        project_id=project_id,
        internal_project_id=internal_project_id,
        data_mode=data_mode,
        overall_result=overall,
        provider=availability.provider,
        imagery_available=bool(scenes) and unavailable_reason is None,
        acquisition_date=acquisition,
        spatial_resolution_m=resolution_m,
        coverage=_coverage_label(overall, covers),
        change_result=None if change is None else change.finding,
        evidence_confidence=confidence,
        confidence_label=confidence_label(confidence),
        project_location=project_location.as_dict(),
        availability=availability.as_dict(),
        location_analysis=None if location is None else location.as_dict(),
        temporal_analysis=None if temporal is None else temporal.as_dict(),
        change_analysis=None if change is None else change.as_dict(),
        resolution_analysis=None if resolution is None else resolution.as_dict(),
        image_gps_signals=[item.as_dict() for item in gps_signals],
        scenes=[item.as_dict() for item in scenes],
        work_scale=work_scale,
        limitations=list(LIMITATIONS),
        explanation=explanation,
        finding=overall_finding(overall),
        note=GOVERNANCE_NOTE,
        engine_version=ENGINE_VERSION,
        labelled_synthetic=labelled,
        official_imagery=official,
    )
