"""Need & Impact V1 orchestration.

Does not change Cost, Time, Overlap, Compliance, Fusion, Graph, PCE,
Document, Image, or Geospatial scoring. Does not sanction projects.
"""

from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import DataMode
from app.engines.need.constants import (
    CRORE_RUPEES,
    ENGINE_NAME,
    ENGINE_VERSION,
    FORBIDDEN_OUTPUT_TERMS,
    GOVERNANCE_NOTE,
    MAX_RANK_CANDIDATES,
)
from app.engines.need.enrichment import enrichment_for
from app.engines.need.errors import NeedImpactError
from app.engines.need.evaluate import evaluate_need_impact
from app.engines.need.rank import rank_assessments
from app.engines.need.repository import constituency_context_for, project_to_inputs, snapshot_for
from app.engines.need.types import (
    NeedImpactResult,
    RankResult,
    SyntheticNeedImpactEnrichment,
)
from app.evidence.adapters.need import result_to_evidence_objects
from app.evidence.constants import FRAUD_CLAIM_PATTERN
from app.evidence.repository import add_evidence_object
from app.models.evidence import EvidenceObjectRow
from app.models.project import Project

_FRAUD_RE = re.compile(FRAUD_CLAIM_PATTERN, re.IGNORECASE)


def parse_data_mode(value: str | DataMode | None, project: Project | None = None) -> DataMode:
    if project is not None and project.is_synthetic:
        return DataMode.SYNTHETIC
    if isinstance(value, DataMode):
        return value
    text = str(value or "").strip().upper().replace("-", "_")
    if text in {"HYBRID", "HYBRID_TEST", "HYBRIDTEST", "HYBRID_DEMO"}:
        return DataMode.HYBRID
    if text in {"SYNTHETIC"}:
        return DataMode.SYNTHETIC
    if text in {"REAL", "REAL_DATA"}:
        return DataMode.REAL
    return DataMode.REAL


def reject_forbidden_text(*values: object) -> None:
    blob = "\n".join("" if item is None else str(item) for item in values).casefold()
    if _FRAUD_RE.search(blob):
        raise NeedImpactError(
            "Need & Impact must not claim fraud or use fraud language.",
            code="fraud_language_forbidden",
            status_code=422,
        )
    for term in FORBIDDEN_OUTPUT_TERMS:
        if term in blob:
            raise NeedImpactError(
                "Need & Impact must not output sanction or fraud conclusions.",
                code="forbidden_output_term",
                status_code=422,
            )


def resolve_budget(
    available_budget: int | float | None,
    available_budget_crore: float | None,
) -> tuple[int | None, float | None]:
    if available_budget is not None and available_budget_crore is not None:
        budget = int(available_budget)
        return budget, round(budget / CRORE_RUPEES, 4)
    if available_budget is not None:
        budget = int(available_budget)
        if budget < 0:
            raise NeedImpactError(
                "Hypothetical available budget cannot be negative.",
                code="invalid_budget",
                status_code=422,
            )
        return budget, round(budget / CRORE_RUPEES, 4)
    if available_budget_crore is not None:
        if available_budget_crore < 0:
            raise NeedImpactError(
                "Hypothetical available budget cannot be negative.",
                code="invalid_budget",
                status_code=422,
            )
        budget = int(round(float(available_budget_crore) * CRORE_RUPEES))
        return budget, float(available_budget_crore)
    return None, None


def _delete_need_for_mode(session: Session, project_id: int, data_mode: DataMode) -> None:
    existing = session.scalars(
        select(EvidenceObjectRow).where(
            EvidenceObjectRow.project_id == project_id,
            EvidenceObjectRow.engine == ENGINE_NAME,
            EvidenceObjectRow.data_mode == data_mode.value,
        )
    ).all()
    for row in existing:
        for fact in list(row.facts):
            session.delete(fact)
        session.delete(row)
    session.flush()


def persist_need_impact_evidence(
    session: Session,
    project: Project,
    result: NeedImpactResult,
) -> list[str]:
    snapshot = snapshot_for(session, project)
    objects = result_to_evidence_objects(project, result, snapshot=snapshot)
    _delete_need_for_mode(session, project.id, result.data_mode)
    ids: list[str] = []
    for obj in objects:
        reject_forbidden_text(obj.finding, obj.explanation)
        row = add_evidence_object(session, obj)
        if row.evidence_id:
            ids.append(row.evidence_id)
    return ids


def assess_project_need_impact(
    session: Session,
    project: Project,
    data_mode: DataMode,
    *,
    persist: bool = True,
    enrichment_overlay: dict[str, SyntheticNeedImpactEnrichment] | None = None,
) -> NeedImpactResult:
    reject_forbidden_text(data_mode.value, project.work_description, project.category)
    enrichment = None
    if data_mode != DataMode.REAL:
        enrichment = enrichment_for(project.internal_project_id, overlay=enrichment_overlay)
    inputs = project_to_inputs(project, data_mode, enrichment=enrichment)
    context = constituency_context_for(session, project)
    result = evaluate_need_impact(inputs, constituency_context=context)
    result.engine_version = ENGINE_VERSION
    result.governance_note = GOVERNANCE_NOTE
    result.provenance = {
        "data_mode": data_mode.value,
        "internal_project_id": project.internal_project_id,
        "source_dataset": project.source_dataset,
        "enrichment_used": result.enrichment_used,
        "enrichment_label": result.enrichment_label,
    }
    reject_forbidden_text(result.explanation, result.finding, result.priority_class)
    if persist:
        result.evidence_ids = persist_need_impact_evidence(session, project, result)
    return result


def rank_projects(
    session: Session,
    project_ids: list[int],
    data_mode: DataMode,
    *,
    available_budget: int | float | None = None,
    available_budget_crore: float | None = None,
    persist: bool = True,
    enrichment_overlay: dict[str, SyntheticNeedImpactEnrichment] | None = None,
) -> RankResult:
    if not project_ids:
        raise NeedImpactError("At least one candidate project id is required.", code="empty_candidates")
    if len(project_ids) > MAX_RANK_CANDIDATES:
        raise NeedImpactError(
            f"At most {MAX_RANK_CANDIDATES} candidate projects can be ranked in this prototype.",
            code="too_many_candidates",
            status_code=422,
        )
    seen: set[int] = set()
    ordered: list[int] = []
    for project_id in project_ids:
        if project_id in seen:
            continue
        seen.add(project_id)
        ordered.append(project_id)
    results: list[NeedImpactResult] = []
    for project_id in ordered:
        project = session.get(Project, project_id)
        if project is None:
            raise NeedImpactError("Project not found.", code="not_found", status_code=404)
        mode = parse_data_mode(data_mode, project)
        results.append(
            assess_project_need_impact(
                session,
                project,
                mode,
                persist=persist,
                enrichment_overlay=enrichment_overlay,
            )
        )
    budget, crore = resolve_budget(available_budget, available_budget_crore)
    ranked = rank_assessments(
        results,
        available_budget=budget,
        available_budget_crore=crore,
    )
    reject_forbidden_text(ranked.explanation)
    return ranked
