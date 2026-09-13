"""Typed payloads for End-to-End Lifecycle Orchestration V1."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain.enums import DataMode, LifecycleStage
from app.engines.lifecycle.constants import ENGINE_VERSION, GOVERNANCE_NOTE


@dataclass
class TimelineNode:
    stage: str
    status: str
    label: str
    available: bool
    href: str | None = None
    note: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "status": self.status,
            "label": self.label,
            "available": self.available,
            "href": self.href,
            "note": self.note,
        }


@dataclass
class ModuleStatus:
    module: str
    available: bool
    status: str | None
    summary: str | None
    href: str | None = None
    evidence_ids: list[str] = field(default_factory=list)
    data_mode: str | None = None

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "module": self.module,
            "available": self.available,
            "status": self.status,
            "summary": self.summary,
        }
        if self.href:
            payload["href"] = self.href
        if self.evidence_ids:
            payload["evidence_ids"] = list(self.evidence_ids)
        if self.data_mode:
            payload["data_mode"] = self.data_mode
        return payload


@dataclass
class LifecycleFacts:
    """Observed facts used to derive the workflow. No invented government fields."""

    lifecycle_state: str
    source_status: str | None
    planning_state: str
    data_mode: DataMode
    has_need: bool = False
    need_priority_class: str | None = None
    need_inconclusive: bool = False
    has_plan: bool = False
    has_claim: bool = False
    has_pce_evidence: bool = False
    pce_result: str | None = None
    milestone_count: int = 0
    latest_milestone_status: str | None = None
    latest_milestone_officer_action: str | None = None
    latest_milestone_recommendation: str | None = None
    has_officer_investigation_decision: bool = False
    last_investigation_decision: str | None = None
    risk_appropriate: bool = False
    risk_insufficient: bool = False
    risk_explanation_type: str | None = None
    has_documents: bool = False
    has_images: bool = False
    has_geo: bool = False
    has_satellite: bool = False
    satellite_unavailable: bool = True
    has_citizen: bool = False
    has_graph: bool = False
    has_compliance: bool = False
    completed_insufficient: bool = False


@dataclass
class LifecycleResult:
    project_id: int
    internal_project_id: str
    scheme_id: str | None
    work_description: str | None
    constituency: str | None
    category: str | None
    requested_amount: int | None
    data_mode: DataMode
    lifecycle_state: str
    source_status: str | None
    current_stage: str
    planning_state: str | None
    completed_stages: list[str]
    pending_stages: list[str]
    timeline: list[TimelineNode]
    evidence_summary: dict[str, Any]
    risk_summary: dict[str, Any] | None
    milestone_summary: dict[str, Any] | None
    need_impact_summary: dict[str, Any] | None
    pce_summary: dict[str, Any] | None
    citizen_summary: dict[str, Any] | None
    geospatial_status: dict[str, Any] | None
    satellite_status: dict[str, Any] | None
    document_status: dict[str, Any] | None
    image_status: dict[str, Any] | None
    compliance_status: dict[str, Any] | None
    relationship_status: dict[str, Any] | None
    project_status_summary: dict[str, Any]
    officer_decisions: list[dict[str, Any]]
    checkpoint_actions: list[str]
    final_case_summary: dict[str, Any] | None
    recommendation: str | None
    recommendation_rationale: str | None
    unavailable_inputs: list[str]
    automatic_sanction: bool = False
    automatic_payment: bool = False
    pfms_integrated: bool = False
    fraud_conclusion: bool = False
    engine_version: str = ENGINE_VERSION
    governance_note: str = GOVERNANCE_NOTE
    workflow_label: str = "SARVSAKSHI workflow state"
    source_status_label: str = "Source status"
    is_synthetic: bool = False
    synthetic_label: str | None = None
    explanation: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "internal_project_id": self.internal_project_id,
            "scheme_id": self.scheme_id,
            "work_description": self.work_description,
            "constituency": self.constituency,
            "category": self.category,
            "requested_amount": self.requested_amount,
            "data_mode": self.data_mode.value if isinstance(self.data_mode, DataMode) else str(self.data_mode),
            "lifecycle_state": self.lifecycle_state,
            "source_status": self.source_status,
            "current_stage": self.current_stage,
            "planning_state": self.planning_state,
            "completed_stages": list(self.completed_stages),
            "pending_stages": list(self.pending_stages),
            "timeline": [item.as_dict() for item in self.timeline],
            "evidence_summary": dict(self.evidence_summary),
            "risk_summary": self.risk_summary,
            "milestone_summary": self.milestone_summary,
            "need_impact_summary": self.need_impact_summary,
            "pce_summary": self.pce_summary,
            "citizen_summary": self.citizen_summary,
            "geospatial_status": self.geospatial_status,
            "satellite_status": self.satellite_status,
            "document_status": self.document_status,
            "image_status": self.image_status,
            "compliance_status": self.compliance_status,
            "relationship_status": self.relationship_status,
            "project_status_summary": dict(self.project_status_summary),
            "officer_decisions": list(self.officer_decisions),
            "checkpoint_actions": list(self.checkpoint_actions),
            "final_case_summary": self.final_case_summary,
            "recommendation": self.recommendation,
            "recommendation_rationale": self.recommendation_rationale,
            "unavailable_inputs": list(self.unavailable_inputs),
            "automatic_sanction": False,
            "automatic_payment": False,
            "pfms_integrated": False,
            "fraud_conclusion": False,
            "engine_version": self.engine_version,
            "governance_note": self.governance_note,
            "workflow_label": self.workflow_label,
            "source_status_label": self.source_status_label,
            "is_synthetic": self.is_synthetic,
            "synthetic_label": self.synthetic_label,
            "explanation": self.explanation,
        }


def parse_lifecycle_state(value: str | LifecycleStage | None) -> str:
    text = (
        value.value
        if isinstance(value, LifecycleStage)
        else str(value or "").strip().upper()
    )
    if text in {
        LifecycleStage.FUTURE.value,
        LifecycleStage.ONGOING.value,
        LifecycleStage.COMPLETED.value,
        LifecycleStage.UNKNOWN.value,
    }:
        return text
    return LifecycleStage.UNKNOWN.value
