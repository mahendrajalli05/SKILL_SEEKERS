"""SQL and in-memory sources for Overlap Intelligence V1."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.engines.overlap.enrichment import HybridGps
from app.engines.overlap.text import (
    combine_place_text,
    constituency_fields,
    embedding_text,
    preserve_source_text,
    rare_block_tokens,
)
from app.engines.overlap.types import OverlapMode, OverlapRecord
from app.models.project import Project

_RECORD_CACHE: dict[tuple[str, str, str], tuple[OverlapRecord, ...]] = {}


def project_to_overlap_record(
    row: Project,
    *,
    gps: HybridGps | None = None,
    gps_is_synthetic: bool = False,
) -> OverlapRecord:
    constituency, usable, kind, _reason = constituency_fields(row.constituency)
    city = (row.city or "").strip()
    ward = (row.ward or "").strip()
    block = (row.block or "").strip()
    village = (row.village or "").strip()
    description = (row.work_description or "").strip()
    source = preserve_source_text(row.source_work) or description
    lat = gps.latitude if gps is not None else None
    lon = gps.longitude if gps is not None else None
    amount = row.allocation_amount
    return OverlapRecord(
        project_id=row.id,
        internal_project_id=row.internal_project_id,
        source_work=source,
        work_description=description,
        embedding_text=embedding_text(description),
        category=(row.category or "").strip(),
        constituency=constituency,
        constituency_usable=usable,
        constituency_kind=kind,
        state=(row.state or "").strip(),
        allocation_amount=int(amount) if amount is not None else None,
        recommended_date=row.recommended_date,
        city=city,
        ward=ward,
        block=block,
        village=village,
        place_text=combine_place_text(city=city, ward=ward, block=block, village=village),
        rare_tokens=rare_block_tokens(description),
        latitude=lat,
        longitude=lon,
        gps_is_synthetic=bool(gps_is_synthetic and lat is not None and lon is not None),
    )


def _cache_key(session: Session, mode: OverlapMode) -> tuple[str, str]:
    bind = session.get_bind()
    url = str(bind.url) if bind is not None else "memory"
    return (url, mode.value)


def load_overlap_records(
    session: Session,
    *,
    mode: OverlapMode,
    gps_by_id: dict[str, HybridGps] | None = None,
    subject_is_synthetic: bool = False,
) -> tuple[OverlapRecord, ...]:
    key = (*_cache_key(session, mode), str(subject_is_synthetic))
    cached = _RECORD_CACHE.get(key)
    if cached is not None:
        return cached
    stmt = select(Project).where(Project.is_synthetic == subject_is_synthetic)
    rows = session.scalars(stmt).all()
    gps_map = gps_by_id or {}
    records: list[OverlapRecord] = []
    if mode == OverlapMode.HYBRID_TEST:
        for row in rows:
            gps = gps_map.get(row.internal_project_id)
            if gps is None:
                continue
            records.append(project_to_overlap_record(row, gps=gps, gps_is_synthetic=True))
    else:
        for row in rows:
            records.append(project_to_overlap_record(row))
    packed = tuple(records)
    _RECORD_CACHE[key] = packed
    return packed


def load_subject_record(
    session: Session,
    project_id: int,
    *,
    mode: OverlapMode,
    gps_by_id: dict[str, HybridGps] | None = None,
) -> OverlapRecord:
    project = session.get(Project, project_id)
    if project is None:
        raise KeyError(f"Project {project_id} was not found.")
    gps = None
    synthetic = False
    if mode == OverlapMode.HYBRID_TEST:
        gps_map = gps_by_id or {}
        gps = gps_map.get(project.internal_project_id)
        synthetic = gps is not None
    return project_to_overlap_record(project, gps=gps, gps_is_synthetic=synthetic)


class InMemoryOverlapSource:
    def __init__(self, records: Sequence[OverlapRecord]) -> None:
        self.records = tuple(records)

    def all_records(self) -> tuple[OverlapRecord, ...]:
        return self.records


def clear_overlap_record_cache() -> None:
    _RECORD_CACHE.clear()
