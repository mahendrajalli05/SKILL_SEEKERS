"""Deterministic SARVSAKSHI Scheme IDs.

Format: SVK-{STATE}-{NNNNNN}

This is an internal application identifier. It is not an official MPLADS
Work ID. ``internal_project_id`` remains the database key. Scheme IDs are
computed from observed rows and are never written onto real project records.

Rank is 1-based among works that share the same internal state code, ordered
by ``internal_project_id``. For a frozen extract this is unique, stable, and
reproducible.
"""

from __future__ import annotations

import re
from collections import defaultdict

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.identity.state_codes import (
    BLANK_STATE_CODE,
    internal_state_code,
    is_blank_state,
)
from app.models.project import Project

SCHEME_ID_PATTERN = re.compile(r"^SVK-([A-Z]{2,3})-(\d{1,6})$", re.IGNORECASE)

_CACHE: dict[str, dict[str, str]] = {}


def format_scheme_id(state_code: str, rank: int) -> str:
    return f"SVK-{state_code}-{rank:06d}"


def parse_scheme_id(value: str | None) -> tuple[str, int] | None:
    text = (value or "").strip()
    match = SCHEME_ID_PATTERN.fullmatch(text)
    if match is None:
        return None
    return match.group(1).upper(), int(match.group(2))


def looks_like_scheme_id(value: str | None) -> bool:
    return parse_scheme_id(value) is not None


def _db_cache_key(db: Session) -> str:
    bind = db.get_bind()
    url = str(getattr(bind, "url", "") or "")
    return url or str(id(bind))


def _state_bucket_key(state: str | None) -> str:
    if is_blank_state(state):
        return BLANK_STATE_CODE
    return internal_state_code(state)


def _load_maps(db: Session) -> dict[str, str]:
    key = _db_cache_key(db)
    cached = _CACHE.get(key)
    if cached is not None:
        return cached
    rows = db.execute(
        select(Project.internal_project_id, Project.state).order_by(
            Project.internal_project_id.asc()
        )
    ).all()
    buckets: dict[str, list[str]] = defaultdict(list)
    for internal_id, state in rows:
        buckets[_state_bucket_key(state)].append(internal_id)
    mapping: dict[str, str] = {}
    for code, ids in buckets.items():
        for index, internal_id in enumerate(ids, start=1):
            mapping[internal_id] = format_scheme_id(code, index)
    _CACHE[key] = mapping
    return mapping


def scheme_ids_for_projects(db: Session, internal_ids: list[str]) -> dict[str, str]:
    mapping = _load_maps(db)
    return {item: mapping[item] for item in internal_ids if item in mapping}


def scheme_id_for_project(db: Session, project: Project) -> str:
    mapping = _load_maps(db)
    existing = mapping.get(project.internal_project_id)
    if existing:
        return existing
    # Newly inserted after cache build: recompute that bucket only.
    reset_scheme_id_cache()
    return _load_maps(db).get(
        project.internal_project_id,
        format_scheme_id(_state_bucket_key(project.state), 1),
    )


def resolve_scheme_id(db: Session, value: str | None) -> Project | None:
    parsed = parse_scheme_id(value)
    if parsed is None:
        return None
    code, rank = parsed
    if rank < 1:
        return None
    mapping = _load_maps(db)
    for internal_id, scheme_id in mapping.items():
        if scheme_id == format_scheme_id(code, rank):
            return db.scalar(
                select(Project).where(Project.internal_project_id == internal_id)
            )
    return None


def scheme_id_equals_filter(db: Session, value: str) -> list[int]:
    """Return matching SQLite ids for an exact Scheme ID."""
    row = resolve_scheme_id(db, value)
    return [row.id] if row is not None else []


def matching_internal_ids_for_scheme_query(
    db: Session,
    query: str,
    *,
    state: str | None = None,
) -> list[str]:
    """Return internal IDs whose computed Scheme ID contains ``query``.

    Scheme IDs are not stored on ``project`` rows. This scans the existing
    in-memory identifier map (already used for display) and does not load
    full project records. Matching is case-insensitive substring search.
    When ``state`` is provided, only that state's Scheme IDs are scanned.
    """
    needle = (query or "").strip().casefold()
    if not needle:
        return []
    mapping = _load_maps(db)
    prefix = f"SVK-{_state_bucket_key(state)}-".casefold() if state else None
    matches: list[str] = []
    for internal_id, scheme_id in mapping.items():
        folded = scheme_id.casefold()
        if prefix and not folded.startswith(prefix):
            continue
        if needle in folded:
            matches.append(internal_id)
    return matches


def state_filter_for_code(db: Session, code: str):
    """SQL clause matching observed states that share an internal code."""
    wanted = (code or "").strip().upper()
    if wanted == BLANK_STATE_CODE:
        return or_(Project.state.is_(None), Project.state == "")
    observed = db.scalars(
        select(Project.state).where(Project.state.is_not(None)).where(Project.state != "").distinct()
    ).all()
    names = [str(item) for item in observed if internal_state_code(str(item)) == wanted]
    if not names:
        return Project.state == "__no_such_state__"
    return Project.state.in_(names)


def count_projects_for_code(db: Session, code: str) -> int:
    clause = state_filter_for_code(db, code)
    return int(db.scalar(select(func.count()).select_from(Project).where(clause)) or 0)


def reset_scheme_id_cache() -> None:
    _CACHE.clear()
