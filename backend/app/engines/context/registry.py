"""Load the contextual source registry. Source facts are not hard-coded in callers."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import REPO_ROOT, get_settings
from app.engines.context.constants import REGISTRY_RELATIVE
from app.engines.context.errors import ContextError
from app.engines.context.types import SourceRecord


def registry_path() -> Path:
    settings = get_settings()
    configured = getattr(settings, "context_data_dir", "") or ""
    if configured:
        base = Path(configured)
        if not base.is_absolute():
            base = REPO_ROOT / base
        candidate = base / "sources" / "registry.json"
        if candidate.is_file():
            return candidate
    return REPO_ROOT / REGISTRY_RELATIVE


def _record(raw: dict[str, Any]) -> SourceRecord:
    return SourceRecord(
        source_id=str(raw.get("source_id") or "").strip(),
        source_name=str(raw.get("source_name") or "").strip(),
        publisher=str(raw.get("publisher") or "").strip(),
        source_type=str(raw.get("source_type") or "").strip(),
        url=(str(raw["url"]).strip() if raw.get("url") else None),
        retrieval_date=(str(raw["retrieval_date"]).strip() if raw.get("retrieval_date") else None),
        dataset_version=(str(raw["dataset_version"]).strip() if raw.get("dataset_version") else None),
        geographic_level=str(raw.get("geographic_level") or "").strip() or "STATE",
        unit=(str(raw["unit"]).strip() if raw.get("unit") else None),
        update_frequency=(str(raw["update_frequency"]).strip() if raw.get("update_frequency") else None),
        license_note=(str(raw["license_note"]).strip() if raw.get("license_note") else None),
        transformation_notes=(
            str(raw["transformation_notes"]).strip() if raw.get("transformation_notes") else None
        ),
        limitations=[str(item) for item in (raw.get("limitations") or [])],
        active=bool(raw.get("active")),
        requires_credential=bool(raw.get("requires_credential")),
        credential_env=(str(raw["credential_env"]).strip() if raw.get("credential_env") else None),
        snapshot_relative_path=(
            str(raw["snapshot_relative_path"]).strip() if raw.get("snapshot_relative_path") else None
        ),
        real_mode_allowed=bool(raw.get("real_mode_allowed", True)),
        unavailable_reason=(str(raw["unavailable_reason"]).strip() if raw.get("unavailable_reason") else None),
        indicators=[str(item) for item in (raw.get("indicators") or [])],
        alternate_url=(str(raw["alternate_url"]).strip() if raw.get("alternate_url") else None),
    )


@lru_cache(maxsize=4)
def load_registry(path: str | None = None) -> list[SourceRecord]:
    file_path = Path(path) if path else registry_path()
    if not file_path.is_file():
        raise ContextError(
            "Contextual source registry is missing.",
            code="registry_missing",
            status_code=500,
        )
    payload = json.loads(file_path.read_text(encoding="utf-8"))
    sources = payload.get("sources") if isinstance(payload, dict) else payload
    if not isinstance(sources, list):
        raise ContextError("Contextual source registry is malformed.", code="malformed_source")
    records = [_record(item) for item in sources if isinstance(item, dict) and item.get("source_id")]
    if not records:
        raise ContextError("Contextual source registry has no sources.", code="registry_empty")
    return records


def reset_registry_cache() -> None:
    load_registry.cache_clear()


def get_source(source_id: str, path: str | None = None) -> SourceRecord | None:
    for item in load_registry(path):
        if item.source_id == source_id:
            return item
    return None


def sources_for_indicator(indicator: str, path: str | None = None) -> list[SourceRecord]:
    return [item for item in load_registry(path) if indicator in item.indicators]
