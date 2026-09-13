from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import DataMode
from app.engines.lifecycle.types import LifecycleResult


class TimelineNodeRead(BaseModel):
    stage: str
    status: str
    label: str
    available: bool
    href: str | None = None
    note: str | None = None


class LifecyclePlanningDecisionCreate(BaseModel):
    action: str
    reason: str | None = None
    actor_role: str | None = "officer"


class LifecyclePlanningDecisionRead(BaseModel):
    id: int
    project_id: int
    action: str
    resulting_state: str
    reason: str | None = None
    actor_role: str | None = None
    scores_unchanged: bool = True
    automatic_sanction: bool = False
    automatic_payment: bool = False
    note: str


class ProjectLifecycleResponse(BaseModel):
    """Orchestrated FUTURE / ONGOING / COMPLETED workflow. Not a sanction."""

    model_config = ConfigDict(from_attributes=True)

    project_id: int
    internal_project_id: str
    scheme_id: str | None = None
    work_description: str | None = None
    constituency: str | None = None
    category: str | None = None
    requested_amount: int | None = None
    data_mode: DataMode
    lifecycle_state: str
    source_status: str | None = None
    current_stage: str
    planning_state: str | None = None
    completed_stages: list[str] = Field(default_factory=list)
    pending_stages: list[str] = Field(default_factory=list)
    timeline: list[TimelineNodeRead] = Field(default_factory=list)
    evidence_summary: dict[str, Any] = Field(default_factory=dict)
    risk_summary: dict[str, Any] | None = None
    milestone_summary: dict[str, Any] | None = None
    need_impact_summary: dict[str, Any] | None = None
    pce_summary: dict[str, Any] | None = None
    citizen_summary: dict[str, Any] | None = None
    geospatial_status: dict[str, Any] | None = None
    satellite_status: dict[str, Any] | None = None
    document_status: dict[str, Any] | None = None
    image_status: dict[str, Any] | None = None
    compliance_status: dict[str, Any] | None = None
    relationship_status: dict[str, Any] | None = None
    project_status_summary: dict[str, Any] = Field(default_factory=dict)
    officer_decisions: list[dict[str, Any]] = Field(default_factory=list)
    checkpoint_actions: list[str] = Field(default_factory=list)
    final_case_summary: dict[str, Any] | None = None
    recommendation: str | None = None
    recommendation_rationale: str | None = None
    unavailable_inputs: list[str] = Field(default_factory=list)
    automatic_sanction: bool = False
    automatic_payment: bool = False
    pfms_integrated: bool = False
    fraud_conclusion: bool = False
    engine_version: str = "lifecycle-orchestration-v1"
    governance_note: str = (
        "SARVSAKSHI workflow state is an application lifecycle label. "
        "It is not an official MPLADS status. Source status is the observed extract STATUS. "
        "AI recommends. Authorized officers decide. "
        "This layer does not sanction a project, release funds, or determine fraud."
    )
    workflow_label: str = "SARVSAKSHI workflow state"
    source_status_label: str = "Source status"
    is_synthetic: bool = False
    synthetic_label: str | None = None
    explanation: str = ""

    @classmethod
    def from_result(cls, result: LifecycleResult) -> "ProjectLifecycleResponse":
        return cls.model_validate(result.as_dict())
