"""TEST/SYNTHETIC mocked satellite provider.

Controlled testing only. Responses are labelled and must never be shown
as official government or commercial satellite imagery. No image files
are generated or presented as real remote-sensing products.
"""

from __future__ import annotations

from datetime import date, timedelta

from app.engines.satellite.constants import (
    ALLOWED_TEST_SCENARIOS,
    MOCK_PROVIDER_LABEL,
    MOCK_PROVIDER_NAME,
    SCENARIO_AVAILABLE,
    SCENARIO_CHANGE_DETECTED,
    SCENARIO_INSUFFICIENT_RESOLUTION,
    SCENARIO_MATCHING_LOCATION,
    SCENARIO_NO_CHANGE,
    SCENARIO_UNAVAILABLE,
    SCENARIO_WRONG_DATE,
    SCENARIO_WRONG_LOCATION,
    UNAVAILABLE_NO_SCENES,
)
from app.engines.satellite.types import ImageryAvailability, ImageryRequest, ImageryScene


def _ref(scenario: str, role: str) -> str:
    return f"TEST/{MOCK_PROVIDER_NAME}/{scenario}/{role}"


def _scene(
    request: ImageryRequest,
    *,
    scenario: str,
    role: str,
    acquisition: date,
    resolution_m: float,
    covers_site: bool,
    visible_site_change: bool | None = None,
    offset_deg: float = 0.0,
) -> ImageryScene:
    lat = None if request.latitude is None else request.latitude + offset_deg
    lon = None if request.longitude is None else request.longitude + offset_deg
    return ImageryScene(
        provider=MOCK_PROVIDER_NAME,
        image_reference=_ref(scenario, role),
        acquisition_date=acquisition.isoformat(),
        spatial_resolution_m=resolution_m,
        cloud_cover_percent=8.0,
        quality="TEST_METADATA_ONLY",
        covers_site=covers_site,
        scene_latitude=lat,
        scene_longitude=lon,
        official_imagery=False,
        labelled_synthetic=True,
        visible_site_change=visible_site_change,
        notes=MOCK_PROVIDER_LABEL,
        role=role,
    )


def _anchor_date(request: ImageryRequest) -> date:
    if request.date_end is not None:
        return request.date_end
    if request.date_start is not None:
        return request.date_start
    return date(2025, 11, 12)


class MockSatelliteProvider:
    """Labelled TEST/SYNTHETIC metadata responses for HYBRID/SYNTHETIC tests."""

    name = MOCK_PROVIDER_NAME

    def check_availability(self, request: ImageryRequest) -> ImageryAvailability:
        return self.fetch_scenes(request)

    def fetch_scenes(self, request: ImageryRequest) -> ImageryAvailability:
        scenario = (request.test_scenario or SCENARIO_AVAILABLE).strip().lower()
        if scenario not in ALLOWED_TEST_SCENARIOS:
            scenario = SCENARIO_AVAILABLE
        if request.latitude is None or request.longitude is None:
            return ImageryAvailability(
                available=False,
                provider=self.name,
                reason=UNAVAILABLE_NO_SCENES,
                scenes=[],
                labelled_synthetic=True,
            )
        scenes = self._scenes_for(scenario, request)
        available = len(scenes) > 0
        return ImageryAvailability(
            available=available,
            provider=self.name,
            reason=(
                MOCK_PROVIDER_LABEL
                if available
                else f"{UNAVAILABLE_NO_SCENES} {MOCK_PROVIDER_LABEL}"
            ),
            scenes=scenes,
            labelled_synthetic=True,
        )

    def _scenes_for(self, scenario: str, request: ImageryRequest) -> list[ImageryScene]:
        anchor = _anchor_date(request)
        if scenario == SCENARIO_UNAVAILABLE:
            return []
        if scenario == SCENARIO_WRONG_LOCATION:
            return [
                _scene(
                    request,
                    scenario=scenario,
                    role="scene",
                    acquisition=anchor,
                    resolution_m=0.5,
                    covers_site=False,
                    offset_deg=0.8,
                )
            ]
        if scenario == SCENARIO_INSUFFICIENT_RESOLUTION:
            return [
                _scene(
                    request,
                    scenario=scenario,
                    role="scene",
                    acquisition=anchor,
                    resolution_m=30.0,
                    covers_site=True,
                )
            ]
        if scenario == SCENARIO_WRONG_DATE:
            return [
                _scene(
                    request,
                    scenario=scenario,
                    role="scene",
                    acquisition=date(2024, 1, 10),
                    resolution_m=0.5,
                    covers_site=True,
                )
            ]
        if scenario == SCENARIO_CHANGE_DETECTED:
            before = (request.date_start or anchor) - timedelta(days=280)
            after = max(anchor, date(2025, 11, 12))
            return [
                _scene(
                    request,
                    scenario=scenario,
                    role="before",
                    acquisition=before,
                    resolution_m=0.5,
                    covers_site=True,
                    visible_site_change=False,
                ),
                _scene(
                    request,
                    scenario=scenario,
                    role="after",
                    acquisition=after,
                    resolution_m=0.5,
                    covers_site=True,
                    visible_site_change=True,
                ),
            ]
        if scenario == SCENARIO_NO_CHANGE:
            before = (request.date_start or anchor) - timedelta(days=280)
            after = max(anchor, date(2025, 11, 12))
            return [
                _scene(
                    request,
                    scenario=scenario,
                    role="before",
                    acquisition=before,
                    resolution_m=0.5,
                    covers_site=True,
                    visible_site_change=False,
                ),
                _scene(
                    request,
                    scenario=scenario,
                    role="after",
                    acquisition=after,
                    resolution_m=0.5,
                    covers_site=True,
                    visible_site_change=False,
                ),
            ]
        if scenario in {SCENARIO_AVAILABLE, SCENARIO_MATCHING_LOCATION}:
            return [
                _scene(
                    request,
                    scenario=scenario,
                    role="scene",
                    acquisition=anchor,
                    resolution_m=0.5,
                    covers_site=True,
                )
            ]
        return [
            _scene(
                request,
                scenario=SCENARIO_AVAILABLE,
                role="scene",
                acquisition=anchor,
                resolution_m=0.5,
                covers_site=True,
            )
        ]
