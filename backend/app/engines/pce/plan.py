"""Assemble a Plan view from observed project fields, overlay, and optional HYBRID enrichment.

REAL mode never consumes synthetic enrichment. Missing government values stay unavailable.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from app.domain.enums import DataMode, SourceType
from app.engines.pce.constants import ENGINE_VERSION, UNAVAILABLE_DIMENSIONS_REASON
from app.engines.pce.types import AssembledPlan, PlanField
from app.evidence.constants import (
    HYBRID_ENRICHMENT_RELATIVE_PATH,
    HYBRID_PROVENANCE_NOTE,
    REAL_PROVENANCE_NOTE,
    SYNTHETIC_PROVENANCE_NOTE,
)
from app.models.plan import Plan
from app.models.project import Project
from app.search.enrichment_display import SyntheticEnrichmentDisplay, enrichment_for


def _iso(value: date | datetime | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    return value.isoformat()


def _field(
    name: str,
    value: Any,
    *,
    data_mode: DataMode,
    source: str,
    synthetic: bool = False,
    unavailable_reason: str | None = None,
) -> PlanField:
    available = value is not None and value != ""
    return PlanField(
        name=name,
        value=value if available else None,
        available=available,
        data_mode=data_mode,
        synthetic=synthetic,
        source=source,
        unavailable_reason=None if available else unavailable_reason,
    )


def assemble_plan(
    project: Project,
    stored: Plan | None,
    *,
    data_mode: DataMode,
    enrichment: SyntheticEnrichmentDisplay | None = None,
) -> AssembledPlan:
    if data_mode == DataMode.REAL:
        enrichment = None
    elif data_mode == DataMode.HYBRID and enrichment is None:
        enrichment = enrichment_for(project.internal_project_id)

    overlay_mode = DataMode(stored.data_mode) if stored is not None else data_mode
    scope = stored.sanctioned_scope if stored and stored.sanctioned_scope else project.work_description
    scope_source = (
        "recorded plan overlay"
        if stored and stored.sanctioned_scope
        else "project.work_description"
    )
    budget: float | None
    budget_from_extract = False
    budget_source: str
    if stored is not None and stored.budget_estimate is not None:
        budget = float(stored.budget_estimate)
        budget_source = "recorded plan overlay"
    elif project.allocation_amount is not None:
        budget = float(project.allocation_amount)
        budget_from_extract = True
        budget_source = "project.allocation_amount"
    else:
        budget = None
        budget_source = "unavailable"

    dimensions = stored.dimensions_value if stored is not None else None
    dimensions_unit = stored.dimensions_unit if stored is not None else None
    blueprint_id = stored.blueprint_document_id if stored is not None else None

    milestone_label = stored.milestone_label if stored is not None else None
    milestone_amount = stored.milestone_amount if stored is not None else None
    planned_start = _iso(stored.planned_start_date) if stored is not None else None
    planned_end = _iso(stored.planned_completion_date) if stored is not None else None
    milestone_synthetic = False
    dates_synthetic = False
    if (
        data_mode == DataMode.HYBRID
        and enrichment is not None
    ):
        if milestone_label is None and enrichment.milestone_number is not None:
            milestone_label = f"M{enrichment.milestone_number}"
            milestone_synthetic = True
        if milestone_amount is None and enrichment.milestone_amount is not None:
            milestone_amount = float(enrichment.milestone_amount)
            milestone_synthetic = True
        if planned_start is None and enrichment.planned_start_date:
            planned_start = enrichment.planned_start_date
            dates_synthetic = True
        if planned_end is None and enrichment.planned_completion_date:
            planned_end = enrichment.planned_completion_date
            dates_synthetic = True

    if data_mode == DataMode.SYNTHETIC:
        notes = SYNTHETIC_PROVENANCE_NOTE
        enrichment_used = False
    elif data_mode == DataMode.HYBRID:
        notes = HYBRID_PROVENANCE_NOTE
        enrichment_used = enrichment is not None
    else:
        notes = REAL_PROVENANCE_NOTE
        enrichment_used = False
    if stored is not None:
        notes = f"{notes} Officer-recorded plan overlay source: {stored.source or 'officer_recorded'}."

    provenance: dict[str, Any] = {
        "data_mode": data_mode.value,
        "source_type": (
            SourceType.SYNTHETIC_TEST_RECORD.value
            if data_mode == DataMode.SYNTHETIC
            else SourceType.HYBRID_ENRICHMENT.value
            if data_mode == DataMode.HYBRID and enrichment_used
            else SourceType.PLAN_RECORD.value
        ),
        "source_ids": [project.internal_project_id],
        "internal_project_id": project.internal_project_id,
        "notes": notes,
        "source_dataset": project.source_dataset,
        "engine_version": ENGINE_VERSION,
        "enrichment_used": enrichment_used,
        "enrichment_path": HYBRID_ENRICHMENT_RELATIVE_PATH if enrichment_used else None,
        "recorded_plan": stored is not None,
    }

    unavailable_dim = UNAVAILABLE_DIMENSIONS_REASON
    fields = [
        _field("sanctioned_scope", scope, data_mode=DataMode.REAL if not (stored and stored.sanctioned_scope and overlay_mode != DataMode.REAL) else overlay_mode, source=scope_source, synthetic=False, unavailable_reason="Work description is unavailable."),
        _field(
            "budget_estimate",
            budget,
            data_mode=DataMode.REAL if budget_from_extract else overlay_mode,
            source=budget_source,
            synthetic=False,
            unavailable_reason="Allocation/estimate is unavailable.",
        ),
        _field(
            "blueprint_document_id",
            blueprint_id,
            data_mode=overlay_mode,
            source="recorded plan overlay" if blueprint_id else "unavailable",
            unavailable_reason="No blueprint/document reference is recorded.",
        ),
        _field(
            "dimensions_value",
            dimensions,
            data_mode=overlay_mode,
            source="recorded plan overlay" if dimensions is not None else "unavailable",
            unavailable_reason=unavailable_dim,
        ),
        _field(
            "dimensions_unit",
            dimensions_unit,
            data_mode=overlay_mode,
            source="recorded plan overlay" if dimensions_unit else "unavailable",
            unavailable_reason=unavailable_dim,
        ),
        _field(
            "milestone_label",
            milestone_label,
            data_mode=DataMode.HYBRID if milestone_synthetic else overlay_mode,
            source="SYNTHETIC enrichment" if milestone_synthetic else ("recorded plan overlay" if stored and stored.milestone_label else "unavailable"),
            synthetic=milestone_synthetic,
            unavailable_reason="Milestone information is unavailable.",
        ),
        _field(
            "milestone_amount",
            milestone_amount,
            data_mode=DataMode.HYBRID if milestone_synthetic else overlay_mode,
            source="SYNTHETIC enrichment" if milestone_synthetic else ("recorded plan overlay" if stored and stored.milestone_amount is not None else "unavailable"),
            synthetic=milestone_synthetic,
            unavailable_reason="Milestone amount is unavailable.",
        ),
        _field(
            "planned_start_date",
            planned_start,
            data_mode=DataMode.HYBRID if dates_synthetic else overlay_mode,
            source="SYNTHETIC enrichment" if dates_synthetic else ("recorded plan overlay" if stored and stored.planned_start_date else "project.recommended_date" if planned_start else "unavailable"),
            synthetic=dates_synthetic,
            unavailable_reason="Planned start date is unavailable in the current public extract.",
        ),
        _field(
            "planned_completion_date",
            planned_end,
            data_mode=DataMode.HYBRID if dates_synthetic else overlay_mode,
            source="SYNTHETIC enrichment" if dates_synthetic else ("recorded plan overlay" if stored and stored.planned_completion_date else "unavailable"),
            synthetic=dates_synthetic,
            unavailable_reason="Planned completion date is unavailable in the current public extract.",
        ),
        _field(
            "recommended_date",
            _iso(project.recommended_date),
            data_mode=DataMode.REAL,
            source="project.recommended_date",
            unavailable_reason="Recommended date is unavailable.",
        ),
    ]

    return AssembledPlan(
        project_id=project.id,
        internal_project_id=project.internal_project_id,
        data_mode=data_mode,
        sanctioned_scope=scope,
        budget_estimate=budget,
        budget_from_extract=budget_from_extract,
        blueprint_document_id=blueprint_id,
        dimensions_value=None if dimensions is None else float(dimensions),
        dimensions_unit=dimensions_unit,
        milestone_label=milestone_label,
        milestone_amount=None if milestone_amount is None else float(milestone_amount),
        planned_start_date=planned_start,
        planned_completion_date=planned_end,
        source=stored.source if stored and stored.source else scope_source,
        provenance=provenance,
        fields=fields,
        recorded=stored is not None,
    )
