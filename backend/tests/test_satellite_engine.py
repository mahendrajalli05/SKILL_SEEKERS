from __future__ import annotations

from datetime import date

from app.domain.enums import DataMode
from app.engines.citizen.constants import ENGINE_VERSION as CITIZEN_VERSION
from app.engines.compliance.constants import ENGINE_VERSION as COMPLIANCE_VERSION
from app.engines.cost.constants import ENGINE_VERSION as COST_VERSION
from app.engines.document.constants import ENGINE_VERSION as DOCUMENT_VERSION
from app.engines.forensics.constants import ENGINE_VERSION as FORENSICS_VERSION
from app.engines.fusion.constants import ENGINE_VERSION as FUSION_VERSION
from app.engines.fusion.constants import SIGNAL_TYPE_TO_SLOT
from app.engines.geo.constants import ENGINE_VERSION as GEO_VERSION
from app.engines.geo.types import ProjectLocation
from app.engines.graph.constants import ENGINE_VERSION as GRAPH_VERSION
from app.engines.image.constants import ENGINE_VERSION as IMAGE_VERSION
from app.engines.milestone.constants import ENGINE_VERSION as MILESTONE_VERSION
from app.engines.need.constants import ENGINE_VERSION as NEED_VERSION
from app.engines.overlap.constants import ENGINE_VERSION as OVERLAP_VERSION
from app.engines.pce.constants import ENGINE_VERSION as PCE_VERSION
from app.engines.satellite.analysis import analyze_change, analyze_coverage, analyze_resolution
from app.engines.satellite.constants import (
    ENGINE_VERSION,
    RESOLUTION_INSUFFICIENT_TEXT,
    SATELLITE_CONSISTENT,
    SATELLITE_INCONCLUSIVE,
    SATELLITE_INCONSISTENT,
    SATELLITE_UNAVAILABLE,
    SCENARIO_AVAILABLE,
    SCENARIO_CHANGE_DETECTED,
    SCENARIO_INSUFFICIENT_RESOLUTION,
    SCENARIO_MATCHING_LOCATION,
    SCENARIO_NO_CHANGE,
    SCENARIO_UNAVAILABLE,
    SCENARIO_WRONG_DATE,
    SCENARIO_WRONG_LOCATION,
)
from app.engines.satellite.dates import analyze_temporal, parse_claim_completion_date
from app.engines.satellite.evaluate import evaluate_satellite
from app.engines.satellite.providers.mock import MockSatelliteProvider
from app.engines.satellite.scale import classify_work_scale
from app.engines.satellite.types import ImageryRequest, ImageryScene
from app.engines.time.constants import ENGINE_VERSION as TIME_VERSION
from app.domain.enums import SignalType


def _location(available: bool = True) -> ProjectLocation:
    return ProjectLocation(
        project_id=7,
        latitude=18.1167 if available else None,
        longitude=83.4 if available else None,
        source="SYNTHETIC hybrid enrichment coordinates. Not official MPLADS GPS.",
        data_mode=DataMode.HYBRID,
        confidence=0.35,
        timestamp=None,
        provenance={"notes": "SYNTHETIC test coordinates"},
        available=available,
        synthetic=True,
    )


def _request(scenario: str, **overrides: object) -> ImageryRequest:
    values: dict[str, object] = {
        "latitude": 18.1167,
        "longitude": 83.4,
        "date_start": date(2025, 1, 1),
        "date_end": date(2025, 10, 31),
        "aoi_radius_m": 500.0,
        "data_mode": DataMode.HYBRID,
        "test_scenario": scenario,
        "work_scale": "LARGE_AREA",
    }
    values.update(overrides)
    return ImageryRequest(**values)  # type: ignore[arg-type]


def _evaluate(scenario: str, *, work_scale: str = "LARGE_AREA", claimed=date(2025, 10, 31), location=None):
    request = _request(scenario)
    availability = MockSatelliteProvider().fetch_scenes(request)
    return evaluate_satellite(
        project_id=7,
        internal_project_id="internal:sat:test",
        data_mode=DataMode.HYBRID,
        project_location=location or _location(),
        availability=availability,
        image_locations=[],
        work_scale=work_scale,
        planned_date=date(2025, 1, 1),
        claimed_completion=claimed,
        milestone_date=claimed,
    )


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
    assert GEO_VERSION == "geospatial-consistency-v1"
    assert NEED_VERSION == "need-impact-v1"
    assert MILESTONE_VERSION == "milestone-advisor-v1"
    assert CITIZEN_VERSION == "jan-sakshi-v1"
    assert FORENSICS_VERSION == "image-forensics-v1"
    assert ENGINE_VERSION == "satellite-remote-sensing-v1"
    assert SignalType.SATELLITE_AVAILABILITY not in SIGNAL_TYPE_TO_SLOT
    assert SignalType.SATELLITE_CHANGE not in SIGNAL_TYPE_TO_SLOT


def test_work_scale_resolution_limits() -> None:
    assert classify_work_scale("Construction of cement concrete road") == "LARGE_LINEAR"
    assert classify_work_scale("Construction of toilet block") == "SMALL_STRUCTURE"
    assert classify_work_scale("Community hall") == "LARGE_AREA"


def test_imagery_unavailable() -> None:
    result = _evaluate(SCENARIO_UNAVAILABLE)
    assert result.overall_result == SATELLITE_UNAVAILABLE
    assert result.imagery_available is False
    assert result.scenes == []
    assert "fraud" not in result.explanation.casefold()


def test_imagery_available_and_matching_location() -> None:
    available = _evaluate(SCENARIO_AVAILABLE)
    matching = _evaluate(SCENARIO_MATCHING_LOCATION)
    assert available.imagery_available is True
    assert matching.location_analysis["covers_claimed_site"] is True
    assert matching.overall_result == SATELLITE_CONSISTENT
    assert "consistent with available imagery" in matching.finding.casefold()
    assert matching.labelled_synthetic is True
    assert matching.official_imagery is False


def test_wrong_location() -> None:
    result = _evaluate(SCENARIO_WRONG_LOCATION)
    assert result.location_analysis["covers_claimed_site"] is False
    assert result.overall_result == SATELLITE_INCONSISTENT
    assert "inconsistent with available imagery" in result.finding.casefold()


def test_before_after_change_and_no_change() -> None:
    changed = _evaluate(SCENARIO_CHANGE_DETECTED)
    none = _evaluate(SCENARIO_NO_CHANGE)
    assert changed.change_analysis["visible_site_change"] is True
    assert changed.overall_result == SATELLITE_CONSISTENT
    assert none.change_analysis["visible_site_change"] is False
    assert none.overall_result == SATELLITE_INCONSISTENT
    assert "definitely completed" not in changed.explanation.casefold()
    assert "exact dimensions verified" not in changed.explanation.casefold()


def test_insufficient_resolution() -> None:
    result = _evaluate(SCENARIO_INSUFFICIENT_RESOLUTION, work_scale="SMALL_STRUCTURE")
    assert result.overall_result == SATELLITE_INCONCLUSIVE
    assert result.resolution_analysis["sufficient"] is False
    assert RESOLUTION_INSUFFICIENT_TEXT in result.resolution_analysis["finding"]
    assert RESOLUTION_INSUFFICIENT_TEXT in result.explanation


def test_wrong_imagery_date() -> None:
    result = _evaluate(SCENARIO_WRONG_DATE, claimed=date(2025, 10, 31))
    assert result.overall_result == SATELLITE_INCONCLUSIVE
    assert result.temporal_analysis["window_matches_claim"] is False
    assert "2024-01" in result.temporal_analysis["explanation"]
    assert "inconclusive for completion" in result.temporal_analysis["explanation"].casefold()


def test_missing_project_gps() -> None:
    request = _request(SCENARIO_AVAILABLE, latitude=None, longitude=None)
    availability = MockSatelliteProvider().fetch_scenes(request)
    result = evaluate_satellite(
        project_id=7,
        internal_project_id="internal:sat:nogps",
        data_mode=DataMode.HYBRID,
        project_location=_location(available=False),
        availability=availability,
        image_locations=[],
        work_scale="LARGE_AREA",
        planned_date=None,
        claimed_completion=None,
        milestone_date=None,
    )
    assert result.overall_result == SATELLITE_UNAVAILABLE
    assert result.imagery_available is False
    assert "were not invented" in result.explanation or "not invented" in result.explanation.casefold()


def test_parse_october_2025_claim_date() -> None:
    parsed = parse_claim_completion_date("Site development completed by October 2025.")
    assert parsed == date(2025, 10, 31)


def test_no_fraud_wording_and_deterministic() -> None:
    first = _evaluate(SCENARIO_CHANGE_DETECTED)
    second = _evaluate(SCENARIO_CHANGE_DETECTED)
    blob = (first.explanation + first.finding + first.note).casefold()
    assert "fraud" not in blob
    assert "definitely exists" not in blob
    assert first.overall_result == second.overall_result
    assert first.scenes == second.scenes
    assert first.explanation == second.explanation


def test_resolution_and_coverage_helpers() -> None:
    scene = ImageryScene(
        provider="test-mock",
        image_reference="TEST/x",
        acquisition_date="2025-11-12",
        spatial_resolution_m=30.0,
        cloud_cover_percent=5.0,
        quality="TEST",
        covers_site=True,
        official_imagery=False,
        labelled_synthetic=True,
    )
    resolution = analyze_resolution([scene], "SMALL_STRUCTURE")
    assert resolution.sufficient is False
    location = analyze_coverage(_location(), [scene], 500.0)
    assert location.result == SATELLITE_CONSISTENT
    change = analyze_change([scene], resolution)
    assert change.result == SATELLITE_INCONCLUSIVE
    temporal = analyze_temporal(
        [scene],
        planned_date=date(2025, 1, 1),
        claimed_completion=date(2025, 10, 31),
        milestone_date=None,
    )
    assert temporal.window_matches_claim is True
