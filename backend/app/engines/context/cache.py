"""Simple snapshot cache for external contextual datasets.

Stores retrieval timestamp, source version, payload hash, and processing
version. Does not fetch remote sources on every project page load.
"""

from __future__ import annotations

import hashlib
import json
import socket
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import REPO_ROOT, get_settings
from app.engines.context.constants import (
    ENGINE_VERSION,
    FAILURE_MALFORMED_SOURCE,
    FAILURE_SOURCE_UNAVAILABLE,
    FAILURE_TIMEOUT,
)
from app.engines.context.types import SourceRecord
from app.models.context import ExternalContextSnapshot


def context_data_root() -> Path:
    settings = get_settings()
    configured = getattr(settings, "context_data_dir", "") or "data/external"
    path = Path(configured)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def snapshot_file(source: SourceRecord) -> Path | None:
    if not source.snapshot_relative_path:
        return None
    return context_data_root() / source.snapshot_relative_path


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def load_snapshot_payload(source: SourceRecord) -> tuple[dict[str, Any] | list[Any] | None, str | None, str | None]:
    path = snapshot_file(source)
    if path is None or not path.is_file():
        return None, None, None
    text = path.read_text(encoding="utf-8")
    payload = json.loads(text)
    return payload, file_sha256(path), datetime.now(timezone.utc).isoformat()


def fetch_remote_payload(source: SourceRecord) -> tuple[Any | None, str | None, str | None]:
    """Optional live retrieval. Off by default so project pages use snapshots."""
    settings = get_settings()
    if not getattr(settings, "context_live_fetch", False):
        return None, None, None
    url = source.url or ""
    if not url or url.startswith("test://"):
        return None, FAILURE_SOURCE_UNAVAILABLE, None
    timeout = float(getattr(settings, "context_http_timeout_seconds", 8.0) or 8.0)
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            raw = response.read()
        payload = json.loads(raw.decode("utf-8"))
        return payload, None, hashlib.sha256(raw).hexdigest()
    except TimeoutError:
        return None, FAILURE_TIMEOUT, None
    except socket.timeout:
        return None, FAILURE_TIMEOUT, None
    except urllib.error.URLError as exc:
        reason = str(getattr(exc, "reason", exc)).casefold()
        if "timed out" in reason or isinstance(getattr(exc, "reason", None), TimeoutError):
            return None, FAILURE_TIMEOUT, None
        return None, FAILURE_SOURCE_UNAVAILABLE, None
    except json.JSONDecodeError:
        return None, FAILURE_MALFORMED_SOURCE, None


def cache_snapshot(
    session: Session | None,
    source: SourceRecord,
    payload: object,
    file_hash: str | None,
) -> None:
    if session is None:
        return
    now = datetime.now(timezone.utc)
    existing = session.scalars(
        select(ExternalContextSnapshot).where(ExternalContextSnapshot.source_id == source.source_id)
    ).first()
    blob = json.dumps(payload, sort_keys=True, default=str)
    if existing is None:
        session.add(
            ExternalContextSnapshot(
                source_id=source.source_id,
                retrieval_at=now,
                source_version=source.dataset_version,
                file_sha256=file_hash,
                payload_json=blob,
                processing_version=ENGINE_VERSION,
                notes="Local snapshot cache. Filesystem paths are not exposed on the API.",
            )
        )
    else:
        existing.retrieval_at = now
        existing.source_version = source.dataset_version
        existing.file_sha256 = file_hash
        existing.payload_json = blob
        existing.processing_version = ENGINE_VERSION
    session.flush()


def cached_payload(session: Session | None, source_id: str) -> dict[str, Any] | list[Any] | None:
    if session is None:
        return None
    row = session.scalars(
        select(ExternalContextSnapshot).where(ExternalContextSnapshot.source_id == source_id)
    ).first()
    if row is None or not row.payload_json:
        return None
    try:
        return json.loads(row.payload_json)
    except json.JSONDecodeError:
        return None
