from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.schemas.project import ProjectRead
from app.domain.schemas.search import UnavailableFieldRead
from app.scope import SCHEME_ID_NOTE, default_data_mode
from app.search.availability import PROVENANCE_AMOUNT_NOTE


class SyntheticMilestonesRead(BaseModel):
    number: int | None = None
    amount: int | None = None
    total_amount: int | None = None


class SyntheticEnrichmentRead(BaseModel):
    """SYNTHETIC prototype enrichment. Never mixed into REAL mode."""

    label: str = "SYNTHETIC"
    disclaimer: str
    implementing_district: str | None = None
    implementing_agency: str | None = None
    vendor_name: str | None = None
    sanction_date: str | None = None
    start_date: str | None = None
    planned_start_date: str | None = None
    planned_completion_date: str | None = None
    completion_date: str | None = None
    actual_start_date: str | None = None
    actual_completion_date: str | None = None
    expenditure: int | None = None
    gps_latitude: float | None = None
    gps_longitude: float | None = None
    physical_progress_percent: int | None = None
    milestones: SyntheticMilestonesRead | None = None


class ProjectDetailRead(ProjectRead):
    """Project identity plus honest availability metadata. No invented government fields."""

    scheme_id: str | None = None
    scheme_id_note: str = SCHEME_ID_NOTE
    has_hybrid_enrichment: bool = False
    hybrid_notice: str | None = None
    amount_unit_note: str = PROVENANCE_AMOUNT_NOTE
    unavailable_fields: list[UnavailableFieldRead] = Field(default_factory=list)
    snapshot_source_url: str | None = None
    snapshot_extracted_at: str | None = None
    snapshot_download_date: str | None = None
    snapshot_publisher: str | None = None
    snapshot_notes: str | None = None
    snapshot_original_filename: str | None = None
    data_mode_default: str = Field(default_factory=default_data_mode)
    data_mode: str = Field(default_factory=default_data_mode)
    synthetic_enrichment: SyntheticEnrichmentRead | None = None
