"""Resolve a satellite provider without hard-coding one vendor in callers."""

from __future__ import annotations

from app.domain.enums import DataMode
from app.engines.satellite.constants import PROVIDER_MOCK, PROVIDER_UNAVAILABLE
from app.engines.satellite.providers.base import SatelliteProvider
from app.engines.satellite.providers.mock import MockSatelliteProvider
from app.engines.satellite.providers.unavailable import (
    DisabledMockSatelliteProvider,
    UnavailableSatelliteProvider,
)

_LIVE_ALIASES = {
    "sentinel",
    "sentinel-2",
    "planetary-computer",
    "stac",
    "maxar",
    "planet",
}


def normalize_provider_name(value: str | None) -> str:
    text = str(value or PROVIDER_UNAVAILABLE).strip().lower().replace("_", "-")
    if text in {"", "none", "off", "disabled", PROVIDER_UNAVAILABLE}:
        return PROVIDER_UNAVAILABLE
    if text in {PROVIDER_MOCK, "test", "test-mock", "synthetic"}:
        return PROVIDER_MOCK
    if text in _LIVE_ALIASES:
        return text
    return PROVIDER_UNAVAILABLE


def resolve_provider(
    name: str | None,
    data_mode: DataMode,
    *,
    allow_mock: bool = False,
) -> SatelliteProvider:
    """Return a provider instance.

    REAL mode never receives mocked official-looking imagery.
    Unconfigured live aliases fall back to unavailable (no fabricated scenes).
    """
    key = normalize_provider_name(name)
    if key == PROVIDER_MOCK:
        if data_mode == DataMode.REAL or not allow_mock:
            return DisabledMockSatelliteProvider()
        return MockSatelliteProvider()
    if key in _LIVE_ALIASES:
        return UnavailableSatelliteProvider(
            reason=(
                f"Provider '{key}' is not configured with a reliable imagery API or credentials. "
                "The result is SATELLITE_UNAVAILABLE. No satellite imagery was fabricated."
            )
        )
    return UnavailableSatelliteProvider()
