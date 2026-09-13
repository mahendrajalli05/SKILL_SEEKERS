from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.domain.enums import DataMode
from app.engines.milestone.constants import GOVERNANCE_NOTE, NO_PAYMENT_NOTE


def _reject_forbidden(value: object) -> object:
    if isinstance(value, str):
        folded = value.casefold()
        for term in ("fraud", "funds released", "payment released", "pfms payment", "sanction approved"):
            if term in folded:
                raise ValueError(
                    "Milestone Advisor must not claim fraud or imply a payment release."
                )
    return value


class MilestoneCreate(BaseModel):
    milestone_number: int | None = None
    milestone_name: str | None = None
    description: str | None = None
    planned_amount: float | None = None
    target_date: str | None = None
    completion_claimed: bool | None = None
    claimed_progress: float | None = None
    claimed_expenditure: float | None = None
    status: str | None = None
    data_mode: str | None = None
    claim_id: int | None = None
    document_ids: list[int] = Field(default_factory=list)
    photo_ids: list[int] = Field(default_factory=list)
    synthetic: bool | None = None
    from_enrichment: bool | None = None
    actor_role: str | None = None

    @field_validator("milestone_name", "description")
    @classmethod
    def no_forbidden_text(cls, value: str | None) -> str | None:
        _reject_forbidden(value)
        return value


class MilestoneDecisionCreate(BaseModel):
    action: str
    reason: str | None = None
    actor_role: str = "officer"
    data_mode: str | None = None

    @field_validator("action", "reason")
    @classmethod
    def no_forbidden(cls, value: str | None) -> str | None:
        _reject_forbidden(value)
        return value


class MilestoneRead(BaseModel):
    milestone_id: int
    project_id: int
    internal_project_id: str
    milestone_number: int | None = None
    milestone_name: str | None = None
    description: str | None = None
    planned_amount: float | None = None
    cumulative_amount: float | None = None
    remaining_planned_amount: float | None = None
    target_date: str | None = None
    completion_claimed: bool | None = None
    claimed_progress: float | None = None
    claimed_expenditure: float | None = None
    status: str
    data_mode: DataMode | str
    synthetic: bool = False
    provenance: dict[str, Any] = Field(default_factory=dict)
    claim_id: int | None = None
    document_ids: list[int] = Field(default_factory=list)
    photo_ids: list[int] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    recommendation: str | None = None
    evidence_status: str | None = None
    amounts: dict[str, Any] | None = None
    progress: dict[str, Any] | None = None
    assessment: dict[str, Any] | None = None
    officer_action: str | None = None
    officer_reason: str | None = None
    officer_actor_role: str | None = None
    officer_acted_at: str | None = None
    decisions: list[dict[str, Any]] = Field(default_factory=list)
    work_description: str | None = None
    investigation_priority: int | None = None
    evidence_confidence: int | None = None
    hybrid_notice: str | None = None
    enrichment_used: bool = False
    funds_released: bool = False
    payment_executed: bool = False
    automatic_sanction: bool = False
    pfms_integrated: bool = False
    engine_version: str
    engine_name: str = "milestone"
    governance_note: str = GOVERNANCE_NOTE
    no_payment_note: str = NO_PAYMENT_NOTE

    @field_validator("recommendation", "officer_action", "governance_note")
    @classmethod
    def no_forbidden(cls, value: str | None) -> str | None:
        _reject_forbidden(value)
        return value


class ProjectMilestonesRead(BaseModel):
    project_id: int
    internal_project_id: str
    work_description: str | None = None
    data_mode: DataMode | str
    current_milestone_id: int | None = None
    current_milestone_name: str | None = None
    current_recommendation: str | None = None
    current_milestone: dict[str, Any] | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    investigation_priority: int | None = None
    evidence_confidence: int | None = None
    hybrid_notice: str | None = None
    enrichment_used: bool = False
    funds_released: bool = False
    payment_executed: bool = False
    automatic_sanction: bool = False
    pfms_integrated: bool = False
    engine_version: str
    engine_name: str = "milestone"
    governance_note: str = GOVERNANCE_NOTE
    no_payment_note: str = NO_PAYMENT_NOTE
    allowed_officer_actions: list[str] = Field(default_factory=list)
    disallowed: list[str] = Field(default_factory=list)

    @field_validator("current_recommendation", "governance_note")
    @classmethod
    def no_forbidden(cls, value: str | None) -> str | None:
        _reject_forbidden(value)
        return value
