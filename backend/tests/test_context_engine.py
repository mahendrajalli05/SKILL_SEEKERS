from __future__ import annotations

from datetime import date

from app.db import get_session_factory
from app.domain.enums import DataMode
from app.engines.context.constants import (
    FAILURE_INCOMPATIBLE_UNIT,
    FAILURE_REQUIRES_CONFIGURATION,
    FAILURE_UNSUPPORTED_GEOGRAPHY,
    INDICATOR_STATE_POPULATION,
    NEW_PROJECT_ASSESSMENT,
    STATUS_AVAILABLE,
    STATUS_INCONCLUSIVE,
    STATUS_UNAVAILABLE,
)
from app.engines.context.geography import match_project_geography
from app.engines.context.service import assess_new_project_context
from app.engines.context.time_match import match_reference_period
from app.engines.need.constants import ENGINE_VERSION as NEED_VERSION
from app.engines.need.service import assess_project_need_impact
from tests.need_test_support import insert_project


def _create(**overrides: object):
    session = get_session_factory()()
    try:
        row = insert_project(session, **overrides)
        session.commit()
        return row.id
    finally:
        session.close()


def test_real_state_population_is_observed_external_not_beneficiaries(client) -> None:
    pid = _create(internal_project_id="internal:context:pop")
    response = client.get(f"/api/v2/projects/{pid}/context", params={"data_mode": "REAL"})
    assert response.status_code == 200, response.text
    body = response.json()
    pop = next(item for item in body["observations"] if item["indicator"] == INDICATOR_STATE_POPULATION)
    assert pop["status"] == STATUS_AVAILABLE
    assert pop["value"] == 52_787_000
    assert pop["unit"] == "persons"
    assert pop["geographic_level"] == "STATE"
    assert pop["geo_key"] == "Andhra Pradesh"
    assert pop["reference_year"] == 2021
    assert pop["publisher"]
    assert pop["source_url"]
    assert pop["retrieval_date"]
    assert pop["context_kind"] == "OBSERVED_EXTERNAL_INDICATOR"
    assert pop["data_mode"] == "REAL"
    assert "beneficiary" in pop["notes"].casefold()
    assert body["cost_v1_1_unchanged"] is True
    assert body["need_impact_formula_unchanged"] is True
    assert body["risk_fusion_unchanged"] is True
    assert body["fraud_probability"] is None


def test_missing_state_is_unavailable_not_zero(client) -> None:
    pid = _create(internal_project_id="internal:context:no-state", state="")
    body = client.get(f"/api/v2/projects/{pid}/context", params={"data_mode": "REAL"}).json()
    pop = next(item for item in body["observations"] if item["indicator"] == INDICATOR_STATE_POPULATION)
    assert pop["status"] == STATUS_UNAVAILABLE
    assert pop["value"] is None
    assert pop["value"] != 0


def test_district_level_is_inconclusive(client) -> None:
    pid = _create(internal_project_id="internal:context:district")
    body = client.get(
        f"/api/v2/projects/{pid}/context",
        params={"data_mode": "REAL", "geographic_level": "DISTRICT"},
    ).json()
    pop = next(item for item in body["observations"] if item["indicator"] == INDICATOR_STATE_POPULATION)
    assert pop["status"] in {STATUS_INCONCLUSIVE, STATUS_UNAVAILABLE}
    assert pop["failure_code"] == FAILURE_UNSUPPORTED_GEOGRAPHY
    district = next(item for item in body["observations"] if item["indicator"] == "district_population")
    assert district["value"] is None


def test_reference_cost_does_not_replace_expenditure(client) -> None:
    pid = _create(internal_project_id="internal:context:cost")
    body = client.get(f"/api/v2/projects/{pid}/context", params={"data_mode": "REAL"}).json()
    allocation = next(item for item in body["observations"] if item["indicator"] == "mplads_allocation")
    spend = next(item for item in body["observations"] if item["indicator"] == "mplads_expenditure")
    comparison = next(item for item in body["observations"] if item["indicator"] == "allocation_vs_reference_rate")
    assert allocation["context_kind"] == "PROJECT_SPECIFIC_FACT"
    assert spend["status"] == STATUS_UNAVAILABLE
    assert spend["value"] is None
    assert comparison["status"] == STATUS_INCONCLUSIVE
    assert comparison["failure_code"] == FAILURE_INCOMPATIBLE_UNIT
    assert comparison["comparison"]["cost_v1_1_score_modified"] is False


def test_hybrid_fixture_not_used_in_real(client) -> None:
    pid = _create(internal_project_id="internal:context:hybrid-guard")
    body = client.get(f"/api/v2/projects/{pid}/context", params={"data_mode": "REAL"}).json()
    notes = " ".join(item["notes"] for item in body["observations"])
    assert "HYBRID/TEST reference-cost fixture is not used in REAL mode" in notes


def test_hybrid_uses_labelled_rate_fixture(client) -> None:
    pid = _create(internal_project_id="internal:context:hybrid-rate")
    body = client.get(f"/api/v2/projects/{pid}/context", params={"data_mode": "HYBRID"}).json()
    rate = next(
        item
        for item in body["observations"]
        if item["indicator"] == "reference_unit_rate" and item["status"] == STATUS_AVAILABLE
    )
    assert rate["data_mode"] == "HYBRID"
    assert "not an official" in rate["notes"].casefold()
    assert rate["unit"].startswith("INR_per_")


def test_data_gov_requires_configuration(client) -> None:
    pid = _create(internal_project_id="internal:context:datagov")
    body = client.get(f"/api/v2/projects/{pid}/context", params={"data_mode": "REAL"}).json()
    catalog = next(item for item in body["observations"] if item["indicator"] == "open_data_catalog")
    assert catalog["failure_code"] == FAILURE_REQUIRES_CONFIGURATION
    assert catalog["value"] is None


def test_new_project_assessment_is_labelled_and_not_persisted() -> None:
    result = assess_new_project_context(
        None,
        {
            "state": "Andhra Pradesh",
            "constituency": "KURNOOL",
            "category": "Drinking Water",
            "work_description": "Construction of water tanks",
            "allocation_amount": 250000,
            "recommendation_date": "2023-06-01",
            "data_mode": "REAL",
        },
    )
    assert result.assessment_kind == NEW_PROJECT_ASSESSMENT
    assert result.persisted is False
    assert result.project_id is None
    assert result.evidence_ids == []
    pop = next(item for item in result.observations if item.indicator == INDICATOR_STATE_POPULATION)
    assert pop.assessment_kind == NEW_PROJECT_ASSESSMENT
    assert "historical Evidence Objects" in " ".join(pop.limitations)


def test_need_formula_unchanged_when_context_exists(client) -> None:
    pid = _create(internal_project_id="internal:context:need-freeze")
    client.get(f"/api/v2/projects/{pid}/context", params={"data_mode": "REAL"})
    need = client.get(f"/api/v1/projects/{pid}/need-impact", params={"data_mode": "REAL"}).json()
    assert need["engine_version"] == NEED_VERSION
    assert need["priority_class"] == "INCONCLUSIVE"
    assert need["need_score"] is None


def test_time_match_nearest_year_is_documented() -> None:
    matched = match_reference_period(date(2023, 6, 1))
    assert matched.method == "nearest_published_year"
    assert matched.selected_year == 2021
    assert matched.gap_years == 2
    assert matched.conclusive is True
    assert "not exact contemporaneous" in matched.note.casefold()


def test_sources_endpoint_does_not_expose_filesystem_paths(client) -> None:
    body = client.get("/api/v2/context/sources").json()
    blob = str(body).casefold()
    assert "c:\\" not in blob
    assert "data/external" not in blob
    ids = {item["source_id"] for item in body["items"]}
    assert "mohfw_ncp_population_projections_2011_2036" in ids


def test_constituency_is_not_treated_as_state() -> None:
    geo = match_project_geography(
        state="Andhra Pradesh",
        constituency="VIZIANAGARAM",
        requested_level="CONSTITUENCY",
    )
    assert geo.status == STATUS_INCONCLUSIVE
    assert geo.failure_code == FAILURE_UNSUPPORTED_GEOGRAPHY


def test_malformed_snapshot_is_unavailable(monkeypatch) -> None:
    from pathlib import Path

    from app.engines.context import cache as cache_mod
    from app.engines.context.adapters.population import observe_state_population
    from app.engines.context.constants import FAILURE_MALFORMED_SOURCE

    fixture = Path(__file__).resolve().parent / "fixtures" / "context" / "malformed_population.json"
    monkeypatch.setattr(cache_mod, "snapshot_file", lambda _source: fixture)
    geo = match_project_geography(state="Andhra Pradesh", constituency="KURNOOL", requested_level="STATE")
    matched = match_reference_period(date(2021, 3, 1))
    item = observe_state_population(None, data_mode=DataMode.REAL, geo=geo, time_match=matched)
    assert item.status == STATUS_UNAVAILABLE
    assert item.failure_code == FAILURE_MALFORMED_SOURCE
    assert item.value is None


def test_stale_dataset_is_inconclusive() -> None:
    from app.engines.context.constants import FAILURE_STALE_DATASET, KIND_OBSERVED_EXTERNAL
    from app.engines.context.quality import apply_observation_quality
    from app.engines.context.types import ContextObservation

    item = ContextObservation(
        indicator=INDICATOR_STATE_POPULATION,
        status=STATUS_AVAILABLE,
        value=52_787_000,
        unit="persons",
        geographic_level="STATE",
        geo_key="Andhra Pradesh",
        reference_year=2021,
        reference_date="2021-03-01",
        source_id="mohfw_ncp_population_projections_2011_2036",
        source_name="Population Projections",
        publisher="MoHFW",
        source_url="https://main.mohfw.gov.in/",
        retrieval_date="2026-09-11",
        dataset_version="July 2020",
        transformation="thousands x 1000",
        limitations=[],
        data_mode=DataMode.REAL,
        confidence=0.82,
        quality="observed",
        context_kind=KIND_OBSERVED_EXTERNAL,
    )
    checked = apply_observation_quality(item, stale=True)
    assert checked.status == STATUS_INCONCLUSIVE
    assert checked.failure_code == FAILURE_STALE_DATASET


def test_live_fetch_timeout_is_not_substituted(monkeypatch) -> None:
    from app.engines.context.cache import fetch_remote_payload
    from app.engines.context.constants import FAILURE_TIMEOUT, POPULATION_SOURCE_ID
    from app.engines.context.registry import get_source

    class _Settings:
        context_live_fetch = True
        context_http_timeout_seconds = 0.01

    monkeypatch.setattr("app.engines.context.cache.get_settings", lambda: _Settings())
    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: (_ for _ in ()).throw(TimeoutError()))
    source = get_source(POPULATION_SOURCE_ID)
    assert source is not None
    payload, code, digest = fetch_remote_payload(source)
    assert payload is None
    assert digest is None
    assert code == FAILURE_TIMEOUT


def test_large_year_gap_is_inconclusive_time_match() -> None:
    matched = match_reference_period(date(2000, 1, 1))
    assert matched.conclusive is False
    assert matched.method == "gap_exceeds_threshold"


def test_synthetic_mode_is_labelled(client) -> None:
    pid = _create(internal_project_id="internal:context:synthetic", is_synthetic=True)
    body = client.get(f"/api/v2/projects/{pid}/context", params={"data_mode": "REAL"}).json()
    assert body["data_mode"] == "SYNTHETIC"
    pop = next(item for item in body["observations"] if item["indicator"] == INDICATOR_STATE_POPULATION)
    assert pop["data_mode"] == "SYNTHETIC"
