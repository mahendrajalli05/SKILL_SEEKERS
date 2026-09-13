from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, model_validator

from app.domain.enums import LifecycleStage


class ProjectRead(BaseModel):
    """API shape for a master work loaded from the cleaned extract."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    internal_project_id: str
    internal_id_kind: str
    internal_id_scheme: str
    source_dataset: str | None = None
    source_first_row_number: int | None = None
    source_duplicate_count: int | None = None
    source_mp_name: str | None = None
    source_work: str | None = None
    source_category: str | None = None
    source_state: str | None = None
    source_constituency: str | None = None
    source_ida: str | None = None
    source_city: str | None = None
    source_ward: str | None = None
    source_block: str | None = None
    source_village: str | None = None
    source_recommended_date: str | None = None
    source_allocation_amount: str | None = None
    source_ida_approval: str | None = None
    source_status: str | None = None
    source_house: str | None = None
    mp_name: str | None = None
    work_description: str | None = None
    category: str | None = None
    state: str | None = None
    constituency: str | None = None
    ida: str | None = None
    city: str | None = None
    ward: str | None = None
    block: str | None = None
    village: str | None = None
    recommended_date: date | None = None
    allocation_amount: int | None = None
    ida_approval: str | None = None
    status: str | None = None
    house: str | None = None
    lifecycle_stage: LifecycleStage = LifecycleStage.UNKNOWN
    snapshot_id: int | None = None
    is_synthetic: bool = False
    synthetic_label: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @model_validator(mode="after")
    def synthetic_must_be_labelled(self) -> ProjectRead:
        if self.is_synthetic and not self.synthetic_label:
            raise ValueError("Synthetic rows must include synthetic_label.")
        return self
