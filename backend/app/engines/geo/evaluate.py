"""Compare project coordinates with reported image GPS."""

from __future__ import annotations

from app.engines.geo.confidence import image_check_confidence, overall_confidence
from app.engines.geo.constants import (
    DEFAULT_THRESHOLD_METERS,
    INCONCLUSIVE,
    LIMITATIONS,
    LOCATION_CONSISTENT,
    LOCATION_MISMATCH,
    MIXED_IMAGES_NOTE,
)
from app.engines.geo.distance import distance_pair
from app.engines.geo.explain import image_explanation, image_finding, overall_explanation, pce_framing
from app.engines.geo.types import (
    GeospatialResult,
    GeospatialSummary,
    ImageConsistency,
    ImageLocation,
    ProjectLocation,
)
from app.engines.geo.satellite import SatelliteCapability


def _mismatch_score(distance_meters: float, threshold_meters: float) -> float:
    if distance_meters <= threshold_meters:
        return 0.0
    extra = distance_meters - threshold_meters
    scaled = 50.0 + min(50.0, extra / max(threshold_meters, 1.0) * 10.0)
    return round(min(100.0, scaled), 1)


def classify_distance(distance_meters: float, threshold_meters: float) -> str:
    if distance_meters <= threshold_meters:
        return LOCATION_CONSISTENT
    return LOCATION_MISMATCH


def evaluate_image(
    *,
    image: ImageLocation,
    project_location: ProjectLocation,
    threshold_meters: float,
    data_mode,
) -> ImageConsistency:
    project_ok = project_location.available and project_location.latitude is not None and project_location.longitude is not None
    image_ok = image.gps_available and image.latitude is not None and image.longitude is not None
    distance_m: float | None = None
    distance_km: float | None = None
    result = INCONCLUSIVE
    score: float | None = None
    if not project_ok or not image_ok:
        result = INCONCLUSIVE
    else:
        distance_m, distance_km = distance_pair(
            float(project_location.latitude),
            float(project_location.longitude),
            float(image.latitude),
            float(image.longitude),
        )
        result = classify_distance(distance_m, threshold_meters)
        score = 0.0 if result == LOCATION_CONSISTENT else _mismatch_score(distance_m, threshold_meters)
    confidence = image_check_confidence(
        project_location=project_location,
        image_gps_available=bool(image_ok),
        metadata_confidence=image.confidence,
        data_mode=data_mode,
    )
    finding = image_finding(
        result=result,
        distance_meters=distance_m,
        threshold_meters=threshold_meters,
        project_available=bool(project_ok),
        image_gps_available=bool(image_ok),
    )
    explanation = image_explanation(
        result=result,
        distance_meters=distance_m,
        threshold_meters=threshold_meters,
        project_available=bool(project_ok),
        image_gps_available=bool(image_ok),
        synthetic_project=project_location.synthetic,
    )
    return ImageConsistency(
        image_id=image.image_id,
        location=image,
        result=result,
        distance_meters=None if distance_m is None else round(distance_m, 3),
        distance_km=None if distance_km is None else round(distance_km, 6),
        threshold_meters=threshold_meters,
        finding=finding,
        explanation=explanation,
        confidence=confidence,
        score=score,
    )


def summarize(images: list[ImageConsistency]) -> GeospatialSummary:
    distances = [item.distance_meters for item in images if item.distance_meters is not None]
    consistent = sum(1 for item in images if item.result == LOCATION_CONSISTENT)
    mismatch = sum(1 for item in images if item.result == LOCATION_MISMATCH)
    inconclusive = sum(1 for item in images if item.result == INCONCLUSIVE)
    gps_available = sum(1 for item in images if item.location.gps_available)
    return GeospatialSummary(
        image_count=len(images),
        gps_available_count=gps_available,
        gps_unavailable_count=sum(1 for item in images if not item.location.gps_available),
        consistent_count=consistent,
        mismatch_count=mismatch,
        inconclusive_count=inconclusive,
        mixed_results=(consistent > 0 and mismatch > 0) or (consistent > 0 and inconclusive > 0) or (mismatch > 0 and inconclusive > 0),
        distances_meters=[round(item, 3) for item in distances if item is not None],
    )


def overall_result(summary: GeospatialSummary, project_available: bool) -> str:
    if not project_available:
        return INCONCLUSIVE
    if summary.image_count == 0:
        return INCONCLUSIVE
    if summary.mismatch_count > 0:
        return LOCATION_MISMATCH
    if summary.consistent_count > 0 and summary.gps_unavailable_count == 0 and summary.inconclusive_count == 0:
        return LOCATION_CONSISTENT
    if summary.consistent_count > 0 and summary.mismatch_count == 0 and summary.gps_unavailable_count > 0:
        # One matching image does not make GPS-missing images trustworthy.
        return INCONCLUSIVE
    if summary.consistent_count > 0 and summary.mismatch_count == 0:
        return LOCATION_CONSISTENT
    return INCONCLUSIVE


def evaluate_project(
    *,
    project_id: int,
    internal_project_id: str,
    data_mode,
    project_location: ProjectLocation,
    image_locations: list[ImageLocation],
    threshold_meters: float = DEFAULT_THRESHOLD_METERS,
    satellite: SatelliteCapability | None = None,
) -> GeospatialResult:
    images = [
        evaluate_image(
            image=item,
            project_location=project_location,
            threshold_meters=threshold_meters,
            data_mode=data_mode,
        )
        for item in image_locations
    ]
    summary = summarize(images)
    overall = overall_result(summary, project_location.available)
    explanation = overall_explanation(
        overall=overall,
        project_location=project_location,
        images=images,
        mixed=summary.mixed_results,
    )
    if summary.mixed_results and MIXED_IMAGES_NOTE not in explanation:
        explanation = f"{explanation} {MIXED_IMAGES_NOTE}"
    return GeospatialResult(
        project_id=project_id,
        internal_project_id=internal_project_id,
        data_mode=data_mode,
        project_location=project_location,
        image_locations=image_locations,
        images=images,
        summary=summary,
        overall_result=overall,
        location_consistency=overall,
        threshold_meters=threshold_meters,
        evidence_confidence=overall_confidence(project_location, images, data_mode),
        satellite=satellite or SatelliteCapability(),
        plan_claim_evidence=pce_framing(
            overall=overall,
            images=images,
            project_location=project_location,
        ),
        explanation=explanation,
        limitations=list(LIMITATIONS),
    )
