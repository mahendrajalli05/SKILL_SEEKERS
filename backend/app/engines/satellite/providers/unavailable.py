"""Default provider: no reliable imagery source is configured."""

from __future__ import annotations

from app.engines.satellite.constants import (
    MOCK_PROVIDER_NAME,
    PROVIDER_UNAVAILABLE,
    UNAVAILABLE_NO_PROVIDER,
)
from app.engines.satellite.types import ImageryAvailability, ImageryRequest


class UnavailableSatelliteProvider:
    """Used when no live satellite API/credentials are available."""

    name = PROVIDER_UNAVAILABLE

    def __init__(self, reason: str | None = None) -> None:
        self.reason = reason or UNAVAILABLE_NO_PROVIDER

    def check_availability(self, request: ImageryRequest) -> ImageryAvailability:
        _ = request
        return ImageryAvailability(
            available=False,
            provider=self.name,
            reason=self.reason,
            scenes=[],
            labelled_synthetic=False,
        )

    def fetch_scenes(self, request: ImageryRequest) -> ImageryAvailability:
        return self.check_availability(request)


class DisabledMockSatelliteProvider(UnavailableSatelliteProvider):
    """Returned when a caller asks for the TEST mock in REAL mode."""

    name = MOCK_PROVIDER_NAME

    def __init__(self) -> None:
        super().__init__(
            reason=(
                "TEST/SYNTHETIC mocked satellite responses are not used in REAL mode "
                "and are never presented as official imagery. "
                + UNAVAILABLE_NO_PROVIDER
            )
        )
