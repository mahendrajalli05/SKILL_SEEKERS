"""Plan–Claim–Evidence V1 orchestration.

Records plan/claim/evidence and runs the deterministic consistency engine.
Does not change Cost, Time, Overlap, Compliance, Fusion, or Graph scoring.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.config import REPO_ROOT
from app.domain.enums import DataMode, SourceType
from app.engines.pce.compare import (
    collect_missing,
    compare_plan_claim_evidence,
    evidence_confidence,
    overall_result,
)
from app.engines.pce.constants import (
    ALLOWED_DOCUMENT_TYPES,
    ENGINE_NAME,
    GOVERNANCE_NOTE,
    HYBRID_CONFIDENCE_CAP,
    IMAGE_DOCUMENT_TYPES,
    REAL_CONFIDENCE_CAP,
    SYNTHETIC_CONFIDENCE_CAP,
)
from app.engines.pce.errors import PceError
from app.engines.pce.explain import (
    build_explanation,
    claim_findings as explain_claim,
    evidence_findings as explain_evidence,
    plan_findings as explain_plan,
)
from app.engines.pce.plan import assemble_plan
from app.engines.pce.repository import (
    add_claim,
    add_document,
    add_photo,
    claim_supporting_ids,
    get_plan,
    list_claims,
    list_documents,
    list_photos,
    upsert_plan,
)
from app.engines.pce.types import (
    AssembledClaim,
    AssembledEvidenceItem,
    AssembledPlan,
    ConsistencyStatus,
    VerificationResult,
)
from app.evidence.adapters.pce import attachment_to_evidence, verification_to_evidence
from app.evidence.constants import FRAUD_CLAIM_PATTERN
from app.evidence.provenance import build_provenance, build_source_ids
from app.evidence.repository import add_evidence_object, persist_evidence_object
from app.models.artifacts import Claim, Document, Photo
from app.models.project import Project
from app.models.snapshot import DatasetSnapshot

_FRAUD_RE = re.compile(FRAUD_CLAIM_PATTERN, re.IGNORECASE)
_DATE_ONLY = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_data_mode(value: str | DataMode | None, project: Project) -> DataMode:
    if project.is_synthetic:
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


def reject_fraud_text(*values: object) -> None:
    blob = "\n".join("" if item is None else str(item) for item in values)
    if _FRAUD_RE.search(blob):
        raise PceError(
            "Plan–Claim–Evidence must not claim fraud or use fraud language.",
            code="fraud_language_forbidden",
            status_code=422,
        )


def _parse_date(value: str | date | None) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError as exc:
        raise PceError("Dates must be ISO YYYY-MM-DD.", code="invalid_date", status_code=422) from exc


def _parse_datetime(value: str | datetime | None) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    if _DATE_ONLY.match(text):
        return datetime.fromisoformat(text)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PceError("Timestamps must be ISO-8601.", code="invalid_timestamp", status_code=422) from exc


def _mode_cap(data_mode: DataMode) -> float:
    if data_mode == DataMode.HYBRID:
        return HYBRID_CONFIDENCE_CAP
    if data_mode == DataMode.SYNTHETIC:
        return SYNTHETIC_CONFIDENCE_CAP
    return REAL_CONFIDENCE_CAP


def _source_type_for(data_mode: DataMode, primary: SourceType) -> SourceType:
    if data_mode == DataMode.SYNTHETIC:
        return SourceType.SYNTHETIC_TEST_RECORD
    if data_mode == DataMode.HYBRID:
        return SourceType.HYBRID_ENRICHMENT
    return primary


def _load_json(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _iso(value: datetime | date | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def assembled_claim_from_row(project: Project, row: Claim) -> AssembledClaim:
    data_mode = DataMode(row.data_mode) if row.data_mode else DataMode.REAL
    return AssembledClaim(
        project_id=project.id,
        claim_id=row.id,
        data_mode=data_mode,
        claimed_progress=row.reported_progress,
        claimed_progress_percent=row.claimed_progress_percent,
        claimed_expenditure=None if row.amount_used is None else float(row.amount_used),
        claimed_completion_state=row.completion_statement,
        claimed_quantity=row.claimed_quantity,
        claimed_quantity_unit=row.claimed_quantity_unit,
        milestone_claimed=row.milestone_label,
        claim_date=_iso(row.claim_date) or _iso(row.created_at),
        claimant_source=row.claimant_source,
        supporting_document_ids=claim_supporting_ids(row),
        provenance=_load_json(row.provenance_json),
        recorded=True,
    )


def empty_claim(project: Project, data_mode: DataMode) -> AssembledClaim:
    return AssembledClaim(
        project_id=project.id,
        claim_id=None,
        data_mode=data_mode,
        claimed_progress=None,
        claimed_progress_percent=None,
        claimed_expenditure=None,
        claimed_completion_state=None,
        claimed_quantity=None,
        claimed_quantity_unit=None,
        milestone_claimed=None,
        claim_date=None,
        claimant_source=None,
        supporting_document_ids=[],
        provenance={},
        recorded=False,
    )


def _filter_mode(data_mode: DataMode, item_mode: str | None) -> bool:
    if data_mode == DataMode.REAL:
        return (item_mode or DataMode.REAL.value) == DataMode.REAL.value
    if data_mode == DataMode.SYNTHETIC:
        return True
    return True


def assembled_evidence(
    project: Project,
    documents: list[Document],
    photos: list[Photo],
    data_mode: DataMode,
) -> list[AssembledEvidenceItem]:
    items: list[AssembledEvidenceItem] = []
    for doc in documents:
        if not _filter_mode(data_mode, doc.data_mode):
            continue
        items.append(
            AssembledEvidenceItem(
                evidence_kind=doc.document_type or doc.kind or "document",
                document_id=doc.id,
                photo_id=None,
                evidence_id=None,
                filename=doc.filename,
                source=doc.source,
                data_mode=DataMode(doc.data_mode) if doc.data_mode else DataMode.REAL,
                timestamp=_iso(doc.created_at),
                latitude=None,
                longitude=None,
                content_hash=doc.content_sha256,
                observed_quantity=doc.observed_quantity,
                observed_quantity_unit=doc.observed_quantity_unit,
                observed_expenditure=doc.observed_expenditure,
                notes=doc.notes,
                provenance=_load_json(doc.provenance_json),
            )
        )
    for photo in photos:
        if not _filter_mode(data_mode, photo.data_mode):
            continue
        items.append(
            AssembledEvidenceItem(
                evidence_kind="image",
                document_id=None,
                photo_id=photo.id,
                evidence_id=None,
                filename=photo.filename,
                source=photo.source,
                data_mode=DataMode(photo.data_mode) if photo.data_mode else DataMode.REAL,
                timestamp=_iso(photo.exif_time) or _iso(photo.created_at),
                latitude=photo.exif_lat,
                longitude=photo.exif_lon,
                content_hash=photo.phash,
                observed_quantity=photo.observed_quantity,
                observed_quantity_unit=photo.observed_quantity_unit,
                observed_expenditure=None,
                notes=photo.notes,
                provenance=_load_json(photo.provenance_json),
            )
        )
    return items


def get_project_plan(session: Session, project: Project, data_mode: DataMode) -> AssembledPlan:
    stored = get_plan(session, project.id)
    if stored is not None and data_mode == DataMode.REAL and stored.data_mode != DataMode.REAL.value:
        stored = None
    return assemble_plan(project, stored, data_mode=data_mode)


def record_plan(session: Session, project: Project, payload: dict[str, Any], data_mode: DataMode) -> AssembledPlan:
    reject_fraud_text(*payload.values())
    if data_mode == DataMode.REAL and project.is_synthetic:
        raise PceError("SYNTHETIC test projects cannot be recorded as REAL.", code="mode_conflict", status_code=422)
    snapshot = session.get(DatasetSnapshot, project.snapshot_id) if project.snapshot_id else project.snapshot
    source_type = _source_type_for(data_mode, SourceType.PLAN_RECORD)
    source_ids = build_source_ids(project.internal_project_id)
    provenance_obj = build_provenance(
        project,
        data_mode=data_mode,
        source_type=source_type,
        source_ids=source_ids,
        snapshot=snapshot,
        extra_notes="Officer-recorded plan overlay. Not an official MPLADS schema field unless sourced from the extract.",
    )
    upsert_plan(
        session,
        project.id,
        sanctioned_scope=payload.get("sanctioned_scope"),
        budget_estimate=payload.get("budget_estimate"),
        blueprint_document_id=payload.get("blueprint_document_id"),
        dimensions_value=payload.get("dimensions_value"),
        dimensions_unit=payload.get("dimensions_unit"),
        milestone_label=payload.get("milestone_label"),
        milestone_amount=payload.get("milestone_amount"),
        planned_start_date=_parse_date(payload.get("planned_start_date")),
        planned_completion_date=_parse_date(payload.get("planned_completion_date")),
        source=payload.get("source") or "officer_recorded",
        data_mode=data_mode,
        provenance=provenance_obj.model_dump(mode="json"),
    )
    session.flush()
    return get_project_plan(session, project, data_mode)


def record_claim(session: Session, project: Project, payload: dict[str, Any], data_mode: DataMode) -> AssembledClaim:
    reject_fraud_text(*payload.values())
    snapshot = session.get(DatasetSnapshot, project.snapshot_id) if project.snapshot_id else project.snapshot
    source_type = _source_type_for(data_mode, SourceType.CLAIM_STATEMENT)
    provenance_obj = build_provenance(
        project,
        data_mode=data_mode,
        source_type=source_type,
        source_ids=build_source_ids(project.internal_project_id),
        snapshot=snapshot,
        extra_notes="Claimant statement under evaluation. Not treated as an established fact.",
    )
    row = add_claim(
        session,
        project.id,
        reported_progress=payload.get("claimed_progress"),
        claimed_progress_percent=payload.get("claimed_progress_percent"),
        amount_used=payload.get("claimed_expenditure"),
        completion_statement=payload.get("claimed_completion_state"),
        claimed_quantity=payload.get("claimed_quantity"),
        claimed_quantity_unit=payload.get("claimed_quantity_unit"),
        milestone_label=payload.get("milestone_claimed") or payload.get("milestone_label"),
        claim_date=_parse_datetime(payload.get("claim_date")),
        claimant_source=payload.get("claimant_source"),
        supporting_document_ids=list(payload.get("supporting_document_ids") or []),
        data_mode=data_mode,
        provenance=provenance_obj.model_dump(mode="json"),
    )
    return assembled_claim_from_row(project, row)


def _save_bytes(project_id: int, filename: str | None, content: bytes | None) -> tuple[str | None, str | None]:
    if not content:
        return None, None
    digest = hashlib.sha256(content).hexdigest()
    safe_name = Path(filename or "upload.bin").name or "upload.bin"
    folder = REPO_ROOT / "data" / "uploads" / "pce" / str(project_id)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{digest[:16]}_{safe_name}"
    path.write_bytes(content)
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/"), digest


def record_evidence(
    session: Session,
    project: Project,
    payload: dict[str, Any],
    data_mode: DataMode,
    *,
    file_bytes: bytes | None = None,
) -> AssembledEvidenceItem:
    reject_fraud_text(*payload.values())
    document_type = str(payload.get("document_type") or payload.get("evidence_kind") or "supporting_document").casefold()
    if document_type not in ALLOWED_DOCUMENT_TYPES:
        raise PceError(
            "Unsupported document_type. Use pdf, document, blueprint, boq, image, "
            "supporting_document, inspection, or citizen.",
            code="invalid_document_type",
            status_code=422,
        )
    snapshot = session.get(DatasetSnapshot, project.snapshot_id) if project.snapshot_id else project.snapshot
    is_image = document_type in IMAGE_DOCUMENT_TYPES
    source_type = _source_type_for(
        data_mode,
        SourceType.IMAGE_ARTIFACT if is_image else SourceType.DOCUMENT_ARTIFACT,
    )
    filename = payload.get("filename")
    stored_path, digest = _save_bytes(project.id, filename, file_bytes)
    content_hash = payload.get("hash") or payload.get("content_sha256") or digest
    provenance_obj = build_provenance(
        project,
        data_mode=data_mode,
        source_type=source_type,
        source_ids=build_source_ids(project.internal_project_id),
        snapshot=snapshot,
        extra_notes="Officer-attached evidence recording layer. Image authenticity is not assessed in V1.",
    )
    if is_image:
        photo = add_photo(
            session,
            project.id,
            filename=filename,
            path=stored_path,
            source=payload.get("source") or "officer_upload",
            data_mode=data_mode,
            provenance=provenance_obj.model_dump(mode="json"),
            latitude=payload.get("latitude"),
            longitude=payload.get("longitude"),
            captured_at=_parse_datetime(payload.get("timestamp")),
            content_hash=content_hash,
            observed_quantity=payload.get("observed_quantity"),
            observed_quantity_unit=payload.get("observed_quantity_unit"),
            notes=payload.get("notes"),
        )
        item = AssembledEvidenceItem(
            evidence_kind="image",
            document_id=None,
            photo_id=photo.id,
            evidence_id=None,
            filename=photo.filename,
            source=photo.source,
            data_mode=data_mode,
            timestamp=_iso(photo.exif_time) or _iso(photo.created_at),
            latitude=photo.exif_lat,
            longitude=photo.exif_lon,
            content_hash=photo.phash,
            observed_quantity=photo.observed_quantity,
            observed_quantity_unit=photo.observed_quantity_unit,
            observed_expenditure=None,
            notes=photo.notes,
            provenance=provenance_obj.model_dump(mode="json"),
        )
    else:
        document = add_document(
            session,
            project.id,
            document_type=document_type,
            filename=filename,
            path=stored_path,
            source=payload.get("source") or "officer_upload",
            data_mode=data_mode,
            provenance=provenance_obj.model_dump(mode="json"),
            content_sha256=content_hash,
            observed_quantity=payload.get("observed_quantity"),
            observed_quantity_unit=payload.get("observed_quantity_unit"),
            observed_expenditure=payload.get("observed_expenditure"),
            notes=payload.get("notes"),
        )
        item = AssembledEvidenceItem(
            evidence_kind=document_type,
            document_id=document.id,
            photo_id=None,
            evidence_id=None,
            filename=document.filename,
            source=document.source,
            data_mode=data_mode,
            timestamp=_iso(document.created_at),
            latitude=None,
            longitude=None,
            content_hash=document.content_sha256,
            observed_quantity=document.observed_quantity,
            observed_quantity_unit=document.observed_quantity_unit,
            observed_expenditure=document.observed_expenditure,
            notes=document.notes,
            provenance=provenance_obj.model_dump(mode="json"),
        )
    extra_ids = []
    if item.document_id:
        extra_ids.append(f"document:{item.document_id}")
    if item.photo_id:
        extra_ids.append(f"photo:{item.photo_id}")
    evidence = attachment_to_evidence(project, item, extra_ids=extra_ids, snapshot=snapshot)
    row = add_evidence_object(session, evidence)
    item.evidence_id = row.evidence_id
    item.provenance = evidence.provenance.model_dump(mode="json")
    return item


def verify_project(
    session: Session,
    project: Project,
    data_mode: DataMode,
    *,
    persist: bool = True,
) -> VerificationResult:
    plan = get_project_plan(session, project, data_mode)
    claims = list_claims(session, project.id)
    visible_claims = [
        row
        for row in claims
        if _filter_mode(data_mode, row.data_mode)
    ]
    claim = (
        assembled_claim_from_row(project, visible_claims[0])
        if visible_claims
        else empty_claim(project, data_mode)
    )
    evidence_items = assembled_evidence(
        project,
        list_documents(session, project.id),
        list_photos(session, project.id),
        data_mode,
    )
    comparisons = compare_plan_claim_evidence(plan, claim, evidence_items)
    overall = overall_result(
        comparisons,
        has_claim=claim.recorded,
        has_evidence=bool(evidence_items),
    )
    missing = collect_missing(comparisons, plan, claim)
    if not evidence_items and "supporting evidence" not in missing:
        missing.append("supporting evidence")
    explanation = build_explanation(overall, comparisons, plan, claim, evidence_items, missing)
    reject_fraud_text(explanation, overall.value, *missing)
    confidence = evidence_confidence(
        comparisons,
        overall,
        data_mode_cap=_mode_cap(data_mode),
        has_evidence=bool(evidence_items),
    )
    snapshot = session.get(DatasetSnapshot, project.snapshot_id) if project.snapshot_id else project.snapshot
    result = VerificationResult(
        project_id=project.id,
        internal_project_id=project.internal_project_id,
        overall_result=overall,
        data_mode=data_mode,
        plan_findings=explain_plan(plan),
        claim_findings=explain_claim(claim),
        evidence_findings=explain_evidence(evidence_items),
        mismatches=[item for item in comparisons if item.status == ConsistencyStatus.MISMATCH],
        missing_information=missing,
        comparisons=comparisons,
        evidence_confidence=confidence,
        explanation=explanation,
        provenance=plan.provenance,
        evidence_ids=[item.evidence_id for item in evidence_items if item.evidence_id],
        note=GOVERNANCE_NOTE,
    )
    if persist:
        obj = verification_to_evidence(result, project, snapshot=snapshot)
        persist_evidence_object(session, obj, replace_engine=ENGINE_NAME)
        result.evidence_ids = [obj.evidence_id, *result.evidence_ids]
        result.provenance = obj.provenance.model_dump(mode="json")
    return result
