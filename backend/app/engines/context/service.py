"""Orchestrate contextual enrichment without changing frozen engines."""

from __future__ import annotations

import json
import re
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import DataMode
from app.engines.context.constants import (
    ENGINE_NAME,
    ENGINE_VERSION,
    FORBIDDEN_OUTPUT_TERMS,
    NEW_INTERNAL_ID,
    NEW_PROJECT_ASSESSMENT,
    NEW_PROJECT_ID,
)
from app.engines.context.errors import ContextError
from app.engines.context.evaluate import evaluate_context
from app.engines.context.types import ContextResult
from app.evidence.adapters.context import result_to_evidence_objects
from app.evidence.constants import FRAUD_CLAIM_PATTERN
from app.evidence.repository import add_evidence_object
from app.models.context import ExternalContextObservation, ExternalSource
from app.models.evidence import EvidenceObjectRow
from app.models.project import Project
from app.engines.context.registry import load_registry

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
    return DataMode.REAL


def reject_forbidden_text(*values: object) -> None:
    blob = "\n".join("" if item is None else str(item) for item in values).casefold()
    if _FRAUD_RE.search(blob):
        raise ContextError(
            "Contextual evidence must not claim fraud or use fraud language.",
            code="fraud_language_forbidden",
            status_code=422,
        )
    for term in FORBIDDEN_OUTPUT_TERMS:
        if term in blob:
            raise ContextError(
                "Contextual evidence must not output fraud or guilt conclusions.",
                code="forbidden_output_term",
                status_code=422,
            )


def sync_source_registry(session: Session) -> None:
    for source in load_registry():
        row = session.scalars(
            select(ExternalSource).where(ExternalSource.source_id == source.source_id)
        ).first()
        payload = {
            "source_name": source.source_name,
            "publisher": source.publisher,
            "source_type": source.source_type,
            "url": source.url,
            "retrieval_date": source.retrieval_date,
            "dataset_version": source.dataset_version,
            "geographic_level": source.geographic_level,
            "unit": source.unit,
            "update_frequency": source.update_frequency,
            "license_note": source.license_note,
            "transformation_notes": source.transformation_notes,
            "limitations_json": json.dumps(source.limitations),
            "active": 1 if source.active else 0,
            "requires_credential": 1 if source.requires_credential else 0,
        }
        if row is None:
            session.add(ExternalSource(source_id=source.source_id, **payload))
        else:
            for key, value in payload.items():
                setattr(row, key, value)
    session.flush()


def _delete_context_evidence(session: Session, project_id: int) -> None:
    existing = session.scalars(
        select(EvidenceObjectRow).where(
            EvidenceObjectRow.project_id == project_id,
            EvidenceObjectRow.engine == ENGINE_NAME,
        )
    ).all()
    for row in existing:
        for fact in list(row.facts):
            session.delete(fact)
        session.delete(row)
    rows = session.scalars(
        select(ExternalContextObservation).where(ExternalContextObservation.project_id == project_id)
    ).all()
    for row in rows:
        session.delete(row)
    session.flush()


def persist_context(
    session: Session,
    project: Project,
    result: ContextResult,
) -> list[str]:
    sync_source_registry(session)
    _delete_context_evidence(session, project.id)
    objects = result_to_evidence_objects(project, result)
    ids: list[str] = []
    for obj in objects:
        reject_forbidden_text(obj.finding, obj.explanation)
        row = add_evidence_object(session, obj)
        if row.evidence_id:
            ids.append(row.evidence_id)
    for item in result.observations:
        session.add(
            ExternalContextObservation(
                project_id=project.id,
                internal_project_id=project.internal_project_id,
                indicator=item.indicator,
                status=item.status,
                value=None if item.value is None else str(item.value),
                unit=item.unit,
                geographic_level=item.geographic_level,
                geo_key=item.geo_key,
                source_id=item.source_id,
                retrieval_date=item.retrieval_date,
                reference_year=item.reference_year,
                data_mode=item.data_mode.value,
                confidence=str(item.confidence),
                quality=item.quality,
                context_kind=item.context_kind,
                provenance_json=json.dumps(item.as_dict(), default=str),
                failure_code=item.failure_code,
                assessment_kind=result.assessment_kind,
            )
        )
    session.flush()
    result.evidence_ids = ids
    result.persisted = True
    return ids


def assess_project_context(
    session: Session,
    project: Project,
    data_mode: DataMode,
    *,
    persist: bool = True,
    requested_level: str | None = None,
) -> ContextResult:
    reject_forbidden_text(data_mode.value, project.work_description, project.category)
    result = evaluate_context(
        session=session,
        data_mode=data_mode,
        internal_project_id=project.internal_project_id,
        project_id=project.id,
        state=project.state,
        constituency=project.constituency,
        block=project.block,
        city=project.city,
        village=project.village,
        ward=project.ward,
        ida=project.ida,
        category=project.category,
        work_description=project.work_description,
        allocation_amount=project.allocation_amount,
        recommended_date=project.recommended_date,
        requested_level=requested_level,
    )
    result.engine_version = ENGINE_VERSION
    if persist and project.id:
        persist_context(session, project, result)
    return result


def assess_new_project_context(
    session: Session | None,
    payload: dict[str, object],
) -> ContextResult:
    data_mode = parse_data_mode(str(payload.get("data_mode") or DataMode.REAL.value))
    rec = payload.get("recommendation_date") or payload.get("recommended_date")
    rec_date: date | str | None
    if isinstance(rec, date):
        rec_date = rec
    else:
        rec_date = str(rec).strip() if rec else None
    amount = payload.get("allocation_amount")
    result = evaluate_context(
        session=session,
        data_mode=data_mode,
        internal_project_id=NEW_INTERNAL_ID,
        project_id=NEW_PROJECT_ID,
        state=str(payload.get("state") or "") or None,
        constituency=str(payload.get("constituency") or "") or None,
        block=str(payload.get("block") or "") or None,
        city=str(payload.get("city") or "") or None,
        village=str(payload.get("village") or "") or None,
        category=str(payload.get("category") or "") or None,
        work_description=str(payload.get("work_description") or "") or None,
        allocation_amount=int(amount) if amount not in (None, "") else None,
        recommended_date=rec_date,
        assessment_kind=NEW_PROJECT_ASSESSMENT,
    )
    result.persisted = False
    result.project_id = None
    return result
