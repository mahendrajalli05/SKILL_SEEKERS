"""Persist Image Evidence V1 rows on the existing photo table."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import REPO_ROOT
from app.domain.enums import DataMode
from app.models.artifacts import Photo

_UPLOAD_REL = Path("data") / "uploads" / "images"


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
    folder = REPO_ROOT / _UPLOAD_REL / str(project_id)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{digest[:16]}_{filename}"
    path.write_bytes(payload)
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/")


def resolve_stored_path(stored: str | None) -> Path | None:
    if not stored:
        return None
    path = Path(stored)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path if path.is_file() else None


def read_stored_bytes(photo: Photo) -> bytes | None:
    path = resolve_stored_path(photo.path)
    if path is None:
        return None
    return path.read_bytes()


def get_photo(session: Session, image_id: int) -> Photo | None:
    return session.get(Photo, image_id)


def list_project_photos(session: Session, project_id: int) -> list[Photo]:
    return list(
        session.scalars(select(Photo).where(Photo.project_id == project_id).order_by(Photo.id)).all()
    )


def list_comparable_photos(
    session: Session,
    *,
    data_mode: str,
    exclude_id: int | None = None,
) -> list[Photo]:
    stmt = select(Photo).where(Photo.data_mode == data_mode)
    if exclude_id is not None:
        stmt = stmt.where(Photo.id != exclude_id)
    return list(session.scalars(stmt).all())


def add_photo(
    session: Session,
    project_id: int,
    *,
    filename: str,
    path: str,
    mime_type: str,
    file_size: int,
    content_sha256: str,
    data_mode: DataMode,
    provenance: dict[str, Any],
    source: str = "officer_upload",
) -> Photo:
    row = Photo(
        project_id=project_id,
        filename=filename,
        path=path,
        mime_type=mime_type,
        file_size=file_size,
        content_sha256=content_sha256,
        source=source,
        data_mode=data_mode.value,
        provenance_json=_dump(provenance),
        analysis_status="NOT_RUN",
        integrity_status="UNIQUE",
        attached_to_evidence=0,
    )
    session.add(row)
    session.flush()
    return row


def store_analysis(
    session: Session,
    photo: Photo,
    *,
    ahash: str | None,
    dhash: str | None,
    phash: str | None,
    integrity_status: str,
    duplicate_of_id: int | None,
    analysis: dict[str, Any],
    analysis_status: str,
    latitude: float | None,
    longitude: float | None,
    captured_at: datetime | None,
) -> Photo:
    photo.ahash = ahash
    photo.dhash = dhash
    photo.phash = phash
    photo.integrity_status = integrity_status
    photo.duplicate_of_id = duplicate_of_id
    photo.analysis_json = _dump(analysis)
    photo.analysis_status = analysis_status
    photo.exif_lat = latitude
    photo.exif_lon = longitude
    photo.exif_time = captured_at
    session.flush()
    return photo


def mark_attached(session: Session, photo: Photo) -> None:
    photo.attached_to_evidence = 1
    session.flush()


def analysis_payload(photo: Photo) -> dict[str, Any]:
    return _load(photo.analysis_json)
