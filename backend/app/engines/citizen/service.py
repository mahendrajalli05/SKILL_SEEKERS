"""Jan-Sakshi / Citizen Evidence V1.

Citizen-generated field evidence. Reuses Image Evidence V1, Geospatial
distance, Evidence Object V1, and Plan → Claim → Evidence framing.

Does not modify Cost, Time, Overlap, Compliance, Risk Fusion, Graph,
PCE comparison, Document, Image, Geospatial, Need & Impact, or Milestone engines.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.config import get_settings
from app.domain.enums import DataMode, SourceType
from app.engines.citizen.aggregate import aggregate_reports
from app.engines.citizen.analyze import analyze_feedback, normalize_issue_category
from app.engines.citizen.constants import (
    AUDIT_SUBMIT,
    AUDIT_VERIFY,
    COMMUNITY_SIGNAL_MIN,
    DEFAULT_RADIUS_METERS,
    DUPLICATE_FLAG,
    ENGINE_NAME,
    ENGINE_VERSION,
    ENTITY_TYPE,
    EXIF_NOTE,
    FORBIDDEN_OUTPUT_TERMS,
    GOVERNANCE_NOTE,
    HYBRID_NOTICE,
    INCONCLUSIVE,
    INSUFFICIENT_SAMPLE_MAX,
    LIMITATIONS,
    LOCATION_REJECTED,
    LOCATION_UNAVAILABLE,
    LOCATION_VERIFIED,
    MAX_SATISFACTION,
    MIN_REPORTS_FOR_CONCERN,
    MIN_SATISFACTION,
    PRIVACY_NOTE,
    RATE_LIMIT_COUNT,
    RATE_LIMIT_WINDOW_SECONDS,
    SOURCE_CITIZEN_UPLOAD,
    STATUS_ACCEPTED,
    STATUS_INCONCLUSIVE,
    STATUS_REJECTED,
    SYNTHETIC_BADGE,
    THRESHOLD_NOTE,
    TIMESTAMP_RECORDED,
    TIMESTAMP_SERVER_ONLY,
    TIMESTAMP_UNAVAILABLE,
    WATERMARK_NOTE,
)
from app.engines.citizen.errors import CitizenError
from app.engines.citizen.explain import submission_explanation
from app.engines.citizen.location import verify_location
from app.engines.citizen.pce_frame import frame_against_claim
from app.engines.citizen.repository import (
    add_report,
    analysis_of,
    evidence_ids_of,
    get_report,
    iso,
    list_reports,
    now_utc,
    provenance_of,
    recent_report_times,
    save_report_payload,
    visible_mode,
)
from app.engines.citizen.types import CitizenReportRecord, DuplicateSignal
from app.engines.citizen.watermark import save_watermark_copy
from app.engines.geo.location import project_location_for
from app.engines.image.constants import EXACT_DUPLICATE
from app.engines.image.errors import ImageError
from app.engines.image.repository import get_photo, read_stored_bytes
from app.engines.image.service import image_read_payload, upload_image
from app.engines.pce.service import assembled_claim_from_row, empty_claim
from app.evidence.adapters.citizen import report_to_evidence_objects, summary_to_evidence
from app.evidence.constants import FRAUD_CLAIM_PATTERN
from app.evidence.provenance import build_provenance, build_source_ids
from app.evidence.repository import add_evidence_object
from app.identity.scheme_id import scheme_id_for_project
from app.models.audit import AuditEvent
from app.models.citizen import CitizenReport
from app.models.project import Project
from app.models.snapshot import DatasetSnapshot

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
        raise CitizenError(
            "Jan-Sakshi must not claim fraud or use fraud language.",
            code="fraud_language_forbidden",
            status_code=422,
        )
    for term in FORBIDDEN_OUTPUT_TERMS:
        if term in blob:
            raise CitizenError(
                "Jan-Sakshi must not output fraud conclusions or payment-release language.",
                code="forbidden_output_term",
                status_code=422,
            )


def _snapshot(session: Session, project: Project) -> DatasetSnapshot | None:
    if project.snapshot_id:
        return session.get(DatasetSnapshot, project.snapshot_id)
    return project.snapshot


def _source_type(data_mode: DataMode) -> SourceType:
    if data_mode == DataMode.SYNTHETIC:
        return SourceType.SYNTHETIC_TEST_RECORD
    return SourceType.CITIZEN_REPORT


def _settings_radius() -> float:
    settings = get_settings()
    try:
        value = float(getattr(settings, "citizen_radius_meters", DEFAULT_RADIUS_METERS))
    except (TypeError, ValueError):
        value = DEFAULT_RADIUS_METERS
    if value <= 0:
        return DEFAULT_RADIUS_METERS
    return value


def _rate_limit_config() -> tuple[int, int]:
    settings = get_settings()
    try:
        count = int(getattr(settings, "citizen_rate_limit_count", RATE_LIMIT_COUNT))
    except (TypeError, ValueError):
        count = RATE_LIMIT_COUNT
    try:
        window = int(getattr(settings, "citizen_rate_limit_window_seconds", RATE_LIMIT_WINDOW_SECONDS))
    except (TypeError, ValueError):
        window = RATE_LIMIT_WINDOW_SECONDS
    return max(1, count), max(1, window)


def _sample_config() -> tuple[int, int, int]:
    settings = get_settings()
    try:
        insufficient = int(getattr(settings, "citizen_insufficient_sample_max", INSUFFICIENT_SAMPLE_MAX))
    except (TypeError, ValueError):
        insufficient = INSUFFICIENT_SAMPLE_MAX
    try:
        community = int(getattr(settings, "citizen_community_signal_min", COMMUNITY_SIGNAL_MIN))
    except (TypeError, ValueError):
        community = COMMUNITY_SIGNAL_MIN
    try:
        concern = int(getattr(settings, "citizen_min_reports_for_concern", MIN_REPORTS_FOR_CONCERN))
    except (TypeError, ValueError):
        concern = MIN_REPORTS_FOR_CONCERN
    return max(1, insufficient), max(insufficient + 1, community), max(2, concern)


def _parse_float(value: object, *, field: str) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise CitizenError(f"{field} must be a number.", code="invalid_coordinate", status_code=422) from exc


def _parse_rating(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        rating = int(value)
    except (TypeError, ValueError) as exc:
        raise CitizenError("satisfaction_rating must be an integer from 1 to 5.", code="invalid_rating", status_code=422) from exc
    if rating < MIN_SATISFACTION or rating > MAX_SATISFACTION:
        raise CitizenError("satisfaction_rating must be between 1 and 5.", code="invalid_rating", status_code=422)
    return rating


def _parse_timestamp(value: str | datetime | None) -> tuple[datetime | None, str | None]:
    if value is None or value == "":
        return None, None
    if isinstance(value, datetime):
        stamp = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return stamp, stamp.isoformat()
    text = str(value).strip()
    if not text:
        return None, None
    cleaned = text.replace("Z", "+00:00").replace("/", "-")
    if re.fullmatch(r"\d{4}:\d{2}:\d{2} \d{2}:\d{2}:\d{2}", cleaned):
        cleaned = cleaned.replace(":", "-", 2).replace(" ", "T", 1)
    try:
        parsed = datetime.fromisoformat(cleaned)
    except ValueError as exc:
        raise CitizenError(
            "capture_timestamp must be an ISO timestamp when supplied.",
            code="invalid_timestamp",
            status_code=422,
        ) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed, parsed.isoformat()


def _enforce_rate_limit(session: Session, project_id: int, data_mode: DataMode) -> None:
    count, window = _rate_limit_config()
    stamps = recent_report_times(session, project_id, data_mode.value)
    now = now_utc()
    recent = [item for item in stamps if (now - (item if item.tzinfo else item.replace(tzinfo=timezone.utc))).total_seconds() <= window]
    if len(recent) >= count:
        raise CitizenError(
            "Too many citizen submissions for this project in the prototype time window. Try again later.",
            code="rate_limited",
            status_code=429,
        )


def _privacy_payload(*, include_location: bool) -> dict[str, Any]:
    return {
        "citizen_gps_public": False,
        "location_included": include_location,
        "note": PRIVACY_NOTE,
    }


def _synthetic_badge(data_mode: DataMode) -> str | None:
    if data_mode == DataMode.SYNTHETIC:
        return SYNTHETIC_BADGE
    if data_mode == DataMode.HYBRID:
        return HYBRID_NOTICE
    return None


def _latest_claim(session: Session, project: Project, data_mode: DataMode):
    from app.engines.pce.repository import list_claims

    claims = [
        item
        for item in list_claims(session, project.id)
        if visible_mode(data_mode, item.data_mode)
    ]
    if not claims:
        return empty_claim(project, data_mode)
    return assembled_claim_from_row(project, claims[-1])


def _image_metadata(session: Session, image_id: int | None) -> dict[str, Any] | None:
    if image_id is None:
        return None
    photo = get_photo(session, image_id)
    if photo is None:
        return None
    payload = image_read_payload(session, photo)
    return {
        "image_id": photo.id,
        "content_sha256": payload.get("content_sha256"),
        "ahash": payload.get("ahash"),
        "dhash": payload.get("dhash"),
        "phash": payload.get("phash"),
        "integrity_status": payload.get("integrity_status"),
        "gps_available": payload.get("gps_available"),
        "capture_timestamp": payload.get("capture_timestamp"),
        "reported_latitude": payload.get("latitude"),
        "reported_longitude": payload.get("longitude"),
        "metadata_status": payload.get("metadata_status"),
        "metadata_source": EXIF_NOTE,
        "data_mode": payload.get("data_mode"),
        "thumbnail_data_url": payload.get("thumbnail_data_url"),
        "exif_note": EXIF_NOTE,
    }


def _duplicate_signal(session: Session, project: Project, photo, data_mode: DataMode) -> DuplicateSignal:
    if photo is None:
        return DuplicateSignal(
            flagged=False,
            flag=None,
            matched_image_id=None,
            matched_report_id=None,
            exact_duplicate=False,
            explanation="No image was submitted.",
        )
    exact = photo.integrity_status == EXACT_DUPLICATE or bool(photo.duplicate_of_id)
    if not exact:
        return DuplicateSignal(
            flagged=False,
            flag=None,
            matched_image_id=None,
            matched_report_id=None,
            exact_duplicate=False,
            explanation="No exact duplicate citizen image was detected.",
        )
    matched_image = photo.duplicate_of_id
    matched_report = None
    for row in list_reports(session, project.id):
        if row.image_id == matched_image and visible_mode(data_mode, row.data_mode):
            matched_report = row.id
            break
    return DuplicateSignal(
        flagged=True,
        flag=DUPLICATE_FLAG,
        matched_image_id=matched_image,
        matched_report_id=matched_report,
        exact_duplicate=True,
        explanation=(
            "An identical image hash was previously stored. Flagged "
            f"{DUPLICATE_FLAG} for review. This is not treated as a legal finding of wrongdoing."
        ),
    )


def to_record(
    session: Session,
    project: Project,
    row: CitizenReport,
    data_mode: DataMode,
    *,
    include_location: bool = False,
) -> CitizenReportRecord:
    analysis = analysis_of(row)
    location = (analysis.get("location_verification") or {})
    duplicate = analysis.get("duplicate") or (
        {
            "flagged": bool(row.duplicate_flag),
            "flag": row.duplicate_flag,
        }
        if row.duplicate_flag
        else None
    )
    image_meta = _image_metadata(session, row.image_id)
    location_public = {
        "result": row.verification_result,
        "project_gps_available": location.get("project_gps_available"),
        "citizen_gps_available": location.get("citizen_gps_available"),
        "distance_band": location.get("distance_band"),
        "threshold_meters": location.get("threshold_meters") or _settings_radius(),
        "reason": location.get("reason") or row.rejection_reason,
        "prototype_rule_note": THRESHOLD_NOTE,
        "project_location_synthetic": location.get("project_location_synthetic", False),
    }
    if include_location:
        location_public["distance_meters"] = location.get("distance_meters") if row.proximity_m is None else row.proximity_m
        location_public["latitude"] = row.latitude
        location_public["longitude"] = row.longitude
        location_public["verification_data"] = True
    else:
        location_public["distance_meters"] = None
    reasons = list(analysis.get("reasons") or [])
    if row.rejection_reason and row.rejection_reason not in reasons:
        reasons.append(row.rejection_reason)
    return CitizenReportRecord(
        citizen_report_id=row.id,
        project_id=project.id,
        scheme_id=scheme_id_for_project(session, project),
        internal_project_id=project.internal_project_id,
        satisfaction_rating=row.satisfaction_rating,
        observation_text=row.observation_text or row.notes,
        issue_category=row.issue_category or row.structured_option,
        submitted_at=iso(row.submitted_at) or iso(row.created_at),
        image_id=row.image_id,
        submission_status=row.submission_status or STATUS_INCONCLUSIVE,
        verification_result=row.verification_result or INCONCLUSIVE,
        timestamp_status=row.timestamp_status or TIMESTAMP_UNAVAILABLE,
        data_mode=row.data_mode or data_mode.value,
        provenance=provenance_of(row),
        location_verification=location_public,
        analysis=analysis.get("feedback"),
        duplicate=duplicate,
        watermark=analysis.get("watermark"),
        plan_claim_evidence=analysis.get("plan_claim_evidence"),
        evidence_ids=evidence_ids_of(row),
        rejection_reason=row.rejection_reason,
        reasons=reasons,
        synthetic=bool(row.synthetic) or data_mode != DataMode.REAL,
        synthetic_badge=_synthetic_badge(data_mode),
        image_hash=None if image_meta is None else image_meta.get("content_sha256"),
        image_metadata=None if image_meta is None else {key: value for key, value in image_meta.items() if key != "thumbnail_data_url"},
        thumbnail_data_url=None if image_meta is None else image_meta.get("thumbnail_data_url"),
        original_image_preserved=bool((analysis.get("watermark") or {}).get("original_preserved", True)),
        privacy=_privacy_payload(include_location=include_location),
        engine_version=ENGINE_VERSION,
        engine_name=ENGINE_NAME,
        governance_note=GOVERNANCE_NOTE,
        latitude=row.latitude if include_location else None,
        longitude=row.longitude if include_location else None,
        location_included=include_location,
    )


def _persist_evidence(
    session: Session,
    project: Project,
    row: CitizenReport,
    record: CitizenReportRecord,
    data_mode: DataMode,
) -> list[str]:
    snapshot = _snapshot(session, project)
    objects = report_to_evidence_objects(project, record, data_mode=data_mode, snapshot=snapshot)
    ids: list[str] = []
    for obj in objects:
        reject_forbidden_text(obj.finding, obj.explanation)
        stored = add_evidence_object(session, obj)
        if stored.evidence_id:
            ids.append(stored.evidence_id)
    summary = project_citizen_summary(session, project, data_mode, persist=False)
    aggregate = summary_to_evidence(project, summary, data_mode=data_mode, snapshot=snapshot)
    reject_forbidden_text(aggregate.finding, aggregate.explanation)
    stored_agg = add_evidence_object(session, aggregate)
    if stored_agg.evidence_id:
        ids.append(stored_agg.evidence_id)
    save_report_payload(session, row, evidence_ids=ids)
    return ids


def submit_citizen_report(
    session: Session,
    project: Project,
    payload: dict[str, Any],
    data_mode: DataMode,
    *,
    image_bytes: bytes | None = None,
    filename: str | None = None,
    declared_mime: str | None = None,
) -> CitizenReportRecord:
    reject_forbidden_text(
        payload.get("observation_text"),
        payload.get("issue_category"),
        filename,
    )
    if data_mode == DataMode.REAL and project.is_synthetic:
        raise CitizenError(
            "SYNTHETIC test projects cannot receive REAL citizen submissions.",
            code="mode_conflict",
            status_code=422,
        )
    _enforce_rate_limit(session, project.id, data_mode)
    rating = _parse_rating(payload.get("satisfaction_rating"))
    observation = (payload.get("observation_text") or payload.get("notes") or "").strip() or None
    category = normalize_issue_category(payload.get("issue_category") or payload.get("structured_option"))
    if payload.get("issue_category") and category is None:
        raise CitizenError(
            "issue_category must be one of work_quality, incomplete_work, delayed_work, location_concern, safety, or other.",
            code="invalid_issue_category",
            status_code=422,
        )
    lat = _parse_float(payload.get("latitude"), field="latitude")
    lon = _parse_float(payload.get("longitude"), field="longitude")
    capture_dt, capture_text = _parse_timestamp(payload.get("capture_timestamp") or payload.get("timestamp"))
    submitted_at = now_utc()
    snapshot = _snapshot(session, project)
    extra = (
        "Citizen field submission. No unnecessary identity data was collected. "
        f"{GOVERNANCE_NOTE} {THRESHOLD_NOTE}"
    )
    if data_mode != DataMode.REAL:
        extra = f"{extra} {SYNTHETIC_BADGE}"
    provenance = build_provenance(
        project,
        data_mode=data_mode,
        source_type=_source_type(data_mode),
        source_ids=build_source_ids(project.internal_project_id),
        snapshot=snapshot,
        extra_notes=extra,
    ).model_dump(mode="json")

    photo = None
    if image_bytes is not None:
        try:
            photo = upload_image(
                session,
                project,
                payload=image_bytes,
                filename=filename,
                declared_mime=declared_mime,
                data_mode=data_mode,
                source=SOURCE_CITIZEN_UPLOAD,
            )
        except ImageError as exc:
            raise CitizenError(exc.message, code=exc.code, status_code=exc.status_code) from exc

    image_meta = None
    if photo is not None:
        image_meta = _image_metadata(session, photo.id)
        if capture_text is None and image_meta and image_meta.get("capture_timestamp"):
            capture_text = str(image_meta.get("capture_timestamp"))
        if lat is None and image_meta and image_meta.get("reported_latitude") is not None:
            # Citizen GPS is the submitted location. EXIF is reported metadata only.
            pass

    if capture_text:
        timestamp_status = TIMESTAMP_RECORDED
    elif photo is not None and image_meta and image_meta.get("capture_timestamp"):
        timestamp_status = TIMESTAMP_RECORDED
        capture_text = str(image_meta.get("capture_timestamp"))
    else:
        timestamp_status = TIMESTAMP_UNAVAILABLE

    project_location = project_location_for(project, data_mode, snapshot=snapshot)
    location = verify_location(
        project_location=project_location,
        citizen_latitude=lat,
        citizen_longitude=lon,
        threshold_meters=_settings_radius(),
    )
    reasons: list[str] = [location.reason]
    duplicate = _duplicate_signal(session, project, photo, data_mode)
    watermark_result = None
    if photo is not None:
        original = image_bytes if image_bytes is not None else read_stored_bytes(photo)
        if original is not None:
            watermark_result = save_watermark_copy(
                original,
                project_id=project.id,
                original_digest=photo.content_sha256 or "",
                scheme_id=scheme_id_for_project(session, project),
                submitted_at=submitted_at.isoformat(),
                latitude=lat,
                longitude=lon,
            )
            after = read_stored_bytes(photo)
            if original != after:
                raise CitizenError(
                    "The original uploaded image must not be altered.",
                    code="original_image_mutated",
                    status_code=500,
                )
            reasons.append(WATERMARK_NOTE)

    feedback = analyze_feedback(observation, issue_category=category, satisfaction_rating=rating)
    if category is None:
        category = feedback.issue_category
    claim = _latest_claim(session, project, data_mode)
    pce = frame_against_claim(claim=claim, observation_text=observation, issue_category=category)

    status = STATUS_ACCEPTED
    rejection_reason = None
    if location.result == LOCATION_REJECTED:
        status = STATUS_REJECTED
        rejection_reason = location.reason
        reasons.append("Submission rejected because the citizen location is outside the prototype radius.")
    elif timestamp_status == TIMESTAMP_UNAVAILABLE:
        status = STATUS_INCONCLUSIVE
        reasons.append("Capture timestamp unavailable. Submission is INCONCLUSIVE.")
    elif location.result == INCONCLUSIVE:
        status = STATUS_INCONCLUSIVE
        reasons.append("Location could not be verified. Result is INCONCLUSIVE / LOCATION_UNAVAILABLE.")
    if rating is None and not observation and photo is None:
        raise CitizenError(
            "A satisfaction rating, observation, or photo is required.",
            code="empty_submission",
            status_code=422,
        )

    analysis_payload = {
        "location_verification": location.as_dict(),
        "feedback": feedback.as_dict(),
        "duplicate": duplicate.as_dict(),
        "watermark": None if watermark_result is None else watermark_result.as_dict(),
        "plan_claim_evidence": pce.as_dict(),
        "reasons": reasons,
        "explanation": submission_explanation(
            status=status,
            verification_result=location.result,
            reasons=reasons,
            duplicate_flagged=duplicate.flagged,
        ),
    }
    reject_forbidden_text(analysis_payload["explanation"], pce.note, feedback.explanation)

    row = add_report(
        session,
        project.id,
        satisfaction_rating=rating,
        observation_text=observation,
        issue_category=category,
        latitude=lat,
        longitude=lon,
        proximity_m=location.distance_meters,
        submitted_at=submitted_at,
        image_id=None if photo is None else photo.id,
        submission_status=status,
        verification_result=location.result,
        timestamp_status=timestamp_status,
        data_mode=data_mode,
        provenance=provenance,
        analysis=analysis_payload,
        duplicate_flag=duplicate.flag,
        watermark_path=None if watermark_result is None else watermark_result.watermark_path,
        evidence_ids=[],
        rejection_reason=rejection_reason,
        synthetic=data_mode != DataMode.REAL or bool(project.is_synthetic),
        capture_timestamp=capture_text,
    )
    session.flush()
    record = to_record(session, project, row, data_mode, include_location=False)
    ids = _persist_evidence(session, project, row, record, data_mode)
    session.add(
        AuditEvent(
            actor_role="citizen",
            action=AUDIT_SUBMIT,
            entity_type=ENTITY_TYPE,
            entity_id=str(row.id),
            payload=json.dumps(
                {
                    "project_id": project.id,
                    "citizen_report_id": row.id,
                    "submission_status": status,
                    "verification_result": location.result,
                    "data_mode": data_mode.value,
                    "evidence_ids": ids,
                },
                sort_keys=True,
            ),
        )
    )
    return to_record(session, project, row, data_mode, include_location=False)


def list_project_reports(
    session: Session,
    project: Project,
    data_mode: DataMode,
    *,
    include_location: bool = False,
) -> list[CitizenReportRecord]:
    rows = [item for item in list_reports(session, project.id) if visible_mode(data_mode, item.data_mode)]
    return [to_record(session, project, row, data_mode, include_location=include_location) for row in rows]


def get_report_record(
    session: Session,
    report_id: int,
    data_mode: DataMode | None = None,
    *,
    include_location: bool = False,
) -> CitizenReportRecord:
    row = get_report(session, report_id)
    if row is None:
        raise CitizenError("Citizen report not found.", code="not_found", status_code=404)
    project = session.get(Project, row.project_id)
    if project is None:
        raise CitizenError("Project not found.", code="not_found", status_code=404)
    mode = parse_data_mode(data_mode or row.data_mode, project)
    if not visible_mode(mode, row.data_mode):
        raise CitizenError("Citizen report not found.", code="not_found", status_code=404)
    return to_record(session, project, row, mode, include_location=include_location)


def verify_citizen_report(
    session: Session,
    report_id: int,
    data_mode: DataMode,
    *,
    include_location: bool = False,
) -> CitizenReportRecord:
    row = get_report(session, report_id)
    if row is None:
        raise CitizenError("Citizen report not found.", code="not_found", status_code=404)
    project = session.get(Project, row.project_id)
    if project is None:
        raise CitizenError("Project not found.", code="not_found", status_code=404)
    mode = parse_data_mode(data_mode, project)
    snapshot = _snapshot(session, project)
    project_location = project_location_for(project, mode, snapshot=snapshot)
    location = verify_location(
        project_location=project_location,
        citizen_latitude=row.latitude,
        citizen_longitude=row.longitude,
        threshold_meters=_settings_radius(),
    )
    reasons = [location.reason]
    status = row.submission_status or STATUS_INCONCLUSIVE
    rejection_reason = row.rejection_reason
    if location.result == LOCATION_REJECTED:
        status = STATUS_REJECTED
        rejection_reason = location.reason
    elif location.result == LOCATION_VERIFIED and row.timestamp_status == TIMESTAMP_RECORDED:
        status = STATUS_ACCEPTED
        rejection_reason = None
    elif location.result == INCONCLUSIVE:
        status = STATUS_INCONCLUSIVE
        reasons.append("Location could not be verified. Result is INCONCLUSIVE / LOCATION_UNAVAILABLE.")
    analysis = analysis_of(row)
    analysis["location_verification"] = location.as_dict()
    analysis["reasons"] = reasons
    save_report_payload(
        session,
        row,
        submission_status=status,
        verification_result=location.result,
        proximity_m=location.distance_meters,
        analysis=analysis,
        rejection_reason=rejection_reason,
    )
    record = to_record(session, project, row, mode, include_location=include_location)
    _persist_evidence(session, project, row, record, mode)
    session.add(
        AuditEvent(
            actor_role="officer",
            action=AUDIT_VERIFY,
            entity_type=ENTITY_TYPE,
            entity_id=str(row.id),
            payload=json.dumps(
                {
                    "project_id": project.id,
                    "citizen_report_id": row.id,
                    "verification_result": location.result,
                    "data_mode": mode.value,
                },
                sort_keys=True,
            ),
        )
    )
    return to_record(session, project, row, mode, include_location=include_location)


def project_citizen_summary(
    session: Session,
    project: Project,
    data_mode: DataMode,
    *,
    persist: bool = True,
):
    rows = [item for item in list_reports(session, project.id) if visible_mode(data_mode, item.data_mode)]
    snapshot = _snapshot(session, project)
    extra = (
        "Citizen aggregate is supporting community feedback only. "
        "A single report does not dominate the project conclusion. "
        "Citizen evidence is not added to Investigation Priority in V1."
    )
    if data_mode != DataMode.REAL:
        extra = f"{extra} {SYNTHETIC_BADGE}"
    provenance = build_provenance(
        project,
        data_mode=data_mode,
        source_type=_source_type(data_mode),
        source_ids=build_source_ids(project.internal_project_id),
        snapshot=snapshot,
        extra_notes=extra,
    ).model_dump(mode="json")
    insufficient, community, concern = _sample_config()
    evidence_ids: list[str] = []
    for row in rows:
        evidence_ids.extend(evidence_ids_of(row))
    summary = aggregate_reports(
        rows,
        project_id=project.id,
        internal_project_id=project.internal_project_id,
        scheme_id=scheme_id_for_project(session, project),
        data_mode=data_mode.value,
        provenance=provenance,
        evidence_ids=sorted(set(evidence_ids)),
        insufficient_max=insufficient,
        community_min=community,
        min_for_concern=concern,
        synthetic_badge=_synthetic_badge(data_mode),
        governance_note=GOVERNANCE_NOTE,
        privacy_note=PRIVACY_NOTE,
        limitations=list(LIMITATIONS),
        engine_version=ENGINE_VERSION,
        engine_name=ENGINE_NAME,
    )
    reject_forbidden_text(summary.explanation, summary.aggregate_finding)
    if persist:
        obj = summary_to_evidence(project, summary, data_mode=data_mode, snapshot=snapshot)
        stored = add_evidence_object(session, obj)
        if stored.evidence_id and stored.evidence_id not in summary.evidence_ids:
            summary.evidence_ids.append(stored.evidence_id)
    return summary


__all__ = [
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "get_report_record",
    "list_project_reports",
    "parse_data_mode",
    "project_citizen_summary",
    "submit_citizen_report",
    "verify_citizen_report",
]
