"""Milestone Advisor V1 typed payloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain.enums import DataMode, MilestoneRecommendation
from app.engines.milestone.constants import GOVERNANCE_NOTE, HYBRID_NOTICE, NO_PAYMENT_NOTE


def _mode_value(value: DataMode | str) -> str:
    return value.value if isinstance(value, DataMode) else str(value)


@dataclass
class AmountView:
    planned_amount: float | None
    cumulative_amount: float | None
    claimed_expenditure: float | None
    remaining_planned_amount: float | None
    planned_amount_available: bool
    cumulative_amount_available: bool
    claimed_expenditure_available: bool
    remaining_available: bool
    claimed_expenditure_synthetic: bool = False
    note: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "planned_amount": self.planned_amount,
            "cumulative_amount": self.cumulative_amount,
            "claimed_expenditure": self.claimed_expenditure,
            "remaining_planned_amount": self.remaining_planned_amount,
            "planned_amount_available": self.planned_amount_available,
            "cumulative_amount_available": self.cumulative_amount_available,
            "claimed_expenditure_available": self.claimed_expenditure_available,
            "remaining_available": self.remaining_available,
            "claimed_expenditure_synthetic": self.claimed_expenditure_synthetic,
            "note": self.note,
        }


@dataclass
class ProgressView:
    claimed_progress: float | None
    evidence_supported_progress: float | None
    planned_progress: float | None
    schedule_mismatch: bool
    schedule_note: str | None
    claimed_progress_available: bool
    evidence_supported_available: bool
    planned_progress_available: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "claimed_progress": self.claimed_progress,
            "evidence_supported_progress": self.evidence_supported_progress,
            "planned_progress": self.planned_progress,
            "schedule_mismatch": self.schedule_mismatch,
            "schedule_note": self.schedule_note,
            "claimed_progress_available": self.claimed_progress_available,
            "evidence_supported_available": self.evidence_supported_available,
            "planned_progress_available": self.planned_progress_available,
        }


@dataclass
class IntelligenceSignal:
    engine: str
    signal_type: str
    disposition: str | None
    finding: str | None
    score: float | None
    flagged: bool
    data_mode: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "engine": self.engine,
            "signal_type": self.signal_type,
            "disposition": self.disposition,
            "finding": self.finding,
            "score": self.score,
            "flagged": self.flagged,
            "data_mode": self.data_mode,
        }


@dataclass
class AssessmentInputs:
    """Pure inputs for the deterministic recommendation. No DB."""

    has_claim: bool
    has_required_evidence: bool
    pce_result: str | None
    geo_mismatch: bool = False
    image_reuse: bool = False
    exact_duplicate: bool = False
    expenditure_inconsistency: bool = False
    progress_inconsistency: bool = False
    schedule_mismatch: bool = False
    cost_flagged: bool = False
    compliance_flagged: bool = False
    overlap_flagged: bool = False


@dataclass
class AssessmentResult:
    recommendation: str
    pce_result: str | None
    evidence_status: str
    supporting_evidence: list[str] = field(default_factory=list)
    conflicting_evidence: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    intelligence_signals: list[str] = field(default_factory=list)
    independent_concerns: list[str] = field(default_factory=list)
    explanation: str = ""
    evidence_confidence: float = 0.0
    funds_released: bool = False
    payment_executed: bool = False
    automatic_sanction: bool = False
    pfms_integrated: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "recommendation": self.recommendation,
            "pce_result": self.pce_result,
            "evidence_status": self.evidence_status,
            "supporting_evidence": list(self.supporting_evidence),
            "conflicting_evidence": list(self.conflicting_evidence),
            "missing_evidence": list(self.missing_evidence),
            "intelligence_signals": list(self.intelligence_signals),
            "independent_concerns": list(self.independent_concerns),
            "explanation": self.explanation,
            "evidence_confidence": self.evidence_confidence,
            "funds_released": False,
            "payment_executed": False,
            "automatic_sanction": False,
            "pfms_integrated": False,
            "governance_note": GOVERNANCE_NOTE,
            "no_payment_note": NO_PAYMENT_NOTE,
        }


@dataclass
class TimelineNode:
    slot: str
    milestone_id: int | None
    milestone_number: int | None
    milestone_name: str | None
    status: str | None
    planned_date: str | None
    claim: str | None
    evidence: str | None
    result: str | None
    officer_action: str | None
    recorded: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "slot": self.slot,
            "milestone_id": self.milestone_id,
            "milestone_number": self.milestone_number,
            "milestone_name": self.milestone_name,
            "status": self.status,
            "planned_date": self.planned_date,
            "claim": self.claim,
            "evidence": self.evidence,
            "result": self.result,
            "officer_action": self.officer_action,
            "recorded": self.recorded,
        }


@dataclass
class OfficerDecisionView:
    id: int
    milestone_id: int
    project_id: int
    action: str
    reason: str | None
    actor_role: str | None
    created_at: str | None
    investigation_priority_snapshot: int | None
    evidence_confidence_snapshot: int | None
    recommended_action_snapshot: str | None
    scores_unchanged: bool = True
    funds_released: bool = False
    payment_executed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "milestone_id": self.milestone_id,
            "project_id": self.project_id,
            "action": self.action,
            "reason": self.reason,
            "actor_role": self.actor_role,
            "created_at": self.created_at,
            "investigation_priority_snapshot": self.investigation_priority_snapshot,
            "evidence_confidence_snapshot": self.evidence_confidence_snapshot,
            "recommended_action_snapshot": self.recommended_action_snapshot,
            "scores_unchanged": self.scores_unchanged,
            "funds_released": False,
            "payment_executed": False,
            "automatic_sanction": False,
            "note": "Human officer decision. Underlying intelligence scores were not changed.",
        }


@dataclass
class MilestoneRecord:
    milestone_id: int
    project_id: int
    internal_project_id: str
    milestone_number: int | None
    milestone_name: str | None
    description: str | None
    planned_amount: float | None
    cumulative_amount: float | None
    remaining_planned_amount: float | None
    target_date: str | None
    completion_claimed: bool | None
    claimed_progress: float | None
    claimed_expenditure: float | None
    status: str
    data_mode: str
    synthetic: bool
    provenance: dict[str, Any]
    claim_id: int | None = None
    document_ids: list[int] = field(default_factory=list)
    photo_ids: list[int] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    recommendation: str | None = None
    evidence_status: str | None = None
    amounts: AmountView | None = None
    progress: ProgressView | None = None
    assessment: dict[str, Any] | None = None
    officer_action: str | None = None
    officer_reason: str | None = None
    officer_actor_role: str | None = None
    officer_acted_at: str | None = None
    decisions: list[OfficerDecisionView] = field(default_factory=list)
    work_description: str | None = None
    investigation_priority: int | None = None
    evidence_confidence: int | None = None
    hybrid_notice: str | None = None
    enrichment_used: bool = False
    funds_released: bool = False
    payment_executed: bool = False
    automatic_sanction: bool = False
    pfms_integrated: bool = False
    engine_version: str = ""
    engine_name: str = "milestone"
    governance_note: str = GOVERNANCE_NOTE

    def as_dict(self) -> dict[str, Any]:
        return {
            "milestone_id": self.milestone_id,
            "project_id": self.project_id,
            "internal_project_id": self.internal_project_id,
            "milestone_number": self.milestone_number,
            "milestone_name": self.milestone_name,
            "description": self.description,
            "planned_amount": self.planned_amount,
            "cumulative_amount": self.cumulative_amount,
            "remaining_planned_amount": self.remaining_planned_amount,
            "target_date": self.target_date,
            "completion_claimed": self.completion_claimed,
            "claimed_progress": self.claimed_progress,
            "claimed_expenditure": self.claimed_expenditure,
            "status": self.status,
            "data_mode": _mode_value(self.data_mode),
            "synthetic": self.synthetic,
            "provenance": dict(self.provenance),
            "claim_id": self.claim_id,
            "document_ids": list(self.document_ids),
            "photo_ids": list(self.photo_ids),
            "evidence_ids": list(self.evidence_ids),
            "recommendation": self.recommendation,
            "evidence_status": self.evidence_status,
            "amounts": self.amounts.as_dict() if self.amounts else None,
            "progress": self.progress.as_dict() if self.progress else None,
            "assessment": dict(self.assessment) if self.assessment else None,
            "officer_action": self.officer_action,
            "officer_reason": self.officer_reason,
            "officer_actor_role": self.officer_actor_role,
            "officer_acted_at": self.officer_acted_at,
            "decisions": [item.as_dict() for item in self.decisions],
            "work_description": self.work_description,
            "investigation_priority": self.investigation_priority,
            "evidence_confidence": self.evidence_confidence,
            "hybrid_notice": self.hybrid_notice or (
                HYBRID_NOTICE if _mode_value(self.data_mode) in {"HYBRID", "SYNTHETIC"} else None
            ),
            "enrichment_used": self.enrichment_used,
            "funds_released": False,
            "payment_executed": False,
            "automatic_sanction": False,
            "pfms_integrated": False,
            "engine_version": self.engine_version,
            "engine_name": self.engine_name,
            "governance_note": self.governance_note,
            "no_payment_note": NO_PAYMENT_NOTE,
        }


@dataclass
class ProjectMilestones:
    project_id: int
    internal_project_id: str
    work_description: str | None
    data_mode: str
    current_milestone_id: int | None
    current_milestone_name: str | None
    current_recommendation: str | None
    items: list[MilestoneRecord]
    timeline: list[TimelineNode]
    investigation_priority: int | None = None
    evidence_confidence: int | None = None
    hybrid_notice: str | None = None
    enrichment_used: bool = False
    funds_released: bool = False
    payment_executed: bool = False
    automatic_sanction: bool = False
    pfms_integrated: bool = False
    engine_version: str = ""
    engine_name: str = "milestone"
    governance_note: str = GOVERNANCE_NOTE

    def as_dict(self) -> dict[str, Any]:
        current = next(
            (item for item in self.items if item.milestone_id == self.current_milestone_id),
            None,
        )
        return {
            "project_id": self.project_id,
            "internal_project_id": self.internal_project_id,
            "work_description": self.work_description,
            "data_mode": _mode_value(self.data_mode),
            "current_milestone_id": self.current_milestone_id,
            "current_milestone_name": self.current_milestone_name,
            "current_recommendation": self.current_recommendation,
            "current_milestone": current.as_dict() if current else None,
            "items": [item.as_dict() for item in self.items],
            "timeline": [item.as_dict() for item in self.timeline],
            "investigation_priority": self.investigation_priority,
            "evidence_confidence": self.evidence_confidence,
            "hybrid_notice": self.hybrid_notice,
            "enrichment_used": self.enrichment_used,
            "funds_released": False,
            "payment_executed": False,
            "automatic_sanction": False,
            "pfms_integrated": False,
            "engine_version": self.engine_version,
            "engine_name": self.engine_name,
            "governance_note": self.governance_note,
            "no_payment_note": NO_PAYMENT_NOTE,
            "allowed_officer_actions": [
                "PROCEED",
                "HOLD",
                "INSPECT",
                "NEED_MORE_INFORMATION",
            ],
            "disallowed": [
                "payment_release",
                "pfms_payment",
                "automatic_sanction",
                "fraud_finding",
            ],
        }


# Keep recommendation enum imported for callers.
__all__ = [
    "AmountView",
    "AssessmentInputs",
    "AssessmentResult",
    "IntelligenceSignal",
    "MilestoneRecord",
    "OfficerDecisionView",
    "ProgressView",
    "ProjectMilestones",
    "TimelineNode",
    "MilestoneRecommendation",
]
