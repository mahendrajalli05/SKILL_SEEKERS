"""Deterministic Evidence Object identifiers."""

from __future__ import annotations

import hashlib
import re

_SAFE_TOKEN = re.compile(r"[^a-zA-Z0-9._-]+")


def _token(value: str) -> str:
    cleaned = _SAFE_TOKEN.sub("-", value.strip())
    return cleaned.strip("-") or "na"


def make_evidence_id(
    *,
    engine_name: str,
    engine_version: str,
    project_id: int,
    signal_type: str,
    data_mode: str,
    extra: str = "",
) -> str:
    """Stable ID for one engine/signal/mode assessment of a project.

    The digest covers identity fields only (not timestamps or scores) so
    re-persisting the same assessment keeps the same evidence_id.
    Optional ``extra`` distinguishes append-only observations (ML versions)
    without changing existing engine identifiers when omitted.
    """
    parts = [
        engine_name.strip(),
        engine_version.strip(),
        str(project_id),
        signal_type.strip(),
        data_mode.strip(),
    ]
    extra_token = extra.strip()
    if extra_token:
        parts.append(extra_token)
    payload = "|".join(parts)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return (
        f"ev:{_token(engine_name)}:{project_id}:{_token(signal_type)}:"
        f"{_token(data_mode)}:{digest}"
    )
