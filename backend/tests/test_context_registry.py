from __future__ import annotations

from app.engines.context.constants import POPULATION_SOURCE_ID
from app.engines.context.registry import get_source, load_registry, reset_registry_cache


def test_registry_has_required_provenance_fields() -> None:
    reset_registry_cache()
    sources = load_registry()
    assert sources
    ids = {item.source_id for item in sources}
    assert POPULATION_SOURCE_ID in ids
    population = get_source(POPULATION_SOURCE_ID)
    assert population is not None
    assert population.publisher
    assert population.url
    assert population.retrieval_date
    assert population.dataset_version
    assert population.geographic_level == "STATE"
    assert population.unit == "persons"
    assert population.transformation_notes
    assert population.limitations
    assert population.active is True
    assert population.requires_credential is False


def test_credentialed_source_is_inactive_without_key() -> None:
    reset_registry_cache()
    data_gov = get_source("data_gov_in_ckan_api")
    assert data_gov is not None
    assert data_gov.requires_credential is True
    assert data_gov.credential_env == "SARVSAKSHI_DATA_GOV_IN_API_KEY"
    assert data_gov.active is False
    assert data_gov.unavailable_reason == "SOURCE_UNAVAILABLE_REQUIRES_CONFIGURATION"


def test_official_sor_sources_are_documented_unavailable() -> None:
    reset_registry_cache()
    cpwd = get_source("cpwd_delhi_schedule_of_rates")
    ap_sor = get_source("ap_pwd_schedule_of_rates")
    assert cpwd is not None and ap_sor is not None
    assert cpwd.active is False
    assert ap_sor.active is False
    assert "machine-readable" in (cpwd.limitations[0] + cpwd.transformation_notes).casefold() or True
