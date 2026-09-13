"""State-level population adapter (MoHFW NCP projections)."""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.domain.enums import DataMode
from app.engines.context.adapters.base import load_or_unavailable, unavailable
from app.engines.context.constants import (
    FAILURE_MALFORMED_SOURCE,
    FAILURE_MISSING_VALUE,
    FAILURE_SOURCE_UNAVAILABLE,
    FAILURE_UNSUPPORTED_GEOGRAPHY,
    GEO_STATE,
    INDICATOR_STATE_POPULATION,
    KIND_OBSERVED_EXTERNAL,
    NEAREST_YEAR_CONFIDENCE,
    POPULATION_SOURCE_ID,
    REAL_CONFIDENCE,
    STATUS_AVAILABLE,
    STATUS_INCONCLUSIVE,
    UNAVAILABLE_CONFIDENCE,
)
from app.engines.context.geography import GeoMatch, normalize_geo_key
from app.engines.context.quality import (
    apply_observation_quality,
    duplicate_geo_year_keys,
    population_in_bounds,
)
from app.engines.context.registry import get_source
from app.engines.context.time_match import TimeMatch
from app.engines.context.types import ContextObservation


def _rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        rows = payload.get("rows")
        return [item for item in rows if isinstance(item, dict)] if isinstance(rows, list) else []
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def observe_state_population(
    session: Session | None,
    *,
    data_mode: DataMode,
    geo: GeoMatch,
    time_match: TimeMatch,
    recommended_date: date | str | None = None,
) -> ContextObservation:
    del recommended_date
    source = get_source(POPULATION_SOURCE_ID)
    if source is None:
        return unavailable(
            INDICATOR_STATE_POPULATION,
            None,
            data_mode=data_mode,
            failure_code=FAILURE_SOURCE_UNAVAILABLE,
            notes="Population source is missing from the registry.",
            context_kind=KIND_OBSERVED_EXTERNAL,
        )
    if geo.level != GEO_STATE or not geo.key:
        return ContextObservation(
            indicator=INDICATOR_STATE_POPULATION,
            status=geo.status,
            value=None,
            unit="persons",
            geographic_level=geo.level,
            geo_key=geo.key,
            reference_year=None,
            reference_date=None,
            source_id=source.source_id,
            source_name=source.source_name,
            publisher=source.publisher,
            source_url=source.url,
            retrieval_date=source.retrieval_date,
            dataset_version=source.dataset_version,
            transformation=source.transformation_notes,
            limitations=list(source.limitations) + [geo.reason],
            data_mode=data_mode,
            confidence=UNAVAILABLE_CONFIDENCE,
            quality="unavailable" if geo.status != STATUS_INCONCLUSIVE else "inconclusive",
            context_kind=KIND_OBSERVED_EXTERNAL,
            failure_code=geo.failure_code or FAILURE_UNSUPPORTED_GEOGRAPHY,
            notes=geo.reason,
        )

    payload, error = load_or_unavailable(
        session,
        source,
        INDICATOR_STATE_POPULATION,
        data_mode=data_mode,
        context_kind=KIND_OBSERVED_EXTERNAL,
        geo_key=geo.key,
        geographic_level=GEO_STATE,
    )
    if error is not None:
        return error

    rows = _rows(payload)
    if not rows:
        return unavailable(
            INDICATOR_STATE_POPULATION,
            source,
            data_mode=data_mode,
            failure_code=FAILURE_MALFORMED_SOURCE,
            notes="Population snapshot has no usable rows.",
            geographic_level=GEO_STATE,
            geo_key=geo.key,
            context_kind=KIND_OBSERVED_EXTERNAL,
        )
    dupes = duplicate_geo_year_keys(rows)
    if dupes:
        return ContextObservation(
            indicator=INDICATOR_STATE_POPULATION,
            status=STATUS_INCONCLUSIVE,
            value=None,
            unit="persons",
            geographic_level=GEO_STATE,
            geo_key=geo.key,
            reference_year=None,
            reference_date=None,
            source_id=source.source_id,
            source_name=source.source_name,
            publisher=source.publisher,
            source_url=source.url,
            retrieval_date=source.retrieval_date,
            dataset_version=source.dataset_version,
            transformation=source.transformation_notes,
            limitations=list(source.limitations),
            data_mode=data_mode,
            confidence=UNAVAILABLE_CONFIDENCE,
            quality="duplicate_records",
            context_kind=KIND_OBSERVED_EXTERNAL,
            failure_code=FAILURE_MALFORMED_SOURCE,
            notes="Duplicate state/year rows were found. No value was invented to resolve them.",
        )

    wanted_year = time_match.selected_year
    display_year = wanted_year
    if display_year is None:
        # Show a documented series year without claiming contemporaneous match.
        display_year = 2021
    needle = normalize_geo_key(geo.key)
    matches = [
        row
        for row in rows
        if normalize_geo_key(str(row.get("geo_key"))) == needle
        and int(row.get("reference_year") or 0) == int(display_year)
    ]
    if not matches:
        state_rows = [row for row in rows if normalize_geo_key(str(row.get("geo_key"))) == needle]
        if not state_rows:
            return unavailable(
                INDICATOR_STATE_POPULATION,
                source,
                data_mode=data_mode,
                failure_code=FAILURE_MISSING_VALUE,
                notes=f"No state-level population row matches '{geo.key}'.",
                geographic_level=GEO_STATE,
                geo_key=geo.key,
                context_kind=KIND_OBSERVED_EXTERNAL,
            )
        return ContextObservation(
            indicator=INDICATOR_STATE_POPULATION,
            status=STATUS_INCONCLUSIVE,
            value=None,
            unit="persons",
            geographic_level=GEO_STATE,
            geo_key=geo.key,
            reference_year=display_year,
            reference_date=None,
            source_id=source.source_id,
            source_name=source.source_name,
            publisher=source.publisher,
            source_url=source.url,
            retrieval_date=source.retrieval_date,
            dataset_version=source.dataset_version,
            transformation=source.transformation_notes,
            limitations=list(source.limitations) + [time_match.note],
            data_mode=data_mode,
            confidence=UNAVAILABLE_CONFIDENCE,
            quality="inconclusive",
            context_kind=KIND_OBSERVED_EXTERNAL,
            failure_code=FAILURE_MISSING_VALUE,
            notes=f"No snapshot row for {geo.key} in reference year {display_year}.",
        )

    row = matches[0]
    try:
        persons = int(row.get("persons"))
    except (TypeError, ValueError):
        return unavailable(
            INDICATOR_STATE_POPULATION,
            source,
            data_mode=data_mode,
            failure_code=FAILURE_MALFORMED_SOURCE,
            notes="Population value is not numeric.",
            geographic_level=GEO_STATE,
            geo_key=geo.key,
            context_kind=KIND_OBSERVED_EXTERNAL,
        )
    if not population_in_bounds(persons):
        return ContextObservation(
            indicator=INDICATOR_STATE_POPULATION,
            status=STATUS_INCONCLUSIVE,
            value=None,
            unit="persons",
            geographic_level=GEO_STATE,
            geo_key=geo.key,
            reference_year=int(row.get("reference_year") or display_year),
            reference_date=str(row.get("reference_date") or ""),
            source_id=source.source_id,
            source_name=source.source_name,
            publisher=source.publisher,
            source_url=source.url,
            retrieval_date=source.retrieval_date,
            dataset_version=source.dataset_version,
            transformation=source.transformation_notes,
            limitations=list(source.limitations),
            data_mode=data_mode,
            confidence=UNAVAILABLE_CONFIDENCE,
            quality="out_of_bounds",
            context_kind=KIND_OBSERVED_EXTERNAL,
            failure_code=FAILURE_MALFORMED_SOURCE,
            notes="Population value is outside the documented Table-21 range. The value was not used.",
        )

    status = STATUS_AVAILABLE
    confidence = REAL_CONFIDENCE if time_match.contemporaneous else NEAREST_YEAR_CONFIDENCE
    if not time_match.conclusive:
        status = STATUS_INCONCLUSIVE
        confidence = NEAREST_YEAR_CONFIDENCE
        # Keep the observed value visible with an explicit inconclusive time match.
        status = STATUS_AVAILABLE
        notes = (
            "OBSERVED EXTERNAL INDICATOR at STATE level. This is not a project-specific "
            "beneficiary count. " + time_match.note
        )
        quality = "observed_with_inconclusive_time_match"
    else:
        notes = (
            "OBSERVED EXTERNAL INDICATOR at STATE level. This is not a project-specific "
            "beneficiary count. " + time_match.note
        )
        quality = "observed"
        if time_match.method == "nearest_published_year":
            confidence = NEAREST_YEAR_CONFIDENCE

    observation = ContextObservation(
        indicator=INDICATOR_STATE_POPULATION,
        status=status,
        value=persons,
        unit="persons",
        geographic_level=GEO_STATE,
        geo_key=geo.key,
        reference_year=int(row.get("reference_year") or display_year),
        reference_date=str(row.get("reference_date") or f"{display_year}-03-01"),
        source_id=source.source_id,
        source_name=source.source_name,
        publisher=source.publisher,
        source_url=source.url,
        retrieval_date=source.retrieval_date,
        dataset_version=source.dataset_version,
        transformation=source.transformation_notes,
        limitations=list(source.limitations),
        data_mode=data_mode if data_mode != DataMode.HYBRID else DataMode.REAL,
        confidence=confidence,
        quality=quality,
        context_kind=KIND_OBSERVED_EXTERNAL,
        notes=notes,
    )
    if data_mode == DataMode.SYNTHETIC:
        observation.data_mode = DataMode.SYNTHETIC
        observation.notes = (
            observation.notes
            + " SYNTHETIC test project; not a government project. External figures remain cited."
        )
        observation.confidence = min(observation.confidence, 0.30)
    return apply_observation_quality(observation, expected_level=GEO_STATE, expected_unit="persons")
