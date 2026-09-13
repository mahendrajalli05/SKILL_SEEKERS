"""Infrastructure / development-need adapters.

NFHS-5 and Census district amenities are documented as UNAVAILABLE until a
verified machine-readable extract exists. Values are never invented.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.domain.enums import DataMode
from app.engines.context.adapters.base import unavailable
from app.engines.context.constants import (
    CENSUS_DISTRICT_SOURCE_ID,
    FAILURE_UNAVAILABLE_INDICATOR,
    FAILURE_UNSUPPORTED_GEOGRAPHY,
    GEO_STATE,
    INDICATOR_DRINKING_WATER,
    INDICATOR_HOUSEHOLD_ELECTRICITY,
    INDICATOR_INFRASTRUCTURE,
    INDICATOR_SANITATION,
    KIND_OBSERVED_EXTERNAL,
    NFHS_SOURCE_ID,
)
from app.engines.context.geography import GeoMatch
from app.engines.context.registry import get_source
from app.engines.context.types import ContextObservation


def _from_source(
    source_id: str,
    indicator: str,
    *,
    data_mode: DataMode,
    geo: GeoMatch,
    extra_note: str,
) -> ContextObservation:
    source = get_source(source_id)
    note = extra_note
    if source is not None:
        note = f"{extra_note} {source.unavailable_reason or 'SOURCE_UNAVAILABLE'}."
    return unavailable(
        indicator,
        source,
        data_mode=data_mode,
        failure_code=(source.unavailable_reason if source else FAILURE_UNAVAILABLE_INDICATOR)
        or FAILURE_UNAVAILABLE_INDICATOR,
        notes=note,
        geographic_level=geo.level or GEO_STATE,
        geo_key=geo.key,
        context_kind=KIND_OBSERVED_EXTERNAL,
    )


def observe_infrastructure(
    session: Session | None,
    *,
    data_mode: DataMode,
    geo: GeoMatch,
) -> list[ContextObservation]:
    del session
    items = [
        _from_source(
            NFHS_SOURCE_ID,
            INDICATOR_INFRASTRUCTURE,
            data_mode=data_mode,
            geo=geo,
            extra_note=(
                "No verified machine-readable NFHS-5 / Census amenity extract is bundled. "
                "Infrastructure availability is UNAVAILABLE rather than zero."
            ),
        ),
        _from_source(
            NFHS_SOURCE_ID,
            INDICATOR_HOUSEHOLD_ELECTRICITY,
            data_mode=data_mode,
            geo=geo,
            extra_note="Household electricity percentage was not transcribed from NFHS-5 PDFs.",
        ),
        _from_source(
            NFHS_SOURCE_ID,
            INDICATOR_DRINKING_WATER,
            data_mode=data_mode,
            geo=geo,
            extra_note="Improved drinking-water percentage was not transcribed from NFHS-5 PDFs.",
        ),
        _from_source(
            NFHS_SOURCE_ID,
            INDICATOR_SANITATION,
            data_mode=data_mode,
            geo=geo,
            extra_note="Improved sanitation percentage was not transcribed from NFHS-5 PDFs.",
        ),
    ]
    district = get_source(CENSUS_DISTRICT_SOURCE_ID)
    items.append(
        unavailable(
            "district_population",
            district,
            data_mode=data_mode,
            failure_code=FAILURE_UNSUPPORTED_GEOGRAPHY,
            notes=(
                "Census 2011 district PCA is not used. The MPLADS extract has no verified "
                "district field, and district is not fabricated from IDA or constituency."
            ),
            geographic_level="DISTRICT",
            geo_key=None,
            context_kind=KIND_OBSERVED_EXTERNAL,
        )
    )
    return items
