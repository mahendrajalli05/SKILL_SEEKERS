"""Satellite provider abstraction.

Application code must request imagery through this interface so a
single vendor is not hard-coded throughout the system.
"""

from __future__ import annotations

from typing import Protocol

from app.engines.satellite.types import ImageryAvailability, ImageryRequest


class SatelliteProvider(Protocol):
    name: str

    def check_availability(self, request: ImageryRequest) -> ImageryAvailability:
        """Return whether imagery exists for the coordinates, window, and AOI."""
        ...

    def fetch_scenes(self, request: ImageryRequest) -> ImageryAvailability:
        """Return imagery metadata/scenes. Must not fabricate official imagery."""
        ...
