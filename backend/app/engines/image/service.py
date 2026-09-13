"""Image Evidence & Authenticity V1 orchestration.

Upload, hash, metadata, quality, Evidence Object recording, and PCE attach.
Does not change Cost, Time, Overlap, Compliance, Fusion, Graph, PCE, or Document.
"""

from __future__ import annotations

import base64
import json
import re
from io import BytesIO
from typing import Any

from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.domain.enums import DataMode, SourceType
from app.engines.image.constants import (
    ANALYSIS_COMPLETE,
    ANALYSIS_UNREADABLE,
    ENGINE_VERSION,
    GOVERNANCE_NOTE,
    INTEGRITY_UNREADABLE,
    SUPPORTING_ONLY_NOTE,
    TEST_WATERMARK,
    THUMBNAIL_MAX_PX,
)
from app.engines.image.errors import ImageError
from app.engines.image.evaluate import captured_at, evaluate_payload, persistable_analysis
from app.engines.image.repository import (
    add_photo,
    analysis_payload,
    get_photo,
    list_project_photos,
    mark_attached,
    read_stored_bytes,
    save_bytes,
    store_analysis,
)
from app.engines.image.security import validate_upload
from app.engines.image.types import ImageAnalysis, MetadataField, ReuseMatch, AuthenticityCapability
from app.evidence.adapters.image import analysis_to_evidence_objects
from app.evidence.constants import FRAUD_CLAIM_PATTERN
from app.evidence.provenance import build_provenance, build_source_ids
from app.evidence.repository import add_evidence_object, list_project_evidence
from app.models.artifacts import Photo
from app.models.project import Project
from app.models.snapshot import DatasetSnapshot

_FRAUD_RE = re.compile(FRAUD_CLAIM_PATTERN, re.IGNORECASE)


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
        raise ImageError(
            "Image Evidence must not claim fraud or use fraud language.",
            code="fraud_language_forbidden",
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
        else SourceType.IMAGE_ARTIFACT
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


def _thumbnail_data_url(payload: bytes | None) -> str | None:
    if not payload:
        return None
    try:
        with Image.open(BytesIO(payload)) as image:
            image.load()
            frame = image.convert("RGB")
            frame.thumbnail((THUMBNAIL_MAX_PX, THUMBNAIL_MAX_PX), Image.Resampling.LANCZOS)
            buf = BytesIO()
            frame.save(buf, format="JPEG", quality=70)
    except (UnidentifiedImageError, OSError, ValueError):
        return None
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def _analysis_from_payload(photo: Photo, payload: dict[str, Any]) -> ImageAnalysis | None:
    if not payload:
        return None
    authenticity_raw = payload.get("authenticity") or {}
    fields = []
    for item in payload.get("metadata_fields") or []:
        if not isinstance(item, dict):
            continue
        fields.append(
            MetadataField(
                field=str(item.get("field") or ""),
                value=item.get("value"),
                source=str(item.get("source") or ""),
                extraction_method=str(item.get("extraction_method") or "unavailable"),
                confidence=float(item.get("confidence") or 0),
                available=bool(item.get("available")),
                unavailable_reason=item.get("unavailable_reason"),
            )
        )

    def _matches(key: str) -> list[ReuseMatch]:
        out: list[ReuseMatch] = []
        for item in payload.get(key) or []:
            if not isinstance(item, dict):
                continue
            out.append(
                ReuseMatch(
                    image_id=int(item.get("image_id") or photo.id),
                    matched_image_id=int(item.get("matched_image_id") or 0),
                    matched_project_id=item.get("matched_project_id"),
                    hash_name=str(item.get("hash_name") or ""),
                    distance=int(item.get("distance") or 0),
                    similarity=float(item.get("hash_similarity") or item.get("similarity") or 0),
                    explanation=str(item.get("explanation") or ""),
                    confidence=float(item.get("confidence") or 0),
                    data_mode=item.get("data_mode"),
                )
            )
        return out

    mode = DataMode(payload.get("data_mode") or photo.data_mode or DataMode.REAL.value)
    return ImageAnalysis(
        image_id=photo.id,
        project_id=photo.project_id,
        content_sha256=str(payload.get("content_sha256") or photo.content_sha256 or ""),
        ahash=payload.get("ahash") or photo.ahash,
        dhash=payload.get("dhash") or photo.dhash,
        phash=payload.get("phash") or photo.phash,
        integrity_status=str(payload.get("integrity_status") or photo.integrity_status or "UNIQUE"),
        duplicate_of_id=payload.get("duplicate_of_id") if payload.get("duplicate_of_id") is not None else photo.duplicate_of_id,
        exact_duplicate=bool(payload.get("exact_duplicate")),
        potential_reuse=bool(payload.get("potential_reuse")),
        exact_matches=_matches("exact_matches"),
        reuse_matches=_matches("reuse_matches"),
        metadata_fields=fields,
        metadata_status=str(payload.get("metadata_status") or "METADATA_UNAVAILABLE"),
        gps_available=bool(payload.get("gps_available")),
        gps_message=payload.get("gps_message"),
        capture_timestamp=payload.get("capture_timestamp"),
        latitude=payload.get("latitude"),
        longitude=payload.get("longitude"),
        quality=payload.get("quality") or {},
        authenticity=AuthenticityCapability(
            capability=str(authenticity_raw.get("capability") or "NOT_IMPLEMENTED"),
            result=str(authenticity_raw.get("result") or "INCONCLUSIVE"),
            explanation=str(authenticity_raw.get("explanation") or ""),
            score=None,
        ),
        evidence_ids=list(payload.get("evidence_ids") or []),
        data_mode=mode,
        notes=list(payload.get("notes") or []),
        provenance=payload.get("provenance") or {},
    )


def _persist_evidence(session: Session, project: Project, analysis: ImageAnalysis) -> list[str]:
    snapshot = _snapshot(session, project)
    objects = analysis_to_evidence_objects(project, analysis, snapshot=snapshot)
    ids: list[str] = []
    for obj in objects:
        reject_fraud_text(obj.finding, obj.explanation)
        row = add_evidence_object(session, obj)
        if row.evidence_id:
            ids.append(row.evidence_id)
    analysis.evidence_ids = ids
    return ids


def upload_image(
    session: Session,
    project: Project,
    *,
    payload: bytes,
    filename: str | None,
    declared_mime: str | None,
    data_mode: DataMode,
    source: str = "officer_upload",
) -> Photo:
    reject_fraud_text(filename, source)
    if data_mode == DataMode.REAL and project.is_synthetic:
        raise ImageError(
            "SYNTHETIC test projects cannot receive REAL image uploads.",
            code="mode_conflict",
            status_code=422,
        )
    mime_type, safe_name, size, digest = validate_upload(payload, filename, declared_mime)
    snapshot = _snapshot(session, project)
    extra = (
        "Officer-uploaded photograph stored with SHA-256. The file is not executed. "
        "EXIF values are reported metadata from the uploaded file. "
        f"{SUPPORTING_ONLY_NOTE}"
    )
    if data_mode != DataMode.REAL:
        extra = f"{extra} {TEST_WATERMARK}"
    provenance = _provenance(project, data_mode, snapshot, extra)
    stored_path = save_bytes(project.id, safe_name, payload, digest)
    row = add_photo(
        session,
        project.id,
        filename=safe_name,
        path=stored_path,
        mime_type=mime_type,
        file_size=size,
        content_sha256=digest,
        data_mode=data_mode,
        provenance=provenance,
        source=source,
    )
    session.flush()
    analyze_image(session, project, row, payload=payload)
    return row


def analyze_image(
    session: Session,
    project: Project,
    photo: Photo,
    *,
    payload: bytes | None = None,
) -> ImageAnalysis:
    raw = payload if payload is not None else read_stored_bytes(photo)
    if raw is None:
        raise ImageError(
            "The stored image is missing, so analysis cannot run.",
            code="missing_file",
            status_code=409,
        )
    analysis = evaluate_payload(session, photo, raw)
    status = ANALYSIS_UNREADABLE if analysis.integrity_status == INTEGRITY_UNREADABLE else ANALYSIS_COMPLETE
    snapshot = _snapshot(session, project)
    extra = (
        "Deterministic SHA-256, perceptual hashing, reported EXIF extraction, "
        "and technical quality checks. Advanced authenticity analysis is INCONCLUSIVE. "
        "Satellite comparison was not performed."
    )
    if analysis.data_mode != DataMode.REAL:
        extra = f"{extra} {TEST_WATERMARK}"
    analysis.provenance = _provenance(
        project,
        analysis.data_mode,
        snapshot,
        extra=extra,
        extra_ids=[f"image:{photo.id}"],
    )
    evidence_ids = _persist_evidence(session, project, analysis)
    stored = persistable_analysis(analysis)
    stored["evidence_ids"] = evidence_ids
    stored["provenance"] = analysis.provenance
    store_analysis(
        session,
        photo,
        ahash=analysis.ahash,
        dhash=analysis.dhash,
        phash=analysis.phash,
        integrity_status=analysis.integrity_status,
        duplicate_of_id=analysis.duplicate_of_id,
        analysis=stored,
        analysis_status=status,
        latitude=analysis.latitude,
        longitude=analysis.longitude,
        captured_at=captured_at(analysis),
    )
    session.flush()
    return analysis


def attach_image_to_evidence(session: Session, project: Project, photo: Photo) -> list[str]:
    payload = analysis_payload(photo)
    analysis = _analysis_from_payload(photo, payload)
    if analysis is None:
        raw = read_stored_bytes(photo)
        if raw is None:
            raise ImageError(
                "Analyze the image before attaching it as evidence.",
                code="analysis_not_run",
                status_code=409,
            )
        analysis = analyze_image(session, project, photo, payload=raw)
    mark_attached(session, photo)
    if not photo.notes:
        photo.notes = SUPPORTING_ONLY_NOTE
    evidence_ids = analysis.evidence_ids or _persist_evidence(session, project, analysis)
    stored = persistable_analysis(analysis)
    stored["evidence_ids"] = evidence_ids
    stored["attached_to_evidence"] = True
    photo.analysis_json = json.dumps(stored, sort_keys=True, default=str)
    session.flush()
    return evidence_ids


def image_layer_confidence(session: Session, project_id: int, data_mode: DataMode) -> float:
    items = list_project_evidence(session, project_id, engine="image", data_mode=data_mode.value)
    if not items:
        return 0.0
    return round(sum(item.confidence for item in items) / len(items), 4)


def project_image_summary(session: Session, project: Project, data_mode: DataMode) -> dict[str, Any]:
    photos = [
        photo
        for photo in list_project_photos(session, project.id)
        if not (data_mode == DataMode.REAL and photo.data_mode and photo.data_mode != DataMode.REAL.value)
    ]
    gps_available = 0
    gps_unavailable = 0
    metadata_available = 0
    quality_warnings = 0
    exact = 0
    reuse = 0
    for photo in photos:
        payload = analysis_payload(photo)
        if payload.get("gps_available") or (photo.exif_lat is not None and photo.exif_lon is not None):
            gps_available += 1
        else:
            gps_unavailable += 1
        if payload.get("metadata_status") == "METADATA_PRESENT":
            metadata_available += 1
        warnings = (payload.get("quality") or {}).get("warnings") or []
        if warnings or not (payload.get("quality") or {}).get("readable", True):
            quality_warnings += 1
        if photo.integrity_status == "EXACT_DUPLICATE" or payload.get("exact_duplicate"):
            exact += 1
        elif photo.integrity_status == "POTENTIAL_IMAGE_REUSE" or payload.get("potential_reuse"):
            reuse += 1
    return {
        "images_submitted": len(photos),
        "exact_duplicates": exact,
        "potential_reuse": reuse,
        "gps_available": gps_available,
        "gps_unavailable": gps_unavailable,
        "metadata_available": metadata_available,
        "metadata_unavailable": len(photos) - metadata_available,
        "quality_warnings": quality_warnings,
        "advanced_authenticity_analysis": "INCONCLUSIVE",
        "authenticity_capability": "NOT_IMPLEMENTED",
        "evidence_confidence": image_layer_confidence(session, project.id, data_mode),
        "note": GOVERNANCE_NOTE,
    }


def image_read_payload(session: Session, photo: Photo) -> dict[str, Any]:
    payload = analysis_payload(photo)
    raw = read_stored_bytes(photo)
    stored_provenance = {}
    if photo.provenance_json:
        try:
            stored_provenance = json.loads(photo.provenance_json)
        except json.JSONDecodeError:
            stored_provenance = {}
    return {
        "image_id": photo.id,
        "project_id": photo.project_id,
        "filename": photo.filename,
        "mime_type": photo.mime_type,
        "file_size": photo.file_size,
        "uploaded_at": photo.created_at.isoformat() if photo.created_at else None,
        "content_sha256": photo.content_sha256,
        "ahash": photo.ahash,
        "dhash": photo.dhash,
        "phash": photo.phash,
        "integrity_status": photo.integrity_status,
        "duplicate_of_id": photo.duplicate_of_id,
        "analysis_status": photo.analysis_status,
        "attached_to_evidence": bool(photo.attached_to_evidence),
        "data_mode": photo.data_mode,
        "source": photo.source,
        "provenance": payload.get("provenance") or stored_provenance,
        "thumbnail_data_url": _thumbnail_data_url(raw),
        "exact_duplicate": bool(payload.get("exact_duplicate")),
        "potential_reuse": bool(payload.get("potential_reuse")),
        "exact_matches": payload.get("exact_matches") or [],
        "reuse_matches": payload.get("reuse_matches") or [],
        "metadata_status": payload.get("metadata_status") or "METADATA_UNAVAILABLE",
        "metadata_fields": payload.get("metadata_fields") or [],
        "gps_available": bool(payload.get("gps_available")),
        "gps_message": payload.get("gps_message") or "GPS metadata unavailable.",
        "capture_timestamp": payload.get("capture_timestamp"),
        "latitude": payload.get("latitude"),
        "longitude": payload.get("longitude"),
        "quality": payload.get("quality") or {},
        "authenticity": payload.get("authenticity")
        or {
            "capability": "NOT_IMPLEMENTED",
            "result": "INCONCLUSIVE",
            "explanation": "",
            "score": None,
        },
        "evidence_ids": payload.get("evidence_ids") or [],
        "evidence_confidence": image_layer_confidence(
            session,
            photo.project_id,
            DataMode(photo.data_mode) if photo.data_mode else DataMode.REAL,
        )
        if photo.data_mode
        else 0.0,
        "engine_version": ENGINE_VERSION,
        "note": GOVERNANCE_NOTE,
        "limitations": [
            SUPPORTING_ONLY_NOTE,
            "EXIF GPS and timestamps are reported metadata from the uploaded file.",
            "Advanced authenticity analysis: INCONCLUSIVE (NOT_IMPLEMENTED).",
            "Satellite / geospatial comparison is not performed in V1.",
        ],
    }


__all__ = [
    "analyze_image",
    "attach_image_to_evidence",
    "get_photo",
    "image_read_payload",
    "list_project_photos",
    "parse_data_mode",
    "project_image_summary",
    "upload_image",
]
