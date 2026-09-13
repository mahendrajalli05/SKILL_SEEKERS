"""Persist and load Plan, Claim, Document, and Photo rows for PCE V1."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import DataMode
from app.models.artifacts import Claim, Document, Photo
from app.models.plan import Plan


def _dump(value: object) -> str:
    return json.dumps(value, sort_keys=True, default=str)


def _load_list(raw: str | None) -> list[int]:
    if not raw:
        return []
    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(loaded, list):
        return []
    out: list[int] = []
    for item in loaded:
        try:
            out.append(int(item))
        except (TypeError, ValueError):
            continue
    return out


def get_plan(session: Session, project_id: int) -> Plan | None:
    return session.scalars(select(Plan).where(Plan.project_id == project_id)).first()


def upsert_plan(
    session: Session,
    project_id: int,
    *,
    sanctioned_scope: str | None,
    budget_estimate: float | None,
    blueprint_document_id: int | None,
    dimensions_value: float | None,
    dimensions_unit: str | None,
    milestone_label: str | None,
    milestone_amount: float | None,
    planned_start_date,
    planned_completion_date,
    source: str | None,
    data_mode: DataMode,
    provenance: dict[str, Any],
) -> Plan:
    row = get_plan(session, project_id)
    if row is None:
        row = Plan(project_id=project_id)
        session.add(row)
    row.sanctioned_scope = sanctioned_scope
    row.budget_estimate = budget_estimate
    row.blueprint_document_id = blueprint_document_id
    row.dimensions_value = dimensions_value
    row.dimensions_unit = dimensions_unit
    row.milestone_label = milestone_label
    row.milestone_amount = milestone_amount
    row.planned_start_date = planned_start_date
    row.planned_completion_date = planned_completion_date
    row.source = source or "officer_recorded"
    row.data_mode = data_mode.value
    row.provenance_json = _dump(provenance)
    session.flush()
    return row


def list_claims(session: Session, project_id: int) -> list[Claim]:
    return list(
        session.scalars(
            select(Claim).where(Claim.project_id == project_id).order_by(Claim.id.desc())
        ).all()
    )


def add_claim(
    session: Session,
    project_id: int,
    *,
    reported_progress: str | None,
    claimed_progress_percent: float | None,
    amount_used: float | None,
    completion_statement: str | None,
    claimed_quantity: float | None,
    claimed_quantity_unit: str | None,
    milestone_label: str | None,
    claim_date: datetime | None,
    claimant_source: str | None,
    supporting_document_ids: list[int],
    data_mode: DataMode,
    provenance: dict[str, Any],
) -> Claim:
    row = Claim(
        project_id=project_id,
        milestone_label=milestone_label,
        reported_progress=reported_progress,
        amount_used=amount_used,
        completion_statement=completion_statement,
        claimed_progress_percent=claimed_progress_percent,
        claimed_quantity=claimed_quantity,
        claimed_quantity_unit=claimed_quantity_unit,
        claim_date=claim_date,
        claimant_source=claimant_source or "implementing_agency",
        supporting_document_ids_json=_dump(supporting_document_ids),
        data_mode=data_mode.value,
        provenance_json=_dump(provenance),
    )
    session.add(row)
    session.flush()
    return row


def list_documents(session: Session, project_id: int) -> list[Document]:
    return list(
        session.scalars(select(Document).where(Document.project_id == project_id).order_by(Document.id)).all()
    )


def list_photos(session: Session, project_id: int) -> list[Photo]:
    return list(
        session.scalars(select(Photo).where(Photo.project_id == project_id).order_by(Photo.id)).all()
    )


def add_document(
    session: Session,
    project_id: int,
    *,
    document_type: str,
    filename: str | None,
    path: str | None,
    source: str | None,
    data_mode: DataMode,
    provenance: dict[str, Any],
    content_sha256: str | None,
    observed_quantity: float | None,
    observed_quantity_unit: str | None,
    observed_expenditure: float | None,
    notes: str | None,
    uploaded_by_role: str = "officer",
) -> Document:
    row = Document(
        project_id=project_id,
        kind=document_type,
        document_type=document_type,
        filename=filename,
        path=path,
        source=source or "officer_upload",
        data_mode=data_mode.value,
        provenance_json=_dump(provenance),
        content_sha256=content_sha256,
        observed_quantity=observed_quantity,
        observed_quantity_unit=observed_quantity_unit,
        observed_expenditure=observed_expenditure,
        notes=notes,
        uploaded_by_role=uploaded_by_role,
    )
    session.add(row)
    session.flush()
    return row


def add_photo(
    session: Session,
    project_id: int,
    *,
    filename: str | None,
    path: str | None,
    source: str | None,
    data_mode: DataMode,
    provenance: dict[str, Any],
    latitude: float | None,
    longitude: float | None,
    captured_at: datetime | None,
    content_hash: str | None,
    observed_quantity: float | None,
    observed_quantity_unit: str | None,
    notes: str | None,
) -> Photo:
    row = Photo(
        project_id=project_id,
        filename=filename,
        path=path,
        source=source or "officer_upload",
        data_mode=data_mode.value,
        provenance_json=_dump(provenance),
        exif_lat=latitude,
        exif_lon=longitude,
        exif_time=captured_at,
        phash=content_hash,
        observed_quantity=observed_quantity,
        observed_quantity_unit=observed_quantity_unit,
        notes=notes,
    )
    session.add(row)
    session.flush()
    return row


def claim_supporting_ids(row: Claim) -> list[int]:
    return _load_list(row.supporting_document_ids_json)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
