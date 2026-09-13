"""Adapter helpers for contextual sources."""

from __future__ import annotations

import json
import os
from typing import Any

from sqlalchemy.orm import Session

from app.domain.enums import DataMode
from app.engines.context.cache import cache_snapshot, fetch_remote_payload, load_snapshot_payload
from app.engines.context.constants import (
    FAILURE_MALFORMED_SOURCE,
    FAILURE_REQUIRES_CONFIGURATION,
    FAILURE_SOURCE_UNAVAILABLE,
    FAILURE_TIMEOUT,
    STATUS_UNAVAILABLE,
    UNAVAILABLE_CONFIDENCE,
)
from app.engines.context.types import ContextObservation, SourceRecord


def credential_available(source: SourceRecord) -> bool:
    if not source.requires_credential:
        return True
    env_name = source.credential_env or ""
    if env_name and os.environ.get(env_name, "").strip():
        return True
    if env_name == "SARVSAKSHI_DATA_GOV_IN_API_KEY":
        from app.config import get_settings

        return bool(get_settings().data_gov_in_api_key.strip())
    return False


def unavailable(
    indicator: str,
    source: SourceRecord | None,
    *,
    data_mode: DataMode,
    failure_code: str,
    notes: str,
    geographic_level: str | None = None,
    geo_key: str | None = None,
    context_kind: str,
) -> ContextObservation:
    return ContextObservation(
        indicator=indicator,
        status=STATUS_UNAVAILABLE,
        value=None,
        unit=source.unit if source else None,
        geographic_level=geographic_level,
        geo_key=geo_key,
        reference_year=None,
        reference_date=None,
        source_id=source.source_id if source else None,
        source_name=source.source_name if source else None,
        publisher=source.publisher if source else None,
        source_url=source.url if source else None,
        retrieval_date=source.retrieval_date if source else None,
        dataset_version=source.dataset_version if source else None,
        transformation=source.transformation_notes if source else None,
        limitations=list(source.limitations) if source else [notes],
        data_mode=data_mode,
        confidence=UNAVAILABLE_CONFIDENCE,
        quality="unavailable",
        context_kind=context_kind,
        failure_code=failure_code,
        notes=notes,
    )


def load_or_unavailable(
    session: Session | None,
    source: SourceRecord,
    indicator: str,
    *,
    data_mode: DataMode,
    context_kind: str,
    geo_key: str | None = None,
    geographic_level: str | None = None,
) -> tuple[Any, ContextObservation | None]:
    if source.requires_credential and not credential_available(source):
        return None, unavailable(
            indicator,
            source,
            data_mode=data_mode,
            failure_code=FAILURE_REQUIRES_CONFIGURATION,
            notes=(
                "This source requires configuration. No credential is present in the "
                "environment. The API key is not stored in source code."
            ),
            geographic_level=geographic_level,
            geo_key=geo_key,
            context_kind=context_kind,
        )
    if not source.active:
        code = source.unavailable_reason or FAILURE_SOURCE_UNAVAILABLE
        return None, unavailable(
            indicator,
            source,
            data_mode=data_mode,
            failure_code=code,
            notes=source.unavailable_reason or "Source is inactive in the registry.",
            geographic_level=geographic_level,
            geo_key=geo_key,
            context_kind=context_kind,
        )
    try:
        payload, file_hash, _retrieved = load_snapshot_payload(source)
    except (ValueError, json.JSONDecodeError):
        return None, unavailable(
            indicator,
            source,
            data_mode=data_mode,
            failure_code=FAILURE_MALFORMED_SOURCE,
            notes="The configured snapshot could not be parsed as JSON.",
            geographic_level=geographic_level,
            geo_key=geo_key,
            context_kind=context_kind,
        )
    if payload is None:
        remote, fail_code, remote_hash = fetch_remote_payload(source)
        if fail_code == FAILURE_TIMEOUT:
            return None, unavailable(
                indicator,
                source,
                data_mode=data_mode,
                failure_code=FAILURE_TIMEOUT,
                notes="Remote retrieval timed out. No substitute value was invented.",
                geographic_level=geographic_level,
                geo_key=geo_key,
                context_kind=context_kind,
            )
        if fail_code:
            return None, unavailable(
                indicator,
                source,
                data_mode=data_mode,
                failure_code=fail_code,
                notes="Live retrieval failed. No substitute value was invented.",
                geographic_level=geographic_level,
                geo_key=geo_key,
                context_kind=context_kind,
            )
        if remote is None:
            return None, unavailable(
                indicator,
                source,
                data_mode=data_mode,
                failure_code=FAILURE_SOURCE_UNAVAILABLE,
                notes="No verified snapshot is configured for this source.",
                geographic_level=geographic_level,
                geo_key=geo_key,
                context_kind=context_kind,
            )
        cache_snapshot(session, source, remote, remote_hash)
        return remote, None
    cache_snapshot(session, source, payload, file_hash)
    return payload, None
