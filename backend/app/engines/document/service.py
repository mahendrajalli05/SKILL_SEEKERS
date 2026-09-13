"""Document & Blueprint Intelligence V1 orchestration.

Upload, extract, integrity, plan attach, and Evidence Object recording.
Does not change Cost, Time, Overlap, Compliance, Fusion, or Graph scoring.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.domain.enums import DataMode, SourceType

from app.engines.document.constants import (
    AUTHORITATIVE_CONFIDENCE,
    CLASS_TO_PCE_KIND,
    DOCUMENT_CLASSES,
    ENGINE_VERSION,
    EXTRACTION_NOT_RUN,
    GOVERNANCE_NOTE,
    INTEGRITY_DUPLICATE_FILE,
    PCE_TYPE_TO_CLASS,
)
from app.engines.document.errors import DocumentError
from app.engines.document.extract import extract_from_bytes
from app.engines.document.integrity import find_duplicate_files, find_similar_documents, integrity_status
from app.engines.document.plan_sources import apply_to_plan, collect_plan_sources, detect_conflicts
from app.engines.document.repository import (
    add_document,
    artifact_payload,
    get_artifact,
    get_document,
    list_project_documents,
    mark_attached,
    save_bytes,
    upsert_artifact,
)
from app.engines.document.security import validate_upload
from app.engines.document.structure import build_structure
from app.engines.document.types import ExtractionResult, ExtractedField, PlanConflict
from app.engines.pce.service import parse_data_mode
from app.evidence.adapters.document import extraction_to_evidence
from app.evidence.constants import FRAUD_CLAIM_PATTERN
from app.evidence.provenance import build_provenance, build_source_ids
from app.evidence.repository import add_evidence_object
from app.models.artifacts import Document
from app.models.project import Project
from app.models.snapshot import DatasetSnapshot

_FRAUD_RE = re.compile(FRAUD_CLAIM_PATTERN, re.IGNORECASE)


def reject_fraud_text(*values: object) -> None:
    blob = "\n".join("" if item is None else str(item) for item in values)
    if _FRAUD_RE.search(blob):
        raise DocumentError(
            "Document Intelligence must not claim fraud or use fraud language.",
            code="fraud_language_forbidden",
            status_code=422,
        )


def normalize_document_class(value: str | None) -> str:
    text = (value or "").strip()
    if not text:
        raise DocumentError(
            "document_type is required. Choose BLUEPRINT, BOQ_ESTIMATE, "
            "PROJECT_DOCUMENT, PROGRESS_REPORT, COMPLETION_DOCUMENT, or OTHER.",
            code="invalid_document_type",
            status_code=422,
        )
    upper = text.replace("-", "_").replace(" ", "_").upper()
    if upper in DOCUMENT_CLASSES:
        return upper
    mapped = PCE_TYPE_TO_CLASS.get(text.casefold())
    if mapped:
        return mapped
    raise DocumentError(
        "Unsupported document_type. Use BLUEPRINT, BOQ_ESTIMATE, PROJECT_DOCUMENT, "
        "PROGRESS_REPORT, COMPLETION_DOCUMENT, or OTHER.",
        code="invalid_document_type",
        status_code=422,
    )


def _snapshot(session: Session, project: Project) -> DatasetSnapshot | None:
    return session.get(DatasetSnapshot, project.snapshot_id) if project.snapshot_id else project.snapshot


def _provenance(
    project: Project,
    data_mode: DataMode,
    snapshot: DatasetSnapshot | None,
    extra: str,
    extra_ids: list[str] | None = None,
) -> dict[str, Any]:
    source_type = (
        SourceType.SYNTHETIC_TEST_RECORD
        if data_mode == DataMode.SYNTHETIC
        else SourceType.HYBRID_ENRICHMENT
        if data_mode == DataMode.HYBRID
        else SourceType.DOCUMENT_ARTIFACT
    )
    obj = build_provenance(
        project,
        data_mode=data_mode,
        source_type=source_type,
        source_ids=build_source_ids(project.internal_project_id, extra_ids),
        snapshot=snapshot,
        extra_notes=extra,
    )
    return obj.model_dump(mode="json")


def _fields_from_payload(payload: dict[str, Any]) -> list[ExtractedField]:
    out: list[ExtractedField] = []
    for item in payload.get("fields") or []:
        if not isinstance(item, dict):
            continue
        out.append(
            ExtractedField(
                name=str(item.get("name") or ""),
                value=item.get("value"),
                unit=item.get("unit"),
                confidence=item.get("confidence"),
                extraction_method=str(item.get("extraction_method") or "unavailable"),
                source_location=item.get("source_location"),
                available=bool(item.get("available")),
                unavailable_reason=item.get("unavailable_reason"),
            )
        )
    return out


def _read_stored_bytes(document: Document) -> bytes | None:
    if not document.path:
        return None
    path = Path(document.path)
    if not path.is_absolute():
        from app.config import REPO_ROOT

        path = REPO_ROOT / path
    if not path.is_file():
        return None
    return path.read_bytes()


def upload_document(
    session: Session,
    project: Project,
    *,
    payload: bytes,
    filename: str | None,
    declared_mime: str | None,
    document_type: str,
    data_mode: DataMode,
) -> Document:
    reject_fraud_text(filename, document_type)
    if data_mode == DataMode.REAL and project.is_synthetic:
        raise DocumentError(
            "SYNTHETIC test projects cannot receive REAL document uploads.",
            code="mode_conflict",
            status_code=422,
        )
    document_class = normalize_document_class(document_type)
    mime_type, safe_name, size, digest = validate_upload(payload, filename, declared_mime)
    duplicates = find_duplicate_files(session, project_id=project.id, content_sha256=digest)
    duplicate_of = duplicates[0].id if duplicates else None
    status = INTEGRITY_DUPLICATE_FILE if duplicate_of else "UNIQUE"
    snapshot = _snapshot(session, project)
    provenance = _provenance(
        project,
        data_mode,
        snapshot,
        extra=(
            "Officer-uploaded file stored with SHA-256. Authenticity is not verified. "
            "The file is not executed. Extraction is not run automatically."
        ),
    )
    stored_path = save_bytes(project.id, safe_name, payload, digest)
    row = add_document(
        session,
        project.id,
        document_type=document_class,
        filename=safe_name,
        path=stored_path,
        mime_type=mime_type,
        file_size=size,
        content_sha256=digest,
        data_mode=data_mode,
        provenance=provenance,
        integrity_status=status,
        duplicate_of_id=duplicate_of,
    )
    session.flush()
    return row


def extract_document(
    session: Session,
    project: Project,
    document: Document,
    *,
    data_mode: DataMode | None = None,
) -> ExtractionResult:
    mode = data_mode or (DataMode(document.data_mode) if document.data_mode else DataMode.REAL)
    payload = _read_stored_bytes(document)
    if payload is None:
        raise DocumentError(
            "The stored file is missing, so extraction cannot run.",
            code="missing_file",
            status_code=409,
        )
    extraction = extract_from_bytes(payload, document.mime_type or "application/octet-stream")
    reject_fraud_text(extraction.get("combined_text"), *(extraction.get("notes") or []))
    structure = build_structure(extraction)
    similar = []
    if extraction.get("text_sha256"):
        similar = find_similar_documents(
            session,
            project_id=project.id,
            text_sha256=str(extraction["text_sha256"]),
            file_sha256=document.content_sha256 or "",
            exclude_id=document.id,
        )
    status = integrity_status(duplicate_of_id=document.duplicate_of_id, similar_ids=similar)
    document.integrity_status = status
    snapshot = _snapshot(session, project)
    provenance = _provenance(
        project,
        mode,
        snapshot,
        extra="Deterministic labelled-field extraction. OCR and LLM were not used.",
        extra_ids=[f"document:{document.id}"],
    )
    extraction["integrity_status"] = status
    artifact = upsert_artifact(
        session,
        document,
        extraction=extraction,
        structure=structure.as_dict(),
        status=str(extraction["status"]),
        method=str(extraction["extraction_method"]),
        text_sha256=extraction.get("text_sha256"),
        data_mode=mode,
        provenance=provenance,
    )
    evidence = extraction_to_evidence(
        project,
        document_id=document.id,
        data_mode=mode,
        extraction=extraction,
        conflicts=[],
        integrity_status=status,
        snapshot=snapshot,
    )
    row = add_evidence_object(session, evidence)
    session.flush()
    result = ExtractionResult(
        document_id=document.id,
        project_id=project.id,
        status=str(extraction["status"]),
        extraction_method=str(extraction["extraction_method"]),
        fields=_fields_from_payload(extraction),
        structure=structure,
        raw_text_available=bool(extraction.get("raw_text_available")),
        page_count=extraction.get("page_count"),
        text_sha256=extraction.get("text_sha256"),
        integrity_status=status,
        similar_document_ids=similar,
        duplicate_of_id=document.duplicate_of_id,
        evidence_id=row.evidence_id,
        data_mode=mode,
        notes=list(extraction.get("notes") or []) + [GOVERNANCE_NOTE],
        provenance=provenance,
    )
    _ = artifact
    return result


def attach_extracted_to_plan(
    session: Session,
    project: Project,
    document: Document,
) -> tuple[list[PlanConflict], list[str]]:
    payload = artifact_payload(get_artifact(session, document.id))
    extraction = payload.get("extraction") or {}
    if not extraction:
        raise DocumentError(
            "Extract the document before attaching facts to the plan.",
            code="extraction_not_run",
            status_code=409,
        )
    mode = DataMode(document.data_mode) if document.data_mode else DataMode.REAL
    snapshot = _snapshot(session, project)
    provenance = _provenance(
        project,
        mode,
        snapshot,
        extra="Officer attached extracted document facts to the plan overlay. Trusted extract values were not overwritten.",
        extra_ids=[f"document:{document.id}"],
    )
    _plan, conflicts, notes = apply_to_plan(
        session,
        project,
        document_id=document.id,
        extraction=extraction,
        data_mode=mode,
        provenance=provenance,
    )
    artifact = get_artifact(session, document.id)
    if artifact is not None:
        mark_attached(session, artifact, plan=True)
    existing = collect_plan_sources(session, project, data_mode=mode)
    conflicts.extend(detect_conflicts(existing))
    # De-duplicate conflict fields while preserving order.
    seen: set[str] = set()
    unique: list[PlanConflict] = []
    for item in conflicts:
        if item.field in seen:
            continue
        seen.add(item.field)
        unique.append(item)
    evidence = extraction_to_evidence(
        project,
        document_id=document.id,
        data_mode=mode,
        extraction=extraction,
        conflicts=unique,
        integrity_status=document.integrity_status or "UNIQUE",
        snapshot=snapshot,
    )
    add_evidence_object(session, evidence)
    return unique, notes


def attach_extracted_to_evidence(
    session: Session,
    project: Project,
    document: Document,
) -> str | None:
    payload = artifact_payload(get_artifact(session, document.id))
    extraction = payload.get("extraction") or {}
    if not extraction:
        raise DocumentError(
            "Extract the document before attaching facts as evidence.",
            code="extraction_not_run",
            status_code=409,
        )
    fields = {
        item["name"]: item
        for item in extraction.get("fields") or []
        if isinstance(item, dict) and item.get("available")
    }
    area = fields.get("area")
    if (
        area
        and area.get("value") is not None
        and (area.get("confidence") or 0) >= AUTHORITATIVE_CONFIDENCE
    ):
        document.observed_quantity = float(area["value"])
        document.observed_quantity_unit = area.get("unit") or "sq.ft"
    estimate = fields.get("estimate_amount") or fields.get("total_amount")
    if (
        estimate
        and estimate.get("value") is not None
        and (estimate.get("confidence") or 0) >= AUTHORITATIVE_CONFIDENCE
    ):
        document.observed_expenditure = float(estimate["value"])
    artifact = get_artifact(session, document.id)
    if artifact is not None:
        mark_attached(session, artifact, evidence=True)
    mode = DataMode(document.data_mode) if document.data_mode else DataMode.REAL
    snapshot = _snapshot(session, project)
    evidence = extraction_to_evidence(
        project,
        document_id=document.id,
        data_mode=mode,
        extraction=extraction,
        conflicts=[],
        integrity_status=document.integrity_status or "UNIQUE",
        snapshot=snapshot,
    )
    row = add_evidence_object(session, evidence)
    session.flush()
    return row.evidence_id


def document_read_payload(session: Session, document: Document) -> dict[str, Any]:
    artifact = get_artifact(session, document.id)
    payload = artifact_payload(artifact)
    extraction = payload.get("extraction") or {}
    structure = payload.get("structure") or {}
    return {
        "document_id": document.id,
        "project_id": document.project_id,
        "filename": document.filename,
        "mime_type": document.mime_type,
        "document_type": document.document_type,
        "pce_kind": CLASS_TO_PCE_KIND.get(document.document_type or "", document.kind),
        "uploaded_at": document.created_at.isoformat() if document.created_at else None,
        "data_mode": document.data_mode,
        "provenance": json.loads(document.provenance_json) if document.provenance_json else {},
        "content_sha256": document.content_sha256,
        "file_size": document.file_size,
        "extraction_status": document.extraction_status or EXTRACTION_NOT_RUN,
        "integrity_status": document.integrity_status,
        "duplicate_of_id": document.duplicate_of_id,
        "attached_to_plan": bool(artifact.attached_to_plan) if artifact else False,
        "attached_to_evidence": bool(artifact.attached_to_evidence) if artifact else False,
        "observed_quantity": document.observed_quantity,
        "observed_quantity_unit": document.observed_quantity_unit,
        "observed_expenditure": document.observed_expenditure,
        "extraction": {
            "status": extraction.get("status") or document.extraction_status or EXTRACTION_NOT_RUN,
            "extraction_method": extraction.get("extraction_method") or (artifact.extraction_method if artifact else None),
            "fields": extraction.get("fields") or [],
            "structure": structure,
            "page_count": extraction.get("page_count"),
            "raw_text_available": extraction.get("raw_text_available"),
            "notes": extraction.get("notes") or [],
            "text_sha256": extraction.get("text_sha256") or (artifact.text_sha256 if artifact else None),
        }
        if extraction or artifact
        else None,
        "engine_version": ENGINE_VERSION,
        "note": GOVERNANCE_NOTE,
    }


def list_conflicts(session: Session, project: Project, data_mode: DataMode) -> list[dict[str, Any]]:
    sources = collect_plan_sources(session, project, data_mode=data_mode)
    return [item.as_dict() for item in detect_conflicts(sources)]


__all__ = [
    "attach_extracted_to_evidence",
    "attach_extracted_to_plan",
    "document_read_payload",
    "extract_document",
    "get_document",
    "list_conflicts",
    "list_project_documents",
    "parse_data_mode",
    "upload_document",
]
