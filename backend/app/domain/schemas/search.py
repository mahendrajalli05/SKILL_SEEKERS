from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.scope import SCHEME_ID_NOTE, current_pilot_label
from app.search.availability import SEARCH_NOTE


class UnavailableFieldRead(BaseModel):
    field: str
    status: str
    reason: str
    display: str | None = None


class ProjectSearchItem(BaseModel):
    """Compact officer search row. Does not invent unavailable government fields."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    scheme_id: str | None = None
    internal_project_id: str
    work_description: str | None = None
    constituency: str | None = None
    category: str | None = None
    status: str | None = None
    state: str | None = None
    mp_name: str | None = None
    allocation_amount: int | None = None
    recommended_date: date | None = None
    has_hybrid_enrichment: bool = False
    data_mode: str = "REAL"
    is_synthetic: bool = False
    synthetic_label: str | None = None


class ProjectSearchResponse(BaseModel):
    items: list[ProjectSearchItem] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
    q: str | None = None
    constituency: str | None = None
    category: str | None = None
    status: str | None = None
    state: str | None = None
    mp_name: str | None = None
    internal_project_id: str | None = None
    scheme_id: str | None = None
    apply_pilot_scope: bool = True
    effective_state: str | None = None
    data_mode: str = "HYBRID"
    pilot_label: str = Field(default_factory=current_pilot_label)
    constituency_filter_applied: bool = False
    ignored_non_geographic_constituency: str | None = None
    scheme_id_note: str = SCHEME_ID_NOTE
    note: str = SEARCH_NOTE


class ProjectSearchOptionsResponse(BaseModel):
    constituencies: list[str] = Field(default_factory=list)
    excluded_non_geographic_constituencies: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    statuses: list[str] = Field(default_factory=list)
    states: list[str] = Field(default_factory=list)
    constituency_enabled: bool = False
    constituency_placeholder: str | None = None
    selected_state: str | None = None
    pilot_label: str = Field(default_factory=current_pilot_label)
    note: str = (
        "State must be selected before constituency. Constituency values are "
        "distinct observed geographic labels for that state. Chamber labels "
        "such as Sitting Rajya Sabha are excluded from geographic filtering. "
        "District, vendor, expenditure, GPS, sanction date, and completion date "
        "are not available as filters."
    )


class ApplicationScopeResponse(BaseModel):
    current_pilot: str
    pilot_label: str
    default_state: str
    default_data_mode: str
    scope_configurable: bool = True
    database_retains_all_states: bool = True
    note: str
