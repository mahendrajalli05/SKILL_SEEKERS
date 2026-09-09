from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, model_validator

from app.domain.enums import AmountRole, LifecycleStage


class ProjectRead(BaseModel):
    """API shape for a master work. All government fields remain optional until profiled."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    unique_work_number: str | None = None
    work_name: str | None = None
    work_description: str | None = None
    work_category: str | None = None
    state: str | None = None
    implementing_district: str | None = None
    constituency: str | None = None
    house_name: str | None = None
    mp_name: str | None = None
    agency_name_raw: str | None = None
    village_or_place: str | None = None
    amount: float | None = None
    amount_role: AmountRole | None = None
    amount_unit: str | None = None
    recommended_amount: float | None = None
    sanctioned_amount: float | None = None
    utilised_amount: float | None = None
    recommendation_date: date | None = None
    sanction_date: date | None = None
    date_of_completion: date | None = None
    work_status: str | None = None
    lifecycle_stage: LifecycleStage = LifecycleStage.UNKNOWN
    image_uploaded: str | None = None
    image_status: str | None = None
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
