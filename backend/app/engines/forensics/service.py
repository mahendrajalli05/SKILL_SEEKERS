"""Advanced Image Forensics V1 orchestration.

Reuses Image Evidence V1 photo storage, hashes, EXIF, and quality.
Writes Evidence Object V1. Does not change Risk Fusion V1.1.
"""

from __future__ import annotations

import json
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import DataMode, SourceType
from app.engines.forensics.constants import (
    ENGINE_NAME,
    GOVERNANCE_NOTE,
    TEST_WATERMARK,
)
from app.engines.forensics.errors import ForensicsError
from app.engines.forensics.evaluate import evaluate_image_forensics
from app.engines.forensics.types import ForensicResult
from app.engines.image.repository import analysis_payload, get_photo, read_stored_bytes
from app.engines.image.service import image_read_payload, parse_data_mode
from app.evidence.adapters.forensics import result_to_evidence_objects
from app.evidence.constants import FRAUD_CLAIM_PATTERN
from app.evidence.provenance import build_provenance, build_source_ids
from app.evidence.repository import add_evidence_object
from app.models.artifacts import Photo
from app.models.evidence import EvidenceObjectRow
from app.models.project import Project
from app.models.snapshot import DatasetSnapshot

_FRAUD_RE = re.compile(FRAUD_CLAIM_PATTERN, re.IGNORECASE)
_CERTAINTY_RE = re.compile(
    r"\b(this (image|photo) is fake|fake image|fraud(ulent)?|definitely ai-generated|definitely manipulated)\b",
    re.IGNORECASE,
)


def reject_forbidden_wording(*values: object) -> None:
    blob = "\n".join("" if item is None else str(item) for item in values)
    if _FRAUD_RE.search(blob) or _CERTAINTY_RE.search(blob):
        raise ForensicsError(
            "Image Forensics must not claim fraud or false certainty.",
            code="forbidden_wording",
            status_code=422,
        )


def _snapshot(session: Session, project: Project) -> DatasetSnapshot | None:
    return session.get(DatasetSnapshot, project.snapshot_id) if project.snapshot_id else project.snapshot


def _visible_mode(requested: DataMode, stored: str | None) -> bool:
    stored_mode = str(stored or DataMode.REAL.value).upper()
    if requested == DataMode.REAL and stored_mode != DataMode.REAL.value:
        return False
    return True


def _latest_claim(session: Session, project: Project, data_mode: DataMode):
    from app.engines.pce.repository import list_claims
    from app.engines.pce.service import assembled_claim_from_row
    from app.engines.pce.types import AssembledClaim

    claims = [
        item
        for item in list_claims(session, project.id)
        if not (data_mode == DataMode.REAL and str(item.data_mode or "").upper() not in {"", "REAL"})
    ]
    if not claims:
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
            recorded=False,
        )
    return assembled_claim_from_row(project, claims[0])


def _delete_forensics_for_image(session: Session, project_id: int, image_id: int, data_mode: DataMode) -> None:
    existing = session.scalars(
        select(EvidenceObjectRow).where(
            EvidenceObjectRow.project_id == project_id,
            EvidenceObjectRow.engine == ENGINE_NAME,
            EvidenceObjectRow.data_mode == data_mode.value,
        )
    ).all()
    for row in existing:
        facts = list(row.facts)
        keep = True
        for fact in facts:
            if fact.key == "image_id" and str(fact.value) == str(image_id):
                keep = False
                break
        if keep:
            continue
        for fact in facts:
            session.delete(fact)
        session.delete(row)
    session.flush()


def persist_forensics_evidence(
    session: Session,
    project: Project,
    result: ForensicResult,
) -> list[str]:
    snapshot = _snapshot(session, project)
    objects = result_to_evidence_objects(project, result, snapshot=snapshot)
    _delete_forensics_for_image(session, project.id, result.image_id, result.data_mode)
    ids: list[str] = []
    for obj in objects:
        reject_forbidden_wording(obj.finding, obj.explanation)
        row = add_evidence_object(session, obj)
        if row.evidence_id:
            ids.append(row.evidence_id)
    result.evidence_ids = ids
    return ids


def _store_forensics(photo: Photo, result: ForensicResult) -> None:
    payload = result.as_dict()
    photo.forensics_json = json.dumps(payload, sort_keys=True, default=str)
    photo.forensics_status = "ANALYZED"
    # Do not rewrite stored image bytes or Image Evidence analysis_json.


def run_image_forensics(
    session: Session,
    project: Project,
    photo: Photo,
    *,
    data_mode: DataMode | None = None,
    persist: bool = True,
) -> ForensicResult:
    mode = parse_data_mode(data_mode or photo.data_mode, project)
    if not _visible_mode(mode, photo.data_mode):
        raise ForensicsError(
            "This image is not visible in REAL mode because it is labelled HYBRID or SYNTHETIC.",
            code="mode_hidden",
            status_code=404,
        )
    reject_forbidden_wording(photo.filename, photo.source)
    raw = read_stored_bytes(photo)
    analysis = analysis_payload(photo)
    claim = _latest_claim(session, project, mode)
    result = evaluate_image_forensics(
        image_id=photo.id,
        project_id=project.id,
        payload=raw,
        stored_sha256=photo.content_sha256,
        mime_type=photo.mime_type,
        file_size=photo.file_size,
        data_mode=mode,
        image_analysis=analysis,
        claim=claim,
        filename=photo.filename,
        ahash=photo.ahash,
        dhash=photo.dhash,
        phash=photo.phash,
    )
    snapshot = _snapshot(session, project)
    extra = (
        "Advanced Image Forensics V1 on an officer-uploaded photograph stored by Image Evidence V1. "
        "Original bytes are not modified. Project images are not transmitted externally. "
        f"{GOVERNANCE_NOTE}"
    )
    if mode != DataMode.REAL:
        extra = f"{extra} {TEST_WATERMARK}"
    source_type = (
        SourceType.SYNTHETIC_TEST_RECORD
        if mode == DataMode.SYNTHETIC
        else SourceType.HYBRID_ENRICHMENT
        if mode == DataMode.HYBRID
        else SourceType.IMAGE_ARTIFACT
    )
    result.provenance = build_provenance(
        project,
        data_mode=mode,
        source_type=source_type,
        source_ids=build_source_ids(project.internal_project_id, [f"image:{photo.id}"]),
        snapshot=snapshot,
        extra_notes=extra,
    ).model_dump(mode="json")
    reject_forbidden_wording(result.explanation, result.finding, result.overall_assessment)
    read_payload = image_read_payload(session, photo)
    result.thumbnail_data_url = read_payload.get("thumbnail_data_url")
    if persist:
        result.evidence_ids = persist_forensics_evidence(session, project, result)
        stored = result.as_dict()
        stored["evidence_ids"] = result.evidence_ids
        stored["provenance"] = result.provenance
        photo.forensics_json = json.dumps(stored, sort_keys=True, default=str)
        photo.forensics_status = "ANALYZED"
        session.flush()
    return result


def get_image_forensics(
    session: Session,
    project: Project,
    photo: Photo,
    *,
    data_mode: DataMode | None = None,
) -> ForensicResult:
    return run_image_forensics(session, project, photo, data_mode=data_mode, persist=True)


__all__ = [
    "get_image_forensics",
    "parse_data_mode",
    "reject_forbidden_wording",
    "run_image_forensics",
]
