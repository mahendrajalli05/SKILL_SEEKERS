"""Material / reference-cost adapter.

Does not substitute a reference rate for project expenditure. Does not change
Cost Intelligence V1.1. Official SoR sources are UNAVAILABLE unless a verified
snapshot exists. HYBRID tests may use a labelled fixture.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.domain.enums import DataMode
from app.engines.context.adapters.base import load_or_unavailable, unavailable
from app.engines.context.constants import (
    ALLOCATION_UNIT,
    AP_SOR_SOURCE_ID,
    CPWD_SOURCE_ID,
    EXPENDITURE_UNIT,
    FAILURE_INCOMPATIBLE_UNIT,
    FAILURE_SOURCE_UNAVAILABLE,
    FAILURE_UNAVAILABLE_INDICATOR,
    GEO_STATE,
    HYBRID_COST_SOURCE_ID,
    HYBRID_FIXTURE_CONFIDENCE,
    INDICATOR_REFERENCE_COST,
    KIND_DERIVED_CONTEXT,
    KIND_OBSERVED_EXTERNAL,
    KIND_PROJECT_FACT,
    STATUS_AVAILABLE,
    STATUS_INCONCLUSIVE,
    STATUS_UNAVAILABLE,
    UNAVAILABLE_CONFIDENCE,
)
from app.engines.context.geography import GeoMatch, normalize_geo_key
from app.engines.context.registry import get_source
from app.engines.context.types import ContextObservation


def _work_tokens(text: str) -> set[str]:
    return {token for token in text.casefold().replace("/", " ").split() if len(token) > 3}


def observe_reference_cost(
    session: Session | None,
    *,
    data_mode: DataMode,
    geo: GeoMatch,
    allocation_amount: int | None,
    work_description: str | None,
    category: str | None,
) -> list[ContextObservation]:
    items: list[ContextObservation] = []
    items.append(
        ContextObservation(
            indicator="mplads_allocation",
            status=STATUS_AVAILABLE if allocation_amount is not None else STATUS_UNAVAILABLE,
            value=allocation_amount,
            unit=ALLOCATION_UNIT,
            geographic_level=None,
            geo_key=None,
            reference_year=None,
            reference_date=None,
            source_id="mplads_project_record",
            source_name="Cleaned MPLADS work-level extract",
            publisher="SARVSAKSHI observed field from public MPLADS extract",
            source_url=None,
            retrieval_date=None,
            dataset_version=None,
            transformation=None,
            limitations=["Allocation is not expenditure and is not a unit rate."],
            data_mode=data_mode,
            confidence=0.9 if allocation_amount is not None else UNAVAILABLE_CONFIDENCE,
            quality="project_observation",
            context_kind=KIND_PROJECT_FACT,
            failure_code=None if allocation_amount is not None else FAILURE_UNAVAILABLE_INDICATOR,
            notes="PROJECT-SPECIFIC FACT: recorded allocation_amount. Unit unspecified in source.",
        )
    )
    items.append(
        ContextObservation(
            indicator="mplads_expenditure",
            status=STATUS_UNAVAILABLE,
            value=None,
            unit=EXPENDITURE_UNIT,
            geographic_level=None,
            geo_key=None,
            reference_year=None,
            reference_date=None,
            source_id=None,
            source_name=None,
            publisher=None,
            source_url=None,
            retrieval_date=None,
            dataset_version=None,
            transformation=None,
            limitations=["The cleaned MPLADS extract has no utilised/spent amount."],
            data_mode=data_mode,
            confidence=UNAVAILABLE_CONFIDENCE,
            quality="unavailable",
            context_kind=KIND_PROJECT_FACT,
            failure_code=FAILURE_UNAVAILABLE_INDICATOR,
            notes="PROJECT-SPECIFIC FACT unavailable: expenditure is not in the extract. Not treated as zero.",
        )
    )

    for source_id in (CPWD_SOURCE_ID, AP_SOR_SOURCE_ID):
        source = get_source(source_id)
        items.append(
            unavailable(
                INDICATOR_REFERENCE_COST if source_id == CPWD_SOURCE_ID else f"{INDICATOR_REFERENCE_COST}:{source_id}",
                source,
                data_mode=data_mode,
                failure_code=(source.unavailable_reason if source else FAILURE_SOURCE_UNAVAILABLE)
                or FAILURE_SOURCE_UNAVAILABLE,
                notes=(
                    "Official schedule-of-rate source is not available as a verified "
                    "machine-readable public extract. No unofficial rates were substituted."
                ),
                geographic_level=GEO_STATE,
                geo_key=geo.key,
                context_kind=KIND_OBSERVED_EXTERNAL,
            )
        )

    hybrid_source = get_source(HYBRID_COST_SOURCE_ID)
    if data_mode == DataMode.REAL:
        items.append(
            unavailable(
                "reference_unit_rate_hybrid_fixture",
                hybrid_source,
                data_mode=DataMode.REAL,
                failure_code=FAILURE_SOURCE_UNAVAILABLE,
                notes="HYBRID/TEST reference-cost fixture is not used in REAL mode.",
                geographic_level=GEO_STATE,
                geo_key=geo.key,
                context_kind=KIND_OBSERVED_EXTERNAL,
            )
        )
        items.append(_inconclusive_comparison(data_mode, allocation_amount, None, None))
        return items

    if hybrid_source is None:
        items.append(_inconclusive_comparison(data_mode, allocation_amount, None, None))
        return items

    payload, error = load_or_unavailable(
        session,
        hybrid_source,
        INDICATOR_REFERENCE_COST,
        data_mode=data_mode,
        context_kind=KIND_OBSERVED_EXTERNAL,
        geo_key=geo.key,
        geographic_level=GEO_STATE,
    )
    if error is not None:
        items.append(error)
        items.append(_inconclusive_comparison(data_mode, allocation_amount, None, None))
        return items

    rates = payload.get("rates") if isinstance(payload, dict) else None
    if not isinstance(rates, list):
        items.append(
            unavailable(
                INDICATOR_REFERENCE_COST,
                hybrid_source,
                data_mode=data_mode,
                failure_code="MALFORMED_SOURCE",
                notes="HYBRID reference-cost fixture is malformed.",
                geographic_level=GEO_STATE,
                geo_key=geo.key,
                context_kind=KIND_OBSERVED_EXTERNAL,
            )
        )
        items.append(_inconclusive_comparison(data_mode, allocation_amount, None, None))
        return items

    haystack = f"{work_description or ''} {category or ''}"
    tokens = _work_tokens(haystack)
    chosen: dict[str, Any] | None = None
    for rate in rates:
        if not isinstance(rate, dict):
            continue
        geography = str(rate.get("geography") or "")
        if geo.key and normalize_geo_key(geography) not in {
            normalize_geo_key(geo.key),
            "",
        }:
            continue
        label = str(rate.get("work_type") or rate.get("material_or_work") or "")
        if _work_tokens(label) & tokens:
            chosen = rate
            break
    if chosen is None and rates:
        first = rates[0] if isinstance(rates[0], dict) else None
        chosen = first

    if not chosen:
        items.append(
            unavailable(
                INDICATOR_REFERENCE_COST,
                hybrid_source,
                data_mode=data_mode,
                failure_code=FAILURE_UNAVAILABLE_INDICATOR,
                notes="HYBRID fixture has no usable unit rate.",
                geographic_level=GEO_STATE,
                geo_key=geo.key,
                context_kind=KIND_OBSERVED_EXTERNAL,
            )
        )
        items.append(_inconclusive_comparison(data_mode, allocation_amount, None, None))
        return items

    unit = str(chosen.get("unit") or "sqm")
    rate_value = chosen.get("reference_rate")
    items.append(
        ContextObservation(
            indicator=INDICATOR_REFERENCE_COST,
            status=STATUS_AVAILABLE,
            value=rate_value,
            unit=f"INR_per_{unit}",
            geographic_level=GEO_STATE,
            geo_key=str(chosen.get("geography") or geo.key),
            reference_year=int(str(chosen.get("effective_date") or "2023")[:4])
            if chosen.get("effective_date")
            else 2023,
            reference_date=str(chosen.get("effective_date") or ""),
            source_id=hybrid_source.source_id,
            source_name=hybrid_source.source_name,
            publisher=hybrid_source.publisher,
            source_url=hybrid_source.url,
            retrieval_date=hybrid_source.retrieval_date,
            dataset_version=hybrid_source.dataset_version,
            transformation=hybrid_source.transformation_notes,
            limitations=list(hybrid_source.limitations),
            data_mode=DataMode.HYBRID if data_mode != DataMode.SYNTHETIC else DataMode.SYNTHETIC,
            confidence=HYBRID_FIXTURE_CONFIDENCE,
            quality="test_fixture",
            context_kind=KIND_OBSERVED_EXTERNAL,
            notes=(
                "OBSERVED EXTERNAL INDICATOR from a labelled HYBRID/TEST fixture. "
                "Not an official schedule of rates and not project expenditure. "
                f"Material/work: {chosen.get('material_or_work')}; unit: {unit}."
            ),
        )
    )
    items.append(_inconclusive_comparison(data_mode, allocation_amount, rate_value, f"INR_per_{unit}"))
    return items


def _inconclusive_comparison(
    data_mode: DataMode,
    allocation_amount: int | None,
    rate: object,
    rate_unit: str | None,
) -> ContextObservation:
    return ContextObservation(
        indicator="allocation_vs_reference_rate",
        status=STATUS_INCONCLUSIVE,
        value=None,
        unit=None,
        geographic_level=None,
        geo_key=None,
        reference_year=None,
        reference_date=None,
        source_id=None,
        source_name=None,
        publisher=None,
        source_url=None,
        retrieval_date=None,
        dataset_version=None,
        transformation=None,
        limitations=[
            "Total allocation and a unit rate are incompatible without a verified quantity in the same unit."
        ],
        data_mode=data_mode,
        confidence=UNAVAILABLE_CONFIDENCE,
        quality="incompatible_units",
        context_kind=KIND_DERIVED_CONTEXT,
        failure_code=FAILURE_INCOMPATIBLE_UNIT,
        derived=True,
        comparison={
            "allocation_amount": allocation_amount,
            "allocation_unit": ALLOCATION_UNIT,
            "reference_rate": rate,
            "reference_unit": rate_unit,
            "cost_v1_1_score_modified": False,
        },
        notes=(
            "DERIVED COMPARISON is INCONCLUSIVE: recorded allocation is a total amount with "
            "unspecified unit; external reference is a unit rate. No quantity is available. "
            "Cost Intelligence V1.1 was not modified."
        ),
    )
