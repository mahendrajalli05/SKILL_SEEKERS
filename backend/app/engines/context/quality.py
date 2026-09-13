"""Quality controls for external contextual observations."""

from __future__ import annotations

from collections import Counter
from typing import Any

from app.engines.context.constants import (
    FAILURE_AMBIGUOUS_VERSION,
    FAILURE_INCOMPATIBLE_UNIT,
    FAILURE_INVALID_TRANSFORMATION,
    FAILURE_MISSING_VALUE,
    FAILURE_STALE_DATASET,
    POPULATION_MAX_PERSONS,
    POPULATION_MIN_PERSONS,
    STATUS_INCONCLUSIVE,
)
from app.engines.context.geography import normalize_geo_key
from app.engines.context.types import ContextObservation, SourceRecord


def provenance_complete(source: SourceRecord) -> list[str]:
    missing: list[str] = []
    if not source.source_name:
        missing.append("source_name")
    if not source.publisher:
        missing.append("publisher")
    if not (source.url or source.source_id):
        missing.append("url")
    if not source.retrieval_date:
        missing.append("retrieval_date")
    if not source.geographic_level:
        missing.append("geographic_level")
    return missing


def population_in_bounds(value: float | int | None) -> bool:
    if value is None:
        return False
    return POPULATION_MIN_PERSONS <= float(value) <= POPULATION_MAX_PERSONS


def duplicate_geo_year_keys(rows: list[dict[str, Any]]) -> list[str]:
    keys = [
        f"{normalize_geo_key(str(row.get('geo_key')))}|{row.get('reference_year')}"
        for row in rows
    ]
    counts = Counter(keys)
    return [key for key, count in counts.items() if count > 1]


def units_compatible(left: str | None, right: str | None) -> bool:
    if not left or not right:
        return False
    return left.strip().casefold() == right.strip().casefold()


def apply_observation_quality(
    observation: ContextObservation,
    *,
    expected_level: str | None = None,
    expected_unit: str | None = None,
    stale: bool = False,
    ambiguous_version: bool = False,
    invalid_transformation: bool = False,
) -> ContextObservation:
    if stale:
        observation.status = STATUS_INCONCLUSIVE
        observation.failure_code = FAILURE_STALE_DATASET
        observation.notes = (observation.notes + " Dataset exceeds documented freshness.").strip()
        observation.confidence = min(observation.confidence, 0.18)
        return observation
    if ambiguous_version:
        observation.status = STATUS_INCONCLUSIVE
        observation.failure_code = FAILURE_AMBIGUOUS_VERSION
        observation.notes = (observation.notes + " Source version is ambiguous.").strip()
        return observation
    if invalid_transformation:
        observation.status = STATUS_INCONCLUSIVE
        observation.failure_code = FAILURE_INVALID_TRANSFORMATION
        observation.value = None
        observation.notes = (observation.notes + " Transformation could not be validated.").strip()
        return observation
    if expected_level and observation.geographic_level and observation.geographic_level != expected_level:
        observation.status = STATUS_INCONCLUSIVE
        observation.failure_code = "UNSUPPORTED_GEOGRAPHY"
        observation.notes = (
            observation.notes
            + f" Geographic level {observation.geographic_level} is not {expected_level}."
        ).strip()
        return observation
    if expected_unit and observation.unit and not units_compatible(observation.unit, expected_unit):
        observation.status = STATUS_INCONCLUSIVE
        observation.failure_code = FAILURE_INCOMPATIBLE_UNIT
        observation.notes = (observation.notes + " Unit is incompatible with the expected unit.").strip()
        return observation
    if observation.status == "AVAILABLE" and observation.value is None:
        observation.status = STATUS_INCONCLUSIVE
        observation.failure_code = FAILURE_MISSING_VALUE
        observation.notes = (observation.notes + " Source row has no usable value.").strip()
    return observation
