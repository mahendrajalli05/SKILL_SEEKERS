"""Satellite provider abstraction for a later imagery backend.

V1 does not download or process satellite imagery. The implementation
is unavailable and must not fabricate results.
"""

from __future__ import annotations

from typing import Protocol

from app.engines.geo.constants import SATELLITE_EXPLANATION, SATELLITE_VERIFICATION_NOT_AVAILABLE
from app.engines.geo.types import ProjectLocation, SatelliteCapability


class SatelliteProvider(Protocol):
    def request_imagery(self, location: ProjectLocation) -> SatelliteCapability:
        """Request satellite imagery for a project location."""
        ...


class UnavailableSatelliteProvider:
    """Default V1 provider. Imagery is not available."""

    def request_imagery(self, location: ProjectLocation) -> SatelliteCapability:
        _ = location
        return SatelliteCapability(
            capability=SATELLITE_VERIFICATION_NOT_AVAILABLE,
            result=SATELLITE_VERIFICATION_NOT_AVAILABLE,
            available=False,
            imagery=None,
            explanation=SATELLITE_EXPLANATION,
        )


def default_satellite_provider() -> SatelliteProvider:
    return UnavailableSatelliteProvider()
