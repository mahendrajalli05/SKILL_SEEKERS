from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain.schemas.project_detail import ProjectDetailRead, SyntheticEnrichmentRead
from app.domain.schemas.search import (
    ApplicationScopeResponse,
    ProjectSearchItem,
    ProjectSearchOptionsResponse,
    ProjectSearchResponse,
    UnavailableFieldRead,
)
from app.errors import AppError
from app.identity.scheme_id import scheme_id_for_project
from app.models.project import Project
from app.scope import (
    SCHEME_ID_NOTE,
    application_scope_payload,
    current_pilot_label,
    default_data_mode,
    resolve_data_mode,
)
from app.search.availability import (
    HYBRID_ENRICHMENT_NOTICE,
    PROVENANCE_AMOUNT_NOTE,
    REAL_DATA_NOTICE,
    SEARCH_NOTE,
    UNAVAILABLE_REAL_FIELDS,
)
from app.search.enrichment_display import enrichment_for
from app.search.hybrid import has_hybrid_enrichment
from app.search.service import (
    DEFAULT_PAGE_SIZE,
    list_search_options,
    search_items_payload,
    search_projects,
)

router = APIRouter()


def _synthetic_payload(internal_project_id: str, data_mode: str) -> SyntheticEnrichmentRead | None:
    if data_mode != "HYBRID":
        return None
    row = enrichment_for(internal_project_id)
    if row is None:
        return None
    return SyntheticEnrichmentRead.model_validate(row.as_payload())


def detail_from_project(db: Session, row: Project, data_mode: str) -> ProjectDetailRead:
    snapshot = row.snapshot
    hybrid = has_hybrid_enrichment(row.internal_project_id)
    identity = ProjectDetailRead.model_validate(row)
    notice = None
    if data_mode == "HYBRID" and hybrid:
        notice = HYBRID_ENRICHMENT_NOTICE
    elif data_mode == "REAL":
        notice = REAL_DATA_NOTICE
    return identity.model_copy(
        update={
            "scheme_id": scheme_id_for_project(db, row),
            "scheme_id_note": SCHEME_ID_NOTE,
            "has_hybrid_enrichment": hybrid,
            "hybrid_notice": notice,
            "amount_unit_note": PROVENANCE_AMOUNT_NOTE,
            "unavailable_fields": [
                UnavailableFieldRead.model_validate(item) for item in UNAVAILABLE_REAL_FIELDS
            ],
            "snapshot_source_url": snapshot.source_url if snapshot else None,
            "snapshot_extracted_at": (
                snapshot.extracted_at.isoformat() if snapshot and snapshot.extracted_at else None
            ),
            "snapshot_download_date": snapshot.download_date if snapshot else None,
            "snapshot_publisher": snapshot.publisher if snapshot else None,
            "snapshot_notes": snapshot.notes if snapshot else None,
            "snapshot_original_filename": snapshot.original_filename if snapshot else None,
            "data_mode_default": default_data_mode(),
            "data_mode": data_mode,
            "synthetic_enrichment": _synthetic_payload(row.internal_project_id, data_mode),
        }
    )


@router.get("/scope", response_model=ApplicationScopeResponse)
def application_scope() -> ApplicationScopeResponse:
    return ApplicationScopeResponse.model_validate(application_scope_payload())


@router.get("/projects/options", response_model=ProjectSearchOptionsResponse)
def project_search_options(
    db: Session = Depends(get_db),
    state: str | None = Query(default=None),
) -> ProjectSearchOptionsResponse:
    options = list_search_options(db, state=state)
    return ProjectSearchOptionsResponse(
        **options,
        pilot_label=current_pilot_label(),
    )


@router.get("/projects", response_model=ProjectSearchResponse)
def list_projects(
    db: Session = Depends(get_db),
    q: str | None = Query(
        default=None,
        description="Text search over Scheme ID, internal project ID, work description, and MP name.",
    ),
    constituency: str | None = Query(default=None),
    category: str | None = Query(default=None),
    status: str | None = Query(default=None),
    state: str | None = Query(default=None),
    mp_name: str | None = Query(default=None),
    internal_project_id: str | None = Query(default=None),
    scheme_id: str | None = Query(default=None),
    apply_pilot_scope: bool = Query(default=True),
    mode: str | None = Query(default=None, description="REAL or HYBRID. Default is HYBRID DEMO."),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=100),
) -> ProjectSearchResponse:
    data_mode = resolve_data_mode(mode)
    rows, total, page, page_size, meta = search_projects(
        db,
        q=q,
        constituency=constituency,
        category=category,
        status=status,
        state=state,
        mp_name=mp_name,
        internal_project_id=internal_project_id,
        scheme_id=scheme_id,
        apply_pilot_scope=apply_pilot_scope,
        page=page,
        page_size=page_size,
    )
    return ProjectSearchResponse(
        items=[
            ProjectSearchItem.model_validate(item)
            for item in search_items_payload(db, rows, data_mode)
        ],
        total=total,
        page=page,
        page_size=page_size,
        q=q,
        constituency=constituency,
        category=category,
        status=status,
        state=state,
        mp_name=mp_name,
        internal_project_id=internal_project_id,
        scheme_id=scheme_id,
        apply_pilot_scope=apply_pilot_scope,
        effective_state=str(meta["effective_state"]) if meta.get("effective_state") else None,
        data_mode=data_mode,
        pilot_label=current_pilot_label(),
        constituency_filter_applied=bool(meta.get("constituency_filter_applied")),
        ignored_non_geographic_constituency=(
            str(meta["ignored_non_geographic_constituency"])
            if meta.get("ignored_non_geographic_constituency")
            else None
        ),
        scheme_id_note=SCHEME_ID_NOTE,
        note=SEARCH_NOTE,
    )


@router.get("/projects/{project_id}", response_model=ProjectDetailRead)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    mode: str | None = Query(default=None, description="REAL or HYBRID. Default is HYBRID DEMO."),
) -> ProjectDetailRead:
    row = db.get(Project, project_id)
    if row is None:
        raise AppError("Project not found.", code="not_found", status_code=404)
    return detail_from_project(db, row, resolve_data_mode(mode))
