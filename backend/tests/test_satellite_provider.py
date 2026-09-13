from __future__ import annotations

from datetime import date

from app.domain.enums import DataMode
from app.engines.satellite.constants import (
    ENGINE_VERSION,
    MOCK_PROVIDER_LABEL,
    MOCK_PROVIDER_NAME,
    SATELLITE_UNAVAILABLE,
    SCENARIO_AVAILABLE,
    SCENARIO_UNAVAILABLE,
    UNAVAILABLE_NO_PROVIDER,
)
from app.engines.satellite.providers import (
    MockSatelliteProvider,
    UnavailableSatelliteProvider,
    resolve_provider,
)
from app.engines.satellite.types import ImageryRequest


def _request(**overrides: object) -> ImageryRequest:
    values: dict[str, object] = {
        "latitude": 18.1167,
        "longitude": 83.4,
        "date_start": date(2025, 1, 1),
        "date_end": date(2025, 11, 12),
        "aoi_radius_m": 500.0,
        "data_mode": DataMode.HYBRID,
        "test_scenario": SCENARIO_AVAILABLE,
        "work_scale": "LARGE_AREA",
    }
    values.update(overrides)
    return ImageryRequest(**values)  # type: ignore[arg-type]


def test_unavailable_provider_does_not_fabricate_imagery() -> None:
    result = UnavailableSatelliteProvider().fetch_scenes(_request(data_mode=DataMode.REAL))
    assert result.available is False
    assert result.scenes == []
    assert result.labelled_synthetic is False
    assert UNAVAILABLE_NO_PROVIDER in result.reason or "not fabricated" in result.reason.casefold()
    assert ENGINE_VERSION == "satellite-remote-sensing-v1"


def test_mock_provider_is_labelled_test_synthetic() -> None:
    result = MockSatelliteProvider().fetch_scenes(_request())
    assert result.available is True
    assert result.labelled_synthetic is True
    assert result.provider == MOCK_PROVIDER_NAME
    assert MOCK_PROVIDER_LABEL in result.reason or all(item.labelled_synthetic for item in result.scenes)
    for scene in result.scenes:
        assert scene.official_imagery is False
        assert scene.labelled_synthetic is True
        assert scene.image_reference.startswith("TEST/")
        assert "official" in scene.notes.casefold() or "not official" in MOCK_PROVIDER_LABEL.casefold()


def test_mock_unavailable_scenario_returns_no_scenes() -> None:
    result = MockSatelliteProvider().fetch_scenes(_request(test_scenario=SCENARIO_UNAVAILABLE))
    assert result.available is False
    assert result.scenes == []
    assert result.labelled_synthetic is True


def test_real_mode_never_resolves_mock_provider() -> None:
    provider = resolve_provider("mock", DataMode.REAL, allow_mock=True)
    result = provider.fetch_scenes(_request(data_mode=DataMode.REAL, test_scenario=SCENARIO_AVAILABLE))
    assert result.available is False
    assert result.scenes == []
    assert result.labelled_synthetic is False


def test_unconfigured_live_alias_is_unavailable() -> None:
    provider = resolve_provider("sentinel-2", DataMode.HYBRID, allow_mock=True)
    result = provider.check_availability(_request())
    assert result.available is False
    assert result.scenes == []
    assert "fabricated" in result.reason.casefold()


def test_registry_is_the_application_entry_point() -> None:
    unavailable = resolve_provider("unavailable", DataMode.HYBRID, allow_mock=False)
    mock = resolve_provider("mock", DataMode.HYBRID, allow_mock=True)
    assert isinstance(unavailable, UnavailableSatelliteProvider)
    assert isinstance(mock, MockSatelliteProvider)
    assert unavailable.name != mock.name
