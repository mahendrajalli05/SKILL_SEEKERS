from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.domain.enums import DataMode
from app.engines.need.constants import GOVERNANCE_NOTE, WEIGHT_NOTE


def _reject_forbidden(value: object) -> object:
    if isinstance(value, str):
        folded = value.casefold()
        for term in ("fraud", "sanction approved", "sanction denied"):
            if term in folded:
                raise ValueError("Need & Impact must not claim fraud or output a sanction decision.")
    return value


class NeedImpactRankRequest(BaseModel):
    project_ids: list[int] = Field(min_length=1)
    available_budget: int | float | None = None
    available_budget_crore: float | None = None
    data_mode: str | None = None

    @field_validator("project_ids")
    @classmethod
    def ids_must_be_positive(cls, value: list[int]) -> list[int]:
        cleaned = [int(item) for item in value]
        if any(item <= 0 for item in cleaned):
            raise ValueError("project_ids must be positive integers.")
        return cleaned


class NeedImpactRead(BaseModel):
    project_id: int
    internal_project_id: str
    data_mode: DataMode | str
    constituency: str
    category: str
    work_description: str
    requested_amount: int | None = None
    lifecycle_stage: str
    status: str
    need_score: float | None = None
    impact_score: float | None = None
    urgency_score: float | None = None
    priority_score: float | None = None
    priority_class: str
    evidence_confidence: float
    need: dict[str, Any]
    impact: dict[str, Any]
    urgency: dict[str, Any]
    top_reasons: list[str] = Field(default_factory=list)
    unavailable_inputs: list[str] = Field(default_factory=list)
    contextual_evidence: list[str] = Field(default_factory=list)
    explanation: str
    finding: str
    weights: dict[str, float]
    weight_note: str = WEIGHT_NOTE
    governance_note: str = GOVERNANCE_NOTE
    limitations: list[str] = Field(default_factory=list)
    constituency_context: dict[str, Any] | None = None
    enrichment_used: bool = False
    enrichment_label: str | None = None
    automatic_sanction: bool = False
    sanction_decision: None = None
    evidence_ids: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    engine_version: str
    engine_name: str = "need"
    priority_recommendation_only: bool = True
    planning_simulation: bool = False

    @field_validator("explanation", "finding", "priority_class", "governance_note")
    @classmethod
    def no_forbidden(cls, value: str) -> str:
        _reject_forbidden(value)
        return value


class NeedImpactRankRead(BaseModel):
    items: list[dict[str, Any]] = Field(default_factory=list)
    unranked: list[dict[str, Any]] = Field(default_factory=list)
    available_budget: int | None = None
    available_budget_crore: float | None = None
    remaining_budget: int | None = None
    data_mode: DataMode | str
    weight_note: str = WEIGHT_NOTE
    governance_note: str = GOVERNANCE_NOTE
    planning_simulation: bool = True
    automatic_sanction: bool = False
    sanction_decision: None = None
    explanation: str
    engine_version: str
    priority_recommendation_only: bool = True

    @field_validator("explanation", "governance_note")
    @classmethod
    def no_forbidden(cls, value: str) -> str:
        _reject_forbidden(value)
        return value
