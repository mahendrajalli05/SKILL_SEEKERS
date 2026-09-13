from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.demo.constants import DEMO_NOTICE, GOVERNANCE_NOTE, LAYER_VERSION


class DemoCaseListItem(BaseModel):
    case_id: str
    display_name: str
    purpose: str
    short_description: str
    expected_lifecycle: str
    expected_direction: str
    internal_project_id: str
    suggested_questions: list[str] = Field(default_factory=list)
    demo_notice: str = DEMO_NOTICE
    available: bool
    project_id: int | None = None
    scheme_id: str | None = None
    lifecycle_state: str | None = None
    source_status: str | None = None
    work_description: str | None = None
    constituency: str | None = None
    href: str


class DemoCaseListResponse(BaseModel):
    items: list[DemoCaseListItem]
    count: int
    demo_notice: str = DEMO_NOTICE
    hybrid_notice: str
    governance_note: str = GOVERNANCE_NOTE
    journey_steps: list[str] = Field(default_factory=list)
    engine_version: str = LAYER_VERSION
    fusion_v2_unchanged: bool = True
    automatic_sanction: bool = False
    automatic_payment: bool = False
    fraud_conclusion: bool = False
    data_mode: str = "HYBRID"
    fixture_layer: str | None = None
    fixture_notice: str | None = None


class DemoCaseResponse(BaseModel):
    """Assembled controlled demonstration case. Not an intelligence score."""

    model_config = ConfigDict(extra="allow")

    case_id: str
    display_name: str
    purpose: str
    scenario_type: str
    short_description: str
    initial_claim: str
    expected_lifecycle: str
    expected_direction: str
    expected_direction_note: str
    suggested_questions: list[str] = Field(default_factory=list)
    officer_actions: list[str] = Field(default_factory=list)
    officer_action_labels: list[str] = Field(default_factory=list)
    investigation_actions: list[str] = Field(default_factory=list)
    modules: list[str] = Field(default_factory=list)
    project_id: int
    scheme_id: str | None = None
    internal_project_id: str
    work_description: str | None = None
    constituency: str | None = None
    category: str | None = None
    state: str | None = None
    source_status: str | None = None
    lifecycle_state: str | None = None
    current_stage: str | None = None
    allocation_amount: int | None = None
    data_mode: str
    data_reliability: str
    has_hybrid_enrichment: bool = False
    is_synthetic: bool = False
    synthetic_label: str | None = None
    demo_notice: str = DEMO_NOTICE
    hybrid_notice: str | None = None
    governance_note: str = GOVERNANCE_NOTE
    no_fraud_note: str | None = None
    no_sanction_note: str | None = None
    available_plan: dict[str, Any] = Field(default_factory=dict)
    available_claim: dict[str, Any] = Field(default_factory=dict)
    available_evidence: dict[str, Any] = Field(default_factory=dict)
    intelligence_signals: list[dict[str, Any]] = Field(default_factory=list)
    risk_fusion_v2: dict[str, Any] = Field(default_factory=dict)
    investigation_workspace: dict[str, Any] = Field(default_factory=dict)
    lifecycle: dict[str, Any] = Field(default_factory=dict)
    pce: dict[str, Any] | None = None
    images: dict[str, Any] | None = None
    documents: dict[str, Any] | None = None
    geospatial: dict[str, Any] | None = None
    satellite: dict[str, Any] | None = None
    citizen: dict[str, Any] | None = None
    milestone: dict[str, Any] | None = None
    compliance: dict[str, Any] | None = None
    need_impact: dict[str, Any] | None = None
    copilot: dict[str, Any] = Field(default_factory=dict)
    recommended_action: str | None = None
    officer_decision: str | None = None
    officer_decisions: list[dict[str, Any]] = Field(default_factory=list)
    checkpoint_actions: list[str] = Field(default_factory=list)
    journey: list[dict[str, Any]] = Field(default_factory=list)
    final_case_summary: dict[str, Any] = Field(default_factory=dict)
    automatic_sanction: bool = False
    automatic_payment: bool = False
    pfms_integrated: bool = False
    fraud_conclusion: bool = False
    engine_version: str = LAYER_VERSION
    fusion_v2_unchanged: bool = True
