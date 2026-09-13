from __future__ import annotations

from app.engines.compliance.constants import ENGINE_VERSION as COMPLIANCE_VERSION
from app.engines.cost.constants import ENGINE_VERSION as COST_VERSION
from app.engines.document.constants import ENGINE_VERSION as DOCUMENT_VERSION
from app.engines.fusion.constants import ENGINE_VERSION as FUSION_VERSION
from app.engines.geo.constants import ENGINE_VERSION, DEFAULT_THRESHOLD_METERS
from app.engines.graph.constants import ENGINE_VERSION as GRAPH_VERSION
from app.engines.image.constants import ENGINE_VERSION as IMAGE_VERSION
from app.engines.overlap.constants import ENGINE_VERSION as OVERLAP_VERSION
from app.engines.pce.constants import ENGINE_VERSION as PCE_VERSION
from app.engines.time.constants import ENGINE_VERSION as TIME_VERSION
from app.engines.geo.satellite import UnavailableSatelliteProvider
from app.engines.geo.types import ProjectLocation
from app.domain.enums import DataMode


def test_frozen_engines_unchanged() -> None:
    assert COST_VERSION == "cost-peer-v1.1"
    assert TIME_VERSION == "time-peer-v1"
    assert OVERLAP_VERSION == "overlap-multi-v1"
    assert COMPLIANCE_VERSION == "compliance-rules-v1"
    assert FUSION_VERSION == "risk-fusion-v1.1"
    assert GRAPH_VERSION == "relationship-graph-v1"
    assert PCE_VERSION == "plan-claim-evidence-v1"
    assert DOCUMENT_VERSION == "document-blueprint-v1"
    assert IMAGE_VERSION == "image-evidence-v1"
    assert ENGINE_VERSION == "geospatial-consistency-v1"
    assert DEFAULT_THRESHOLD_METERS == 500.0


def test_satellite_provider_is_unavailable() -> None:
    location = ProjectLocation(
        project_id=1,
        latitude=15.9,
        longitude=80.0,
        source="SYNTHETIC",
        data_mode=DataMode.HYBRID,
        confidence=0.35,
        timestamp=None,
        provenance={},
        available=True,
        synthetic=True,
    )
    result = UnavailableSatelliteProvider().request_imagery(location)
    assert result.available is False
    assert result.imagery is None
    assert result.result == "SATELLITE_VERIFICATION_NOT_AVAILABLE"
    assert "not downloaded" in result.explanation or "not available" in result.explanation.casefold()
    assert "fraud" not in result.explanation.casefold()
