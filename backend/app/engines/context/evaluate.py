"""Compose contextual observations for a project or new-project assessment."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.domain.enums import DataMode
from app.engines.context.adapters.infrastructure import observe_infrastructure
from app.engines.context.adapters.population import observe_state_population
from app.engines.context.adapters.reference_cost import observe_reference_cost
from app.engines.context.constants import (
    DATA_GOV_SOURCE_ID,
    ENGINE_VERSION,
    FAILURE_REQUIRES_CONFIGURATION,
    GEO_STATE,
    GOVERNANCE_NOTE,
    KIND_OBSERVED_EXTERNAL,
    LIMITATIONS,
    NEW_PROJECT_ASSESSMENT,
)
from app.engines.context.adapters.base import credential_available, unavailable
from app.engines.context.geography import match_project_geography
from app.engines.context.registry import get_source
from app.engines.context.time_match import match_reference_period
from app.engines.context.types import ContextObservation, ContextResult


def evaluate_context(
    *,
    session: Session | None,
    data_mode: DataMode,
    internal_project_id: str,
    project_id: int | None,
    state: str | None,
    constituency: str | None,
    block: str | None = None,
    city: str | None = None,
    village: str | None = None,
    ward: str | None = None,
    ida: str | None = None,
    category: str | None = None,
    work_description: str | None = None,
    allocation_amount: int | None = None,
    recommended_date: date | str | None = None,
    assessment_kind: str | None = None,
    requested_level: str | None = None,
) -> ContextResult:
    geo = match_project_geography(
        state=state,
        constituency=constituency,
        block=block,
        city=city,
        village=village,
        ward=ward,
        ida=ida,
        requested_level=requested_level or GEO_STATE,
    )
    time_match = match_reference_period(recommended_date)
    observations: list[ContextObservation] = []
    observations.append(
        observe_state_population(
            session,
            data_mode=data_mode,
            geo=geo,
            time_match=time_match,
            recommended_date=recommended_date,
        )
    )
    observations.extend(observe_infrastructure(session, data_mode=data_mode, geo=geo))
    observations.extend(
        observe_reference_cost(
            session,
            data_mode=data_mode,
            geo=geo,
            allocation_amount=allocation_amount,
            work_description=work_description,
            category=category,
        )
    )

    data_gov = get_source(DATA_GOV_SOURCE_ID)
    if data_gov is not None and (data_gov.requires_credential and not credential_available(data_gov)):
        observations.append(
            unavailable(
                "open_data_catalog",
                data_gov,
                data_mode=data_mode,
                failure_code=FAILURE_REQUIRES_CONFIGURATION,
                notes=(
                    "data.gov.in requires an API key in SARVSAKSHI_DATA_GOV_IN_API_KEY. "
                    "No credential is configured. No live catalog was queried."
                ),
                geographic_level=GEO_STATE,
                geo_key=geo.key,
                context_kind=KIND_OBSERVED_EXTERNAL,
            )
        )

    if assessment_kind == NEW_PROJECT_ASSESSMENT:
        for item in observations:
            item.assessment_kind = NEW_PROJECT_ASSESSMENT
            item.limitations = list(item.limitations) + [
                "NEW_PROJECT_ASSESSMENT: no historical Evidence Objects, execution evidence, "
                "citizen evidence, project-specific expenditure, or project-specific beneficiaries."
            ]

    unavailable_items = [
        {
            "indicator": item.indicator,
            "status": item.status,
            "failure_code": item.failure_code,
            "source_id": item.source_id,
            "notes": item.notes,
        }
        for item in observations
        if item.status != "AVAILABLE"
    ]
    rec = recommended_date.isoformat() if isinstance(recommended_date, date) else (
        str(recommended_date) if recommended_date else None
    )
    return ContextResult(
        project_id=project_id,
        internal_project_id=internal_project_id,
        engine_version=ENGINE_VERSION,
        data_mode=data_mode,
        assessment_kind=assessment_kind,
        governance_note=GOVERNANCE_NOTE,
        requested_geographic_level=requested_level or GEO_STATE,
        matched_geographic_level=geo.level,
        project_state=geo.project_state,
        project_constituency=geo.project_constituency,
        recommended_date=rec,
        allocation_amount=allocation_amount,
        observations=observations,
        unavailable_indicators=unavailable_items,
        limitations=list(LIMITATIONS),
        processing_version=ENGINE_VERSION,
    )
