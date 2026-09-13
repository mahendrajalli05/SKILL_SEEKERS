"""Deterministic SARVSAKSHI lifecycle state machine.

Does not change project.lifecycle_stage (source-derived).
Does not score intelligence. Does not sanction or release funds.
"""

from __future__ import annotations

from app.domain.enums import LifecycleStage
from app.engines.lifecycle.constants import (
    CHECKPOINT_COMPLETED,
    CHECKPOINT_FUTURE,
    CHECKPOINT_ONGOING,
    DEFERRED,
    NEEDS_MORE_INFORMATION,
    PLANNING,
    PRIORITIZED,
    STAGE_CLAIM,
    STAGE_COMPLETION,
    STAGE_EVIDENCE,
    STAGE_FINAL_INVESTIGATION,
    STAGE_FUTURE,
    STAGE_INVESTIGATION,
    STAGE_MILESTONE,
    STAGE_OFFICER_DECISION,
    STAGE_ONGOING,
    STAGE_PLAN,
    STAGE_PRIORITIZATION,
    STAGE_RISK_FUSION,
)
from app.engines.lifecycle.types import LifecycleFacts


def default_planning_state(lifecycle_state: str, stored: str | None) -> str | None:
    if lifecycle_state != LifecycleStage.FUTURE.value:
        return stored if stored else None
    if stored in {PLANNING, PRIORITIZED, DEFERRED, NEEDS_MORE_INFORMATION}:
        return stored
    return PLANNING


def risk_fusion_appropriate(lifecycle_state: str, *, has_investigation_evidence: bool) -> bool:
    if lifecycle_state in {LifecycleStage.ONGOING.value, LifecycleStage.COMPLETED.value}:
        return True
    if lifecycle_state == LifecycleStage.UNKNOWN.value and has_investigation_evidence:
        return True
    return False


def completed_evidence_insufficient(facts: LifecycleFacts) -> bool:
    if facts.lifecycle_state != LifecycleStage.COMPLETED.value:
        return False
    supporting = (
        facts.has_pce_evidence
        or facts.has_documents
        or facts.has_images
        or facts.has_citizen
        or facts.has_geo
        or (facts.has_plan and facts.has_claim)
    )
    if facts.risk_insufficient and not supporting:
        return True
    if not supporting and facts.pce_result in {None, "INCONCLUSIVE"}:
        return True
    return False


def derive_current_stage(facts: LifecycleFacts) -> str:
    state = facts.lifecycle_state
    if state == LifecycleStage.UNKNOWN.value:
        if facts.has_officer_investigation_decision:
            return STAGE_OFFICER_DECISION
        if facts.risk_appropriate:
            return STAGE_INVESTIGATION
        return LifecycleStage.UNKNOWN.value
    if state == LifecycleStage.FUTURE.value:
        return STAGE_PRIORITIZATION
    if state == LifecycleStage.COMPLETED.value:
        if facts.completed_insufficient:
            return STAGE_FINAL_INVESTIGATION
        if facts.has_officer_investigation_decision:
            return STAGE_OFFICER_DECISION
        return STAGE_FINAL_INVESTIGATION
    # ONGOING
    if not facts.has_plan:
        return STAGE_PLAN
    if not facts.has_claim:
        return STAGE_CLAIM
    if not facts.has_pce_evidence and facts.milestone_count == 0:
        return STAGE_EVIDENCE
    if facts.milestone_count:
        latest = (facts.latest_milestone_status or "").upper()
        if latest not in {"COMPLETED", "PROCEED"}:
            return STAGE_MILESTONE
    if facts.has_officer_investigation_decision:
        return STAGE_OFFICER_DECISION
    if facts.risk_appropriate:
        return STAGE_RISK_FUSION
    return STAGE_INVESTIGATION


def checkpoint_actions_for(lifecycle_state: str) -> list[str]:
    if lifecycle_state == LifecycleStage.FUTURE.value:
        return list(CHECKPOINT_FUTURE)
    if lifecycle_state == LifecycleStage.COMPLETED.value:
        return list(CHECKPOINT_COMPLETED)
    if lifecycle_state == LifecycleStage.ONGOING.value:
        return list(CHECKPOINT_ONGOING)
    return list(CHECKPOINT_ONGOING)


def workflow_recommendation(facts: LifecycleFacts, current_stage: str) -> tuple[str | None, str]:
    """Officer-facing recommendation. Never a sanction or fraud conclusion."""
    if facts.lifecycle_state == LifecycleStage.FUTURE.value:
        planning = facts.planning_state or PLANNING
        if planning == NEEDS_MORE_INFORMATION or facts.need_inconclusive:
            return (
                "NEED MORE INFORMATION",
                "Need & Impact inputs are incomplete or the officer requested more information. "
                "This is not a sanction.",
            )
        if planning == DEFERRED:
            return (
                "DEFER",
                "Officer deferred this proposed work. Priority recommendation only; not a sanction.",
            )
        if planning == PRIORITIZED:
            return (
                "PRIORITIZE",
                "Officer recorded PRIORITIZED as a SARVSAKSHI planning state. "
                "Authorized officials still make the administrative decision. Not a sanction.",
            )
        if facts.need_priority_class:
            return (
                facts.need_priority_class.replace("_", " "),
                "Need & Impact priority recommendation for a proposed work. "
                "Authorized officials make the final administrative decision. Not a sanction.",
            )
        return (
            "NEED MORE INFORMATION",
            "Proposed-work prioritization is pending Need & Impact inputs.",
        )
    if facts.lifecycle_state == LifecycleStage.COMPLETED.value and facts.completed_insufficient:
        return (
            "INCONCLUSIVE",
            "Final investigation evidence is insufficient. Result is INCONCLUSIVE. "
            "Completion dates and expenditure were not invented.",
        )
    if current_stage == STAGE_MILESTONE and facts.latest_milestone_recommendation:
        rec = facts.latest_milestone_recommendation
        return (
            rec,
            f"Milestone Advisor last recommended {rec}. An authorized officer records "
            "PROCEED / HOLD / INSPECT / NEED MORE INFORMATION. Funds are not released.",
        )
    if facts.risk_explanation_type == "CONFLICTING_EVIDENCE":
        return (
            "NEED MORE INFORMATION",
            "Risk Fusion V2 reported conflicting evidence. Do not force a single conclusion.",
        )
    if facts.risk_insufficient:
        return (
            "NEED MORE INFORMATION",
            "Risk Fusion V2 has insufficient assessable evidence. Unavailable evidence is not treated as suspicious.",
        )
    return None, "See Risk Fusion V2 and officer checkpoints. AI recommends. Officers decide."
