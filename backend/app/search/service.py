"""Paginated officer search over observed project fields plus Scheme ID."""

from __future__ import annotations

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.geo.constituency import is_geographic_constituency
from app.identity.scheme_id import (
    looks_like_scheme_id,
    matching_internal_ids_for_scheme_query,
    resolve_scheme_id,
    scheme_ids_for_projects,
)
from app.models.project import Project
from app.scope import SELECT_STATE_FIRST, current_pilot_state, resolve_data_mode
from app.search.hybrid import has_hybrid_enrichment

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
MAX_QUERY_LENGTH = 200
_IN_CHUNK = 400


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text or None


def normalize_search_query(value: str | None) -> str | None:
    """Trim, collapse whitespace, and cap length. Empty/whitespace → None."""
    if value is None:
        return None
    text = " ".join(value.split())
    if not text:
        return None
    if len(text) > MAX_QUERY_LENGTH:
        text = text[:MAX_QUERY_LENGTH]
    return text


def _in_chunks(column, values: list[object]):
    if not values:
        return None
    if len(values) <= _IN_CHUNK:
        return column.in_(values)
    parts = [
        column.in_(values[index : index + _IN_CHUNK])
        for index in range(0, len(values), _IN_CHUNK)
    ]
    return or_(*parts)


def clamp_page(page: int, page_size: int) -> tuple[int, int]:
    safe_page = max(1, page)
    safe_size = min(MAX_PAGE_SIZE, max(1, page_size))
    return safe_page, safe_size


def effective_state(
    state: str | None,
    *,
    apply_pilot_scope: bool,
) -> str | None:
    """Resolve the state used for normal search.

    Omitted state + pilot scope → current pilot (Andhra Pradesh by default).
    Explicit state always wins. Clearing state with apply_pilot_scope=false
    removes the geographic restriction.
    """
    explicit = _blank_to_none(state)
    if explicit:
        return explicit
    if apply_pilot_scope:
        return current_pilot_state()
    return None


def apply_search_filters(
    db: Session,
    stmt: Select[tuple[Project]],
    *,
    q: str | None,
    constituency: str | None,
    category: str | None,
    status: str | None,
    state: str | None,
    mp_name: str | None,
    internal_project_id: str | None,
    scheme_id: str | None = None,
    apply_pilot_scope: bool = True,
) -> tuple[Select[tuple[Project]], dict[str, object]]:
    meta: dict[str, object] = {
        "constituency_filter_applied": False,
        "ignored_non_geographic_constituency": None,
        "identifier_lookup": False,
        "effective_state": None,
    }
    q_text = normalize_search_query(q)
    scheme_text = normalize_search_query(scheme_id)
    internal_text = _blank_to_none(internal_project_id)

    state_text = effective_state(state, apply_pilot_scope=apply_pilot_scope)
    meta["effective_state"] = state_text
    if state_text:
        stmt = stmt.where(Project.state == state_text)

    if q_text:
        pattern = f"%{_escape_like(q_text.casefold())}%"
        text_clause = or_(
            func.lower(Project.internal_project_id).like(pattern, escape="\\"),
            func.lower(Project.work_description).like(pattern, escape="\\"),
            func.lower(Project.mp_name).like(pattern, escape="\\"),
        )
        scheme_internal_ids = matching_internal_ids_for_scheme_query(
            db, q_text, state=state_text
        )
        if looks_like_scheme_id(q_text):
            resolved = resolve_scheme_id(db, q_text)
            if resolved is not None:
                scheme_internal_ids.append(resolved.internal_project_id)
                meta["identifier_lookup"] = True
        scheme_clause = _in_chunks(
            Project.internal_project_id, list(dict.fromkeys(scheme_internal_ids))
        )
        if scheme_clause is not None:
            stmt = stmt.where(or_(text_clause, scheme_clause))
        else:
            stmt = stmt.where(text_clause)

    if scheme_text:
        resolved = resolve_scheme_id(db, scheme_text)
        if resolved is not None:
            stmt = stmt.where(Project.id == resolved.id)
            meta["identifier_lookup"] = True
        else:
            matched = matching_internal_ids_for_scheme_query(
                db, scheme_text, state=state_text
            )
            scheme_clause = _in_chunks(Project.internal_project_id, matched)
            if scheme_clause is not None:
                stmt = stmt.where(scheme_clause)
            else:
                stmt = stmt.where(Project.id == -1)

    if internal_text:
        stmt = stmt.where(Project.internal_project_id == internal_text)
        meta["identifier_lookup"] = True

    constituency_text = _blank_to_none(constituency)
    if constituency_text:
        if is_geographic_constituency(constituency_text):
            stmt = stmt.where(Project.constituency == constituency_text)
            meta["constituency_filter_applied"] = True
        else:
            meta["ignored_non_geographic_constituency"] = constituency_text

    category_text = _blank_to_none(category)
    if category_text:
        stmt = stmt.where(Project.category == category_text)
    status_text = _blank_to_none(status)
    if status_text:
        stmt = stmt.where(Project.status == status_text)

    mp_text = normalize_search_query(mp_name)
    if mp_text:
        pattern = f"%{_escape_like(mp_text.casefold())}%"
        stmt = stmt.where(func.lower(Project.mp_name).like(pattern, escape="\\"))
    return stmt, meta


def search_projects(
    db: Session,
    *,
    q: str | None = None,
    constituency: str | None = None,
    category: str | None = None,
    status: str | None = None,
    state: str | None = None,
    mp_name: str | None = None,
    internal_project_id: str | None = None,
    scheme_id: str | None = None,
    apply_pilot_scope: bool = True,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> tuple[list[Project], int, int, int, dict[str, object]]:
    page, page_size = clamp_page(page, page_size)
    filtered, meta = apply_search_filters(
        db,
        select(Project),
        q=q,
        constituency=constituency,
        category=category,
        status=status,
        state=state,
        mp_name=mp_name,
        internal_project_id=internal_project_id,
        scheme_id=scheme_id,
        apply_pilot_scope=apply_pilot_scope,
    )
    total = db.scalar(select(func.count()).select_from(filtered.subquery())) or 0
    offset = (page - 1) * page_size
    rows = list(
        db.scalars(
            filtered.order_by(
                Project.recommended_date.desc(),
                Project.id.desc(),
            )
            .offset(offset)
            .limit(page_size)
        ).all()
    )
    return rows, int(total), page, page_size, meta


def item_data_mode(row: Project, requested_mode: str) -> str:
    if requested_mode == "HYBRID" and has_hybrid_enrichment(row.internal_project_id):
        return "HYBRID"
    return "REAL"


def search_item_payload(db: Session, row: Project, requested_mode: str) -> dict[str, object]:
    scheme_map = scheme_ids_for_projects(db, [row.internal_project_id])
    data_mode = item_data_mode(row, requested_mode)
    return {
        "id": row.id,
        "scheme_id": scheme_map.get(row.internal_project_id),
        "internal_project_id": row.internal_project_id,
        "work_description": row.work_description,
        "constituency": row.constituency,
        "category": row.category,
        "status": row.status,
        "state": row.state,
        "mp_name": row.mp_name,
        "allocation_amount": row.allocation_amount,
        "recommended_date": row.recommended_date,
        "has_hybrid_enrichment": has_hybrid_enrichment(row.internal_project_id),
        "data_mode": data_mode,
        "is_synthetic": row.is_synthetic,
        "synthetic_label": row.synthetic_label,
    }


def search_items_payload(
    db: Session,
    rows: list[Project],
    requested_mode: str,
) -> list[dict[str, object]]:
    scheme_map = scheme_ids_for_projects(db, [row.internal_project_id for row in rows])
    items: list[dict[str, object]] = []
    for row in rows:
        data_mode = item_data_mode(row, requested_mode)
        items.append(
            {
                "id": row.id,
                "scheme_id": scheme_map.get(row.internal_project_id),
                "internal_project_id": row.internal_project_id,
                "work_description": row.work_description,
                "constituency": row.constituency,
                "category": row.category,
                "status": row.status,
                "state": row.state,
                "mp_name": row.mp_name,
                "allocation_amount": row.allocation_amount,
                "recommended_date": row.recommended_date,
                "has_hybrid_enrichment": has_hybrid_enrichment(row.internal_project_id),
                "data_mode": data_mode,
                "is_synthetic": row.is_synthetic,
                "synthetic_label": row.synthetic_label,
            }
        )
    return items


def _distinct_values(db: Session, column: object, state: str | None) -> list[str]:
    stmt = select(column).where(column.is_not(None)).where(column != "")
    if state:
        stmt = stmt.where(Project.state == state)
    rows = db.scalars(stmt.distinct().order_by(column)).all()
    return [str(item) for item in rows if str(item).strip()]


def list_search_options(db: Session, state: str | None = None) -> dict[str, object]:
    """State-dependent options. Constituencies require a selected state."""
    selected = _blank_to_none(state)
    states = _distinct_values(db, Project.state, None)
    if selected is None:
        return {
            "states": states,
            "constituencies": [],
            "excluded_non_geographic_constituencies": [],
            "categories": [],
            "statuses": [],
            "constituency_enabled": False,
            "constituency_placeholder": SELECT_STATE_FIRST,
            "selected_state": None,
        }

    observed = _distinct_values(db, Project.constituency, selected)
    geographic = [item for item in observed if is_geographic_constituency(item)]
    excluded = [item for item in observed if not is_geographic_constituency(item)]
    return {
        "states": states,
        "constituencies": geographic,
        "excluded_non_geographic_constituencies": excluded,
        "categories": _distinct_values(db, Project.category, selected),
        "statuses": _distinct_values(db, Project.status, selected),
        "constituency_enabled": True,
        "constituency_placeholder": None,
        "selected_state": selected,
    }


def requested_search_mode(mode: str | None) -> str:
    return resolve_data_mode(mode)
