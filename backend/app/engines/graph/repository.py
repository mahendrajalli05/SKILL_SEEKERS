"""SQL and in-memory sources for Relationship Graph V1."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.engines.graph.types import GraphMode, GraphRecord
from app.engines.overlap.text import constituency_fields, preserve_source_text
from app.models.project import Project

_RECORD_CACHE: dict[tuple[str, str, str], tuple[GraphRecord, ...]] = {}


def project_to_graph_record(row: Project) -> GraphRecord:
    constituency, usable, kind, _reason = constituency_fields(row.constituency)
    description = (row.work_description or "").strip()
    source = preserve_source_text(row.source_work) or description
    amount = row.allocation_amount
    return GraphRecord(
        project_id=row.id,
        internal_project_id=row.internal_project_id,
        mp_name=(row.mp_name or "").strip(),
        work_description=description,
        source_work=source,
        category=(row.category or "").strip(),
        state=(row.state or "").strip(),
        constituency=constituency,
        constituency_usable=usable,
        constituency_kind=kind,
        ida=(row.ida or "").strip(),
        allocation_amount=int(amount) if amount is not None else None,
        recommended_date=row.recommended_date,
        city=(row.city or "").strip(),
        ward=(row.ward or "").strip(),
        block=(row.block or "").strip(),
        village=(row.village or "").strip(),
        is_synthetic=bool(row.is_synthetic),
    )


def _cache_key(session: Session, mode: GraphMode) -> tuple[str, str]:
    bind = session.get_bind()
    url = str(bind.url) if bind is not None else "memory"
    return (url, mode.value)


def load_graph_records(
    session: Session,
    *,
    mode: GraphMode,
    subject_is_synthetic: bool = False,
) -> tuple[GraphRecord, ...]:
    key = (*_cache_key(session, mode), str(subject_is_synthetic))
    cached = _RECORD_CACHE.get(key)
    if cached is not None:
        return cached
    stmt = select(Project).where(Project.is_synthetic == subject_is_synthetic)
    rows = session.scalars(stmt).all()
    packed = tuple(project_to_graph_record(row) for row in rows)
    _RECORD_CACHE[key] = packed
    return packed


def load_subject_record(session: Session, project_id: int) -> GraphRecord:
    project = session.get(Project, project_id)
    if project is None:
        raise KeyError(f"Project {project_id} was not found.")
    return project_to_graph_record(project)


class InMemoryGraphSource:
    def __init__(self, records: Sequence[GraphRecord]) -> None:
        self.records = tuple(records)

    def all_records(self) -> tuple[GraphRecord, ...]:
        return self.records


def clear_graph_record_cache() -> None:
    _RECORD_CACHE.clear()
