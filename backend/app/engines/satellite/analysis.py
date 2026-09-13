"""Site coverage, resolution, and basic change analyses.

Only analyses that can be defended from available metadata/observations.
Does not infer exact dimensions, floor count, expenditure, or quantity.
"""

from __future__ import annotations

from app.engines.geo.distance import haversine_m
from app.engines.satellite.constants import (
    HIGH_CLOUD_COVER_PERCENT,
    RESOLUTION_INSUFFICIENT_TEXT,
    SATELLITE_CONSISTENT,
    SATELLITE_INCONCLUSIVE,
    SATELLITE_INCONSISTENT,
)
from app.engines.satellite.scale import useful_gsd_limit_m
from app.engines.geo.types import ProjectLocation
from app.engines.satellite.types import (
    ChangeAnalysis,
    ImageryScene,
    LocationAnalysis,
    ResolutionAnalysis,
)


def analyze_coverage(
    location: ProjectLocation,
    scenes: list[ImageryScene],
    aoi_radius_m: float,
) -> LocationAnalysis:
    if not location.available or location.latitude is None or location.longitude is None:
        return LocationAnalysis(
            result=SATELLITE_INCONCLUSIVE,
            covers_claimed_site=None,
            finding="Claimed site coordinates are unavailable.",
            explanation=(
                "Insufficient imagery evidence for site coverage. "
                "Project GPS was not invented."
            ),
        )
    if not scenes:
        return LocationAnalysis(
            result=SATELLITE_INCONCLUSIVE,
            covers_claimed_site=None,
            finding="No imagery scenes are available to test site coverage.",
            explanation="Insufficient imagery evidence. Unrelated imagery was not substituted.",
        )
    covering = [item for item in scenes if item.covers_site is True]
    not_covering = [item for item in scenes if item.covers_site is False]
    distance: float | None = None
    for scene in scenes:
        if scene.scene_latitude is None or scene.scene_longitude is None:
            continue
        distance = round(
            haversine_m(
                float(location.latitude),
                float(location.longitude),
                float(scene.scene_latitude),
                float(scene.scene_longitude),
            ),
            1,
        )
        if scene.covers_site is None and distance <= aoi_radius_m:
            covering.append(scene)
        elif scene.covers_site is None and distance > aoi_radius_m:
            not_covering.append(scene)
    if covering and not not_covering:
        return LocationAnalysis(
            result=SATELLITE_CONSISTENT,
            covers_claimed_site=True,
            finding="Available imagery covers the claimed site.",
            explanation=(
                "Consistent with available imagery for site coverage. "
                "Coverage does not prove that the claimed work exists or is complete."
            ),
            distance_to_scene_m=distance,
        )
    if not_covering and not covering:
        return LocationAnalysis(
            result=SATELLITE_INCONSISTENT,
            covers_claimed_site=False,
            finding="Available imagery does not cover the claimed site.",
            explanation=(
                "Inconsistent with available imagery for site coverage. "
                "Unrelated imagery was not treated as covering the claimed coordinates."
            ),
            distance_to_scene_m=distance,
        )
    return LocationAnalysis(
        result=SATELLITE_INCONCLUSIVE,
        covers_claimed_site=None,
        finding="Site coverage could not be determined reliably from available scenes.",
        explanation="Insufficient imagery evidence for a location-consistency conclusion.",
        distance_to_scene_m=distance,
    )


def analyze_resolution(scenes: list[ImageryScene], work_scale: str) -> ResolutionAnalysis:
    limit = useful_gsd_limit_m(work_scale)
    resolutions = [
        float(item.spatial_resolution_m)
        for item in scenes
        if item.spatial_resolution_m is not None
    ]
    if not scenes:
        return ResolutionAnalysis(
            result=SATELLITE_INCONCLUSIVE,
            work_scale=work_scale,
            spatial_resolution_m=None,
            useful_gsd_limit_m=limit,
            sufficient=None,
            finding="No spatial resolution is available.",
            explanation="Insufficient imagery evidence. Resolution was not invented.",
        )
    if not resolutions:
        return ResolutionAnalysis(
            result=SATELLITE_INCONCLUSIVE,
            work_scale=work_scale,
            spatial_resolution_m=None,
            useful_gsd_limit_m=limit,
            sufficient=None,
            finding="Spatial resolution is unknown.",
            explanation=(
                "Insufficient imagery evidence. "
                + RESOLUTION_INSUFFICIENT_TEXT
            ),
        )
    best = min(resolutions)
    cloudy = [
        item
        for item in scenes
        if item.cloud_cover_percent is not None
        and float(item.cloud_cover_percent) > HIGH_CLOUD_COVER_PERCENT
    ]
    if cloudy and len(cloudy) == len(scenes):
        return ResolutionAnalysis(
            result=SATELLITE_INCONCLUSIVE,
            work_scale=work_scale,
            spatial_resolution_m=best,
            useful_gsd_limit_m=limit,
            sufficient=False,
            finding="Cloud cover is too high for reliable site observation.",
            explanation="Insufficient imagery evidence because of cloud/quality limitations.",
        )
    if best > limit:
        return ResolutionAnalysis(
            result=SATELLITE_INCONCLUSIVE,
            work_scale=work_scale,
            spatial_resolution_m=best,
            useful_gsd_limit_m=limit,
            sufficient=False,
            finding=RESOLUTION_INSUFFICIENT_TEXT,
            explanation=(
                f"{RESOLUTION_INSUFFICIENT_TEXT} Work scale {work_scale} "
                f"needs spatial resolution at or below {limit} m; available imagery is {best} m. "
                "A binary physical-verification result was not forced."
            ),
        )
    return ResolutionAnalysis(
        result=SATELLITE_CONSISTENT,
        work_scale=work_scale,
        spatial_resolution_m=best,
        useful_gsd_limit_m=limit,
        sufficient=True,
        finding="Spatial resolution is potentially sufficient for site-level observation.",
        explanation=(
            f"Available spatial resolution {best} m is within the prototype useful limit "
            f"of {limit} m for work scale {work_scale}. This does not verify physical measurements."
        ),
    )


def analyze_change(scenes: list[ImageryScene], resolution: ResolutionAnalysis) -> ChangeAnalysis:
    if resolution.sufficient is not True:
        return ChangeAnalysis(
            result=SATELLITE_INCONCLUSIVE,
            finding="Change detection was not assessed because resolution or coverage is insufficient.",
            explanation=(
                RESOLUTION_INSUFFICIENT_TEXT
                if resolution.sufficient is False
                else "Insufficient imagery evidence for change detection."
            ),
            assessed=False,
        )
    before = next((item for item in scenes if item.role == "before"), None)
    after = next((item for item in scenes if item.role == "after"), None)
    if before is None or after is None:
        observed = [item.visible_site_change for item in scenes if item.visible_site_change is not None]
        if not observed:
            return ChangeAnalysis(
                result=SATELLITE_INCONCLUSIVE,
                finding="No before/after pair or change observation is available.",
                explanation=(
                    "Insufficient imagery evidence for change detection. "
                    "Exact building dimensions, floor count, and expenditure were not inferred."
                ),
                assessed=False,
            )
        changed = any(observed)
        return ChangeAnalysis(
            result=SATELLITE_CONSISTENT if changed else SATELLITE_INCONCLUSIVE,
            finding=(
                "Potential site change recorded in available observations."
                if changed
                else "No visible site-level change was recorded in available observations."
            ),
            explanation=(
                "Consistent with available imagery for a site-level change observation."
                if changed
                else (
                    "Insufficient imagery evidence to confirm physical change. "
                    "Absence of a recorded change observation is not proof that no work exists."
                )
            ),
            visible_site_change=changed,
            assessed=True,
        )
    if before.visible_site_change is None or after.visible_site_change is None:
        return ChangeAnalysis(
            result=SATELLITE_INCONCLUSIVE,
            finding="Before/after imagery exists but no defensible change observation is available.",
            explanation=(
                "Insufficient imagery evidence for change detection. "
                "Pixel-level computer vision was not fabricated."
            ),
            before_reference=before.image_reference,
            after_reference=after.image_reference,
            assessed=False,
        )
    changed = bool(after.visible_site_change)
    if changed:
        return ChangeAnalysis(
            result=SATELLITE_CONSISTENT,
            finding="Potential site-level change detected between before and after observations.",
            explanation=(
                "Consistent with available imagery: a labelled site-level change observation "
                "is present on the later scene. This is not exact quantity or completion proof."
            ),
            before_reference=before.image_reference,
            after_reference=after.image_reference,
            visible_site_change=True,
            assessed=True,
        )
    return ChangeAnalysis(
        result=SATELLITE_INCONSISTENT,
        finding="No visible site-level change was recorded between before and after observations.",
        explanation=(
            "Inconsistent with available imagery for a claimed site-level change, "
            "where resolution permits a site-level observation. "
            "This does not prove that no work exists and is not a legal finding."
        ),
        before_reference=before.image_reference,
        after_reference=after.image_reference,
        visible_site_change=False,
        assessed=True,
    )
