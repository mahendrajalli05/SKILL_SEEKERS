from __future__ import annotations

from app.engines.geo.constants import SATELLITE_VERIFICATION_NOT_AVAILABLE
from app.engines.geo.satellite import default_satellite_provider
from app.engines.geo.types import ProjectLocation
from app.domain.enums import DataMode


def test_default_provider_does_not_fabricate_imagery() -> None:
    location = ProjectLocation(
        project_id=7,
        latitude=17.7,
        longitude=83.0,
        source="SYNTHETIC hybrid enrichment coordinates. Not official MPLADS GPS.",
        data_mode=DataMode.HYBRID,
        confidence=0.35,
        timestamp=None,
        provenance={},
        available=True,
        synthetic=True,
    )
    result = default_satellite_provider().request_imagery(location)
    assert result.capability == SATELLITE_VERIFICATION_NOT_AVAILABLE
    assert result.result == SATELLITE_VERIFICATION_NOT_AVAILABLE
    assert result.available is False
    assert result.imagery is None
    assert result.as_dict()["score"] is None
    assert "downloaded" in result.explanation.casefold() or "not processed" in result.explanation.casefold()
    assert "not available" in result.explanation.casefold()
