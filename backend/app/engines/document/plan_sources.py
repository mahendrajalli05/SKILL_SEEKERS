"""Attach extracted facts to PLAN without silently overwriting trusted values."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.domain.enums import DataMode
from app.engines.document.constants import AUTHORITATIVE_CONFIDENCE, PLAN_CONFLICT_THRESHOLD
from app.engines.document.repository import get_plan_row, list_project_documents, get_artifact
from app.engines.document.types import PlanConflict, SourceValue
from app.engines.pce.compare import relative_difference
from app.models.plan import Plan
from app.models.project import Project


def _numeric(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def authoritative_fields(extraction: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for item in extraction.get("fields") or []:
        if not isinstance(item, dict) or not item.get("available"):
            continue
        confidence = item.get("confidence")
        if confidence is None or float(confidence) < AUTHORITATIVE_CONFIDENCE:
            continue
        out[str(item["name"])] = item
    return out


def collect_plan_sources(
    session: Session,
    project: Project,
    *,
    data_mode: DataMode,
) -> list[SourceValue]:
    sources: list[SourceValue] = []
    if project.allocation_amount is not None:
        sources.append(
            SourceValue(
                field="estimate_amount",
                value=float(project.allocation_amount),
                unit=None,
                source="project.allocation_amount",
                confidence=1.0,
                timestamp=None,
                document_id=None,
                data_mode=DataMode.REAL,
            )
        )
    if project.work_description:
        sources.append(
            SourceValue(
                field="work_name",
                value=project.work_description,
                unit=None,
                source="project.work_description",
                confidence=1.0,
                timestamp=None,
                document_id=None,
                data_mode=DataMode.REAL,
            )
        )
    stored = get_plan_row(session, project.id)
    if stored is not None and (data_mode != DataMode.REAL or stored.data_mode == DataMode.REAL.value):
        if stored.dimensions_value is not None:
            sources.append(
                SourceValue(
                    field="area",
                    value=float(stored.dimensions_value),
                    unit=stored.dimensions_unit,
                    source=stored.source or "recorded plan overlay",
                    confidence=1.0,
                    timestamp=stored.updated_at.isoformat() if stored.updated_at else None,
                    document_id=stored.blueprint_document_id,
                    data_mode=DataMode(stored.data_mode) if stored.data_mode else data_mode,
                )
            )
        if stored.budget_estimate is not None:
            sources.append(
                SourceValue(
                    field="estimate_amount",
                    value=float(stored.budget_estimate),
                    unit="INR",
                    source=stored.source or "recorded plan overlay",
                    confidence=1.0,
                    timestamp=stored.updated_at.isoformat() if stored.updated_at else None,
                    document_id=stored.blueprint_document_id,
                    data_mode=DataMode(stored.data_mode) if stored.data_mode else data_mode,
                )
            )
    for document in list_project_documents(session, project.id):
        if data_mode == DataMode.REAL and document.data_mode and document.data_mode != DataMode.REAL.value:
            continue
        artifact = get_artifact(session, document.id)
        if artifact is None or not artifact.attached_to_plan:
            continue
        payload = artifact.extracted_fields_json
        extraction: dict[str, Any] = {}
        if payload:
            import json

            try:
                loaded = json.loads(payload)
            except json.JSONDecodeError:
                loaded = {}
            if isinstance(loaded, dict):
                extraction = loaded.get("extraction") or {}
        for item in authoritative_fields(extraction).values():
            sources.append(
                SourceValue(
                    field=str(item["name"]),
                    value=item.get("value"),
                    unit=item.get("unit"),
                    source=f"document:{document.id}",
                    confidence=item.get("confidence"),
                    timestamp=document.updated_at.isoformat() if document.updated_at else None,
                    document_id=document.id,
                    data_mode=DataMode(document.data_mode) if document.data_mode else data_mode,
                )
            )
    return sources


def detect_conflicts(sources: list[SourceValue]) -> list[PlanConflict]:
    by_field: dict[str, list[SourceValue]] = {}
    for item in sources:
        by_field.setdefault(item.field, []).append(item)
    conflicts: list[PlanConflict] = []
    for field, items in by_field.items():
        numeric = [(_numeric(item.value), item) for item in items]
        usable = [(value, item) for value, item in numeric if value is not None]
        if len(usable) < 2:
            texts = {str(item.value) for item in items if item.value is not None}
            if len(texts) > 1:
                conflicts.append(
                    PlanConflict(
                        field=field,
                        result="PLAN_DATA_CONFLICT",
                        sources=items,
                        explanation=(
                            f"Multiple sources provide different {field} values. "
                            "No source was chosen as truth."
                        ),
                    )
                )
            continue
        spread = relative_difference(
            min(value for value, _item in usable),
            max(value for value, _item in usable),
        )
        if spread > PLAN_CONFLICT_THRESHOLD:
            conflicts.append(
                PlanConflict(
                    field=field,
                    result="PLAN_DATA_CONFLICT",
                    sources=items,
                    explanation=(
                        f"Multiple sources provide different {field} values. "
                        "No source was chosen as truth."
                    ),
                )
            )
    return conflicts


def apply_to_plan(
    session: Session,
    project: Project,
    *,
    document_id: int,
    extraction: dict[str, Any],
    data_mode: DataMode,
    provenance: dict[str, Any],
) -> tuple[Plan, list[PlanConflict], list[str]]:
    from app.engines.pce.repository import upsert_plan

    fields = authoritative_fields(extraction)
    stored = get_plan_row(session, project.id)
    notes: list[str] = []
    conflicts: list[PlanConflict] = []

    sanctioned_scope = stored.sanctioned_scope if stored else None
    budget_estimate = stored.budget_estimate if stored else None
    blueprint_document_id = stored.blueprint_document_id if stored else None
    dimensions_value = stored.dimensions_value if stored else None
    dimensions_unit = stored.dimensions_unit if stored else None
    milestone_label = stored.milestone_label if stored else None
    milestone_amount = stored.milestone_amount if stored else None
    planned_start = stored.planned_start_date if stored else None
    planned_end = stored.planned_completion_date if stored else None
    source = stored.source if stored else f"officer_attached_document:{document_id}"

    area = fields.get("area")
    if area is not None:
        incoming = _numeric(area.get("value"))
        if incoming is not None:
            if dimensions_value is None:
                dimensions_value = incoming
                dimensions_unit = area.get("unit") or "sq.ft"
                blueprint_document_id = blueprint_document_id or document_id
                notes.append("Attached extracted area to empty plan overlay.")
            elif relative_difference(float(dimensions_value), incoming) > PLAN_CONFLICT_THRESHOLD:
                conflicts.append(
                    PlanConflict(
                        field="area",
                        result="PLAN_DATA_CONFLICT",
                        sources=[
                            SourceValue(
                                "area",
                                dimensions_value,
                                dimensions_unit,
                                stored.source if stored else "plan overlay",
                                1.0,
                                None,
                                stored.blueprint_document_id if stored else None,
                                data_mode,
                            ),
                            SourceValue(
                                "area",
                                incoming,
                                area.get("unit"),
                                f"document:{document_id}",
                                area.get("confidence"),
                                None,
                                document_id,
                                data_mode,
                            ),
                        ],
                        explanation="Plan overlay and extracted document area differ. No source was chosen as truth.",
                    )
                )
                notes.append("Extracted area was not written over the existing plan overlay.")
            else:
                notes.append("Extracted area agrees with the recorded plan overlay.")

    estimate = fields.get("estimate_amount")
    if estimate is not None:
        incoming = _numeric(estimate.get("value"))
        trusted = float(project.allocation_amount) if project.allocation_amount is not None else None
        if incoming is not None and trusted is not None:
            if relative_difference(trusted, incoming) > PLAN_CONFLICT_THRESHOLD:
                conflicts.append(
                    PlanConflict(
                        field="estimate_amount",
                        result="PLAN_DATA_CONFLICT",
                        sources=[
                            SourceValue(
                                "estimate_amount",
                                trusted,
                                None,
                                "project.allocation_amount",
                                1.0,
                                None,
                                None,
                                DataMode.REAL,
                            ),
                            SourceValue(
                                "estimate_amount",
                                incoming,
                                estimate.get("unit"),
                                f"document:{document_id}",
                                estimate.get("confidence"),
                                None,
                                document_id,
                                data_mode,
                            ),
                        ],
                        explanation="Trusted allocation and extracted estimate differ. The extract value was not overwritten.",
                    )
                )
                notes.append("Extracted estimate was not written over the trusted allocation.")
            else:
                notes.append("Extracted estimate agrees with the observed allocation.")
        elif incoming is not None and budget_estimate is None and trusted is None:
            budget_estimate = incoming
            notes.append("Attached extracted estimate to empty plan overlay.")
        elif incoming is not None and budget_estimate is not None:
            if relative_difference(float(budget_estimate), incoming) > PLAN_CONFLICT_THRESHOLD:
                conflicts.append(
                    PlanConflict(
                        field="estimate_amount",
                        result="PLAN_DATA_CONFLICT",
                        sources=[
                            SourceValue(
                                "estimate_amount",
                                budget_estimate,
                                None,
                                stored.source if stored else "plan overlay",
                                1.0,
                                None,
                                None,
                                data_mode,
                            ),
                            SourceValue(
                                "estimate_amount",
                                incoming,
                                estimate.get("unit"),
                                f"document:{document_id}",
                                estimate.get("confidence"),
                                None,
                                document_id,
                                data_mode,
                            ),
                        ],
                        explanation="Plan overlay and extracted estimate differ. No source was chosen as truth.",
                    )
                )
                notes.append("Extracted estimate was not written over the existing plan overlay.")

    work_name = fields.get("work_name") or fields.get("scope_description")
    if work_name and work_name.get("value") and not sanctioned_scope and not project.work_description:
        sanctioned_scope = str(work_name["value"])
        notes.append("Attached extracted work name to empty plan overlay.")

    start = fields.get("planned_start")
    if start and start.get("value") and planned_start is None:
        from datetime import date

        try:
            planned_start = date.fromisoformat(str(start["value"])[:10])
            notes.append("Attached extracted planned start to empty plan overlay.")
        except ValueError:
            pass
    end = fields.get("planned_completion")
    if end and end.get("value") and planned_end is None:
        from datetime import date

        try:
            planned_end = date.fromisoformat(str(end["value"])[:10])
            notes.append("Attached extracted planned completion to empty plan overlay.")
        except ValueError:
            pass

    milestone_items = extraction.get("milestones") or []
    if milestone_amount is None and milestone_items:
        first = milestone_items[0]
        if isinstance(first, dict) and first.get("amount") is not None:
            confidence = first.get("confidence") or 0.0
            if float(confidence) >= AUTHORITATIVE_CONFIDENCE:
                milestone_amount = float(first["amount"])
                milestone_label = first.get("milestone")
                notes.append("Attached extracted milestone to empty plan overlay.")

    provenance = dict(provenance)
    provenance["attached_document_id"] = document_id
    if conflicts:
        provenance["plan_data_conflict"] = True
    row = upsert_plan(
        session,
        project.id,
        sanctioned_scope=sanctioned_scope,
        budget_estimate=budget_estimate,
        blueprint_document_id=blueprint_document_id,
        dimensions_value=dimensions_value,
        dimensions_unit=dimensions_unit,
        milestone_label=milestone_label,
        milestone_amount=milestone_amount,
        planned_start_date=planned_start,
        planned_completion_date=planned_end,
        source=source,
        data_mode=data_mode if stored is None else DataMode(stored.data_mode),
        provenance=provenance,
    )
    return row, conflicts, notes
