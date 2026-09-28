"""SQL and in-memory sources for Overlap Intelligence V1."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, timedelta

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.engines.overlap.constants import DATE_CANDIDATE_WINDOW_DAYS
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


import sys

_INTERN_MAX_LEN = 120


def _intern(value: str | None) -> str:
    if not value:
        return ""
    s = value.strip()
    return sys.intern(s) if len(s) <= _INTERN_MAX_LEN else s


PROJECT_OVERLAP_COLUMNS = (
    Project.id,
    Project.internal_project_id,
    Project.source_work,
    Project.work_description,
    Project.category,
    Project.constituency,
    Project.state,
    Project.allocation_amount,
    Project.recommended_date,
    Project.city,
    Project.ward,
    Project.block,
    Project.village,
    Project.is_synthetic,
)


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
        internal_project_id=_intern(row.internal_project_id),
        source_work=source,
        work_description=description,
        embedding_text=embedding_text(description),
        category=_intern(row.category),
        constituency=_intern(constituency),
        constituency_usable=usable,
        constituency_kind=_intern(kind),
        state=_intern(row.state),
        allocation_amount=int(amount) if amount is not None else None,
        recommended_date=row.recommended_date,
        city=_intern(city),
        ward=_intern(ward),
        block=_intern(block),
        village=_intern(village),
        place_text=combine_place_text(city=city, ward=ward, block=block, village=village),
        rare_tokens=rare_block_tokens(description),
        latitude=lat,
        longitude=lon,
        gps_is_synthetic=bool(gps_is_synthetic and lat is not None and lon is not None),
    )


def row_to_overlap_record(
    row,
    *,
    gps: HybridGps | None = None,
    gps_is_synthetic: bool = False,
) -> OverlapRecord:
    if isinstance(row, Project):
        return project_to_overlap_record(row, gps=gps, gps_is_synthetic=gps_is_synthetic)
    (
        p_id,
        internal_id,
        source_work,
        work_desc,
        category,
        constituency_raw,
        state,
        amount,
        recommended_date,
        city_raw,
        ward_raw,
        block_raw,
        village_raw,
        is_synthetic,
    ) = row
    constituency, usable, kind, _reason = constituency_fields(constituency_raw)
    city = (city_raw or "").strip()
    ward = (ward_raw or "").strip()
    block = (block_raw or "").strip()
    village = (village_raw or "").strip()
    description = (work_desc or "").strip()
    source = preserve_source_text(source_work) or description
    lat = gps.latitude if gps is not None else None
    lon = gps.longitude if gps is not None else None
    return OverlapRecord(
        project_id=p_id,
        internal_project_id=_intern(internal_id),
        source_work=source,
        work_description=description,
        embedding_text=embedding_text(description),
        category=_intern(category),
        constituency=_intern(constituency),
        constituency_usable=usable,
        constituency_kind=_intern(kind),
        state=_intern(state),
        allocation_amount=int(amount) if amount is not None else None,
        recommended_date=recommended_date,
        city=_intern(city),
        ward=_intern(ward),
        block=_intern(block),
        village=_intern(village),
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
    subject: OverlapRecord | None = None,
    constituency: str | None = None,
    category: str | None = None,
    state: str | None = None,
    recommended_date: date | None = None,
) -> tuple[OverlapRecord, ...]:
    gps_map = gps_by_id or {}
    gps_ids = tuple(gps_map.keys()) if (mode == OverlapMode.HYBRID_TEST and gps_map) else ()

    const_val = constituency or (subject.constituency if subject and subject.constituency_usable else None)
    rec_date = recommended_date or (subject.recommended_date if subject else None)

    scope_parts: list[str] = []
    if const_val and const_val.strip():
        scope_parts.append(f"const:{const_val.strip().lower()}")
    elif subject and not subject.constituency_usable and subject.category:
        scope_parts.append(f"cat:{subject.category.strip().lower()}")
    elif category and category.strip():
        scope_parts.append(f"cat:{category.strip().lower()}")
    if rec_date is not None:
        scope_parts.append(f"date:{rec_date.isoformat()}")
    scope = "|".join(scope_parts) or "all"

    key = (*_cache_key(session, mode), str(subject_is_synthetic), scope)
    cached = _RECORD_CACHE.get(key)
    if cached is not None:
        return cached

    stmt = select(*PROJECT_OVERLAP_COLUMNS).where(Project.is_synthetic == subject_is_synthetic)

    if const_val and const_val.strip():
        norm_const = const_val.strip().lower()
        geo_filter = func.lower(func.trim(Project.constituency)) == norm_const
        if gps_ids:
            geo_filter = or_(geo_filter, Project.internal_project_id.in_(gps_ids))
        stmt = stmt.where(geo_filter)
    elif subject and not subject.constituency_usable:
        non_geo_conditions = []
        if subject.category and subject.category.strip():
            non_geo_conditions.append(func.lower(func.trim(Project.category)) == subject.category.strip().lower())
        if subject.state and subject.state.strip():
            non_geo_conditions.append(func.lower(func.trim(Project.state)) == subject.state.strip().lower())
        if non_geo_conditions:
            cat_filter = and_(*non_geo_conditions)
            if gps_ids:
                cat_filter = or_(cat_filter, Project.internal_project_id.in_(gps_ids))
            stmt = stmt.where(cat_filter)
    elif category and category.strip():
        cat_filter = func.lower(func.trim(Project.category)) == category.strip().lower()
        if state and state.strip():
            cat_filter = and_(cat_filter, func.lower(func.trim(Project.state)) == state.strip().lower())
        if gps_ids:
            cat_filter = or_(cat_filter, Project.internal_project_id.in_(gps_ids))
        stmt = stmt.where(cat_filter)

    if rec_date is not None:
        min_date = rec_date - timedelta(days=DATE_CANDIDATE_WINDOW_DAYS)
        max_date = rec_date + timedelta(days=DATE_CANDIDATE_WINDOW_DAYS)
        stmt = stmt.where(
            or_(
                Project.recommended_date.is_(None),
                Project.recommended_date.between(min_date, max_date),
            )
        )

    rows = session.execute(stmt).all()
    records: list[OverlapRecord] = []
    if mode == OverlapMode.HYBRID_TEST:
        for row in rows:
            internal_id = row[1] if not isinstance(row, Project) else row.internal_project_id
            gps = gps_map.get(internal_id)
            if gps is None:
                continue
            records.append(row_to_overlap_record(row, gps=gps, gps_is_synthetic=True))
    else:
        for row in rows:
            records.append(row_to_overlap_record(row))
    packed = tuple(records)
    if len(_RECORD_CACHE) > 128:
        _RECORD_CACHE.clear()
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
