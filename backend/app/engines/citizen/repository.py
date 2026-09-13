"""Persist Jan-Sakshi citizen reports on the existing citizen_report table."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import DataMode
from app.models.citizen import CitizenReport


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


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc).isoformat()
    return value.isoformat()


def visible_mode(data_mode: DataMode, item_mode: str | None) -> bool:
    if data_mode == DataMode.REAL:
        return (item_mode or DataMode.REAL.value) == DataMode.REAL.value
    return True


def get_report(session: Session, report_id: int) -> CitizenReport | None:
    return session.get(CitizenReport, report_id)


def list_reports(session: Session, project_id: int) -> list[CitizenReport]:
    return list(
        session.scalars(
            select(CitizenReport).where(CitizenReport.project_id == project_id).order_by(CitizenReport.id)
        ).all()
    )


def add_report(
    session: Session,
    project_id: int,
    *,
    satisfaction_rating: int | None,
    observation_text: str | None,
    issue_category: str | None,
    latitude: float | None,
    longitude: float | None,
    proximity_m: float | None,
    submitted_at: datetime,
    image_id: int | None,
    submission_status: str,
    verification_result: str,
    timestamp_status: str,
    data_mode: DataMode,
    provenance: dict[str, Any],
    analysis: dict[str, Any] | None,
    duplicate_flag: str | None,
    watermark_path: str | None,
    evidence_ids: list[str],
    rejection_reason: str | None,
    synthetic: bool,
    capture_timestamp: str | None,
) -> CitizenReport:
    row = CitizenReport(
        project_id=project_id,
        latitude=latitude,
        longitude=longitude,
        proximity_m=proximity_m,
        structured_option=issue_category,
        rating_existence=satisfaction_rating,
        notes=observation_text,
        satisfaction_rating=satisfaction_rating,
        observation_text=observation_text,
        issue_category=issue_category,
        submitted_at=submitted_at,
        image_id=image_id,
        submission_status=submission_status,
        verification_result=verification_result,
        timestamp_status=timestamp_status,
        data_mode=data_mode.value,
        provenance_json=_dump(provenance),
        analysis_json=_dump(analysis or {}),
        duplicate_flag=duplicate_flag,
        watermark_path=watermark_path,
        evidence_ids_json=_dump(evidence_ids),
        rejection_reason=rejection_reason,
        synthetic=synthetic,
        capture_timestamp=capture_timestamp,
    )
    session.add(row)
    session.flush()
    return row


def save_report_payload(
    session: Session,
    row: CitizenReport,
    *,
    submission_status: str | None = None,
    verification_result: str | None = None,
    proximity_m: float | None = None,
    analysis: dict[str, Any] | None = None,
    evidence_ids: list[str] | None = None,
    duplicate_flag: str | None = None,
    watermark_path: str | None = None,
    rejection_reason: str | None = None,
    timestamp_status: str | None = None,
) -> CitizenReport:
    if submission_status is not None:
        row.submission_status = submission_status
    if verification_result is not None:
        row.verification_result = verification_result
    if proximity_m is not None:
        row.proximity_m = proximity_m
    if analysis is not None:
        row.analysis_json = _dump(analysis)
    if evidence_ids is not None:
        row.evidence_ids_json = _dump(evidence_ids)
    if duplicate_flag is not None:
        row.duplicate_flag = duplicate_flag
    if watermark_path is not None:
        row.watermark_path = watermark_path
    if rejection_reason is not None:
        row.rejection_reason = rejection_reason
    if timestamp_status is not None:
        row.timestamp_status = timestamp_status
    session.flush()
    return row


def provenance_of(row: CitizenReport) -> dict[str, Any]:
    return _load(row.provenance_json)


def analysis_of(row: CitizenReport) -> dict[str, Any]:
    return _load(row.analysis_json)


def evidence_ids_of(row: CitizenReport) -> list[str]:
    raw = row.evidence_ids_json
    if not raw:
        return []
    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(loaded, list):
        return []
    return [str(item) for item in loaded]


def recent_report_times(session: Session, project_id: int, data_mode: str) -> list[datetime]:
    rows = session.scalars(
        select(CitizenReport)
        .where(CitizenReport.project_id == project_id)
        .where(CitizenReport.data_mode == data_mode)
        .order_by(CitizenReport.id.desc())
    ).all()
    return [row.submitted_at or row.created_at for row in rows if (row.submitted_at or row.created_at)]
