"""Persist Document & Blueprint V1 rows on existing document / plan_artifact tables."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import REPO_ROOT
from app.domain.enums import DataMode
from app.models.artifacts import Document, PlanArtifact
from app.models.plan import Plan


def _dump(value: object) -> str:
    return json.dumps(value, sort_keys=True, default=str)


def _load(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def save_bytes(project_id: int, filename: str, payload: bytes, digest: str) -> str:
    folder = REPO_ROOT / "data" / "uploads" / "documents" / str(project_id)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{digest[:16]}_{filename}"
    path.write_bytes(payload)
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/")


def get_document(session: Session, document_id: int) -> Document | None:
    return session.get(Document, document_id)


def list_project_documents(session: Session, project_id: int) -> list[Document]:
    return list(
        session.scalars(
            select(Document).where(Document.project_id == project_id).order_by(Document.id)
        ).all()
    )


def get_artifact(session: Session, document_id: int) -> PlanArtifact | None:
    return session.scalars(
        select(PlanArtifact).where(PlanArtifact.document_id == document_id).order_by(PlanArtifact.id)
    ).first()


def add_document(
    session: Session,
    project_id: int,
    *,
    document_type: str,
    filename: str,
    path: str,
    mime_type: str,
    file_size: int,
    content_sha256: str,
    data_mode: DataMode,
    provenance: dict[str, Any],
    integrity_status: str,
    duplicate_of_id: int | None,
) -> Document:
    row = Document(
        project_id=project_id,
        kind=document_type,
        document_type=document_type,
        filename=filename,
        path=path,
        mime_type=mime_type,
        file_size=file_size,
        content_sha256=content_sha256,
        source="officer_upload",
        data_mode=data_mode.value,
        provenance_json=_dump(provenance),
        extraction_status="NOT_RUN",
        integrity_status=integrity_status,
        duplicate_of_id=duplicate_of_id,
        uploaded_by_role="officer",
    )
    session.add(row)
    session.flush()
    return row


def upsert_artifact(
    session: Session,
    document: Document,
    *,
    extraction: dict[str, Any],
    structure: dict[str, Any],
    status: str,
    method: str,
    text_sha256: str | None,
    data_mode: DataMode,
    provenance: dict[str, Any],
) -> PlanArtifact:
    row = get_artifact(session, document.id)
    if row is None:
        row = PlanArtifact(document_id=document.id)
        session.add(row)
    area = None
    area_field = next(
        (
            item
            for item in extraction.get("fields") or []
            if isinstance(item, dict) and item.get("name") == "area" and item.get("available")
        ),
        None,
    )
    if area_field and area_field.get("value") is not None:
        try:
            area = float(area_field["value"])
        except (TypeError, ValueError):
            area = None
    row.claimed_area = area
    row.structure_type = document.document_type
    row.extracted_fields_json = _dump({"extraction": extraction, "structure": structure})
    row.extraction_status = status
    row.extraction_method = method
    row.text_sha256 = text_sha256
    row.data_mode = data_mode.value
    row.provenance_json = _dump(provenance)
    document.extracted_text = extraction.get("combined_text") or None
    document.extraction_status = status
    session.flush()
    return row


def mark_attached(session: Session, artifact: PlanArtifact, *, plan: bool = False, evidence: bool = False) -> None:
    if plan:
        artifact.attached_to_plan = 1
    if evidence:
        artifact.attached_to_evidence = 1
    session.flush()


def list_attached_artifacts(session: Session, project_id: int) -> list[tuple[Document, PlanArtifact]]:
    documents = list_project_documents(session, project_id)
    out: list[tuple[Document, PlanArtifact]] = []
    for document in documents:
        artifact = get_artifact(session, document.id)
        if artifact is None:
            continue
        if artifact.attached_to_plan or artifact.attached_to_evidence:
            out.append((document, artifact))
    return out


def get_plan_row(session: Session, project_id: int) -> Plan | None:
    return session.scalars(select(Plan).where(Plan.project_id == project_id)).first()


def artifact_payload(artifact: PlanArtifact | None) -> dict[str, Any]:
    if artifact is None:
        return {}
    return _load(artifact.extracted_fields_json)
