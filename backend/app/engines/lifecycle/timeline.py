"""Reusable project lifecycle timeline.

Unavailable steps are NOT AVAILABLE / INCONCLUSIVE.
Not every project contains every state.
"""

from __future__ import annotations

from app.domain.enums import LifecycleStage
from app.engines.lifecycle.constants import (
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
    STATUS_COMPLETED,
    STATUS_CURRENT,
    STATUS_INCONCLUSIVE,
    STATUS_NOT_AVAILABLE,
    STATUS_PENDING,
    TIMELINE_STAGES,
)
from app.engines.lifecycle.types import LifecycleFacts, TimelineNode

_LABELS = {
    STAGE_FUTURE: "Future / proposed",
    STAGE_PRIORITIZATION: "Prioritization (Need & Impact)",
    STAGE_ONGOING: "Ongoing",
    STAGE_PLAN: "Plan",
    STAGE_CLAIM: "Claim",
    STAGE_EVIDENCE: "Evidence",
    STAGE_MILESTONE: "Milestone",
    STAGE_RISK_FUSION: "Risk Fusion V2",
    STAGE_INVESTIGATION: "Investigation",
    STAGE_OFFICER_DECISION: "Officer decision",
    STAGE_COMPLETION: "Completion",
    STAGE_FINAL_INVESTIGATION: "Final investigation",
}

_HREFS = {
    STAGE_FUTURE: "",
    STAGE_PRIORITIZATION: "#need-impact",
    STAGE_ONGOING: "/investigate",
    STAGE_PLAN: "#plan-claim-evidence",
    STAGE_CLAIM: "#plan-claim-evidence",
    STAGE_EVIDENCE: "#plan-claim-evidence",
    STAGE_MILESTONE: "#milestones",
    STAGE_RISK_FUSION: "#risk-fusion-v2",
    STAGE_INVESTIGATION: "/investigate",
    STAGE_OFFICER_DECISION: "#officer-decision",
    STAGE_COMPLETION: "/investigate",
    STAGE_FINAL_INVESTIGATION: "/investigate",
}


def _node(stage: str, status: str, *, note: str | None = None) -> TimelineNode:
    available = status not in {STATUS_NOT_AVAILABLE}
    return TimelineNode(
        stage=stage,
        status=status,
        label=_LABELS[stage],
        available=available,
        href=_HREFS.get(stage) if available else None,
        note=note,
    )


def _mark(stage: str, current: str, present: bool, *, inconclusive: bool = False) -> str:
    if inconclusive:
        return STATUS_INCONCLUSIVE
    if not present:
        return STATUS_NOT_AVAILABLE
    if stage == current:
        return STATUS_CURRENT
    return STATUS_COMPLETED if _before(stage, current) else STATUS_PENDING


def _index(stage: str) -> int:
    return TIMELINE_STAGES.index(stage)


def _before(stage: str, current: str) -> bool:
    if current not in TIMELINE_STAGES or stage not in TIMELINE_STAGES:
        return False
    return _index(stage) < _index(current)


def build_timeline(facts: LifecycleFacts, current_stage: str) -> list[TimelineNode]:
    state = facts.lifecycle_state
    nodes: list[TimelineNode] = []

    if state == LifecycleStage.UNKNOWN.value:
        for stage in TIMELINE_STAGES:
            if stage == current_stage:
                nodes.append(_node(stage, STATUS_CURRENT, note="Lifecycle is UNKNOWN from source STATUS."))
            else:
                nodes.append(
                    _node(
                        stage,
                        STATUS_NOT_AVAILABLE,
                        note="NOT AVAILABLE — source STATUS did not map to FUTURE / ONGOING / COMPLETED.",
                    )
                )
        return nodes

    if state == LifecycleStage.FUTURE.value:
        planning = facts.planning_state or PLANNING
        nodes.append(_node(STAGE_FUTURE, STATUS_CURRENT if current_stage == STAGE_FUTURE else STATUS_COMPLETED))
        prio_note = None
        prio_status = STATUS_CURRENT
        if planning == PRIORITIZED:
            prio_status = STATUS_COMPLETED
            prio_note = "Officer recorded PRIORITIZED. Not a sanction."
        elif planning == DEFERRED:
            prio_status = STATUS_COMPLETED
            prio_note = "Officer recorded DEFERRED. Not a sanction."
        elif planning == NEEDS_MORE_INFORMATION:
            prio_status = STATUS_INCONCLUSIVE
            prio_note = "Officer requested more information."
        elif facts.need_inconclusive:
            prio_status = STATUS_INCONCLUSIVE
            prio_note = "Need & Impact is INCONCLUSIVE until unavailable inputs are sourced."
        nodes.append(_node(STAGE_PRIORITIZATION, prio_status, note=prio_note))
        later_note = "NOT AVAILABLE — this work is in the FUTURE / proposed workflow."
        for stage in TIMELINE_STAGES:
            if stage in {STAGE_FUTURE, STAGE_PRIORITIZATION}:
                continue
            nodes.append(_node(stage, STATUS_NOT_AVAILABLE, note=later_note))
        return nodes

    if state == LifecycleStage.ONGOING.value:
        nodes.append(
            _node(
                STAGE_FUTURE,
                STATUS_NOT_AVAILABLE,
                note="NOT AVAILABLE — source STATUS maps to ONGOING, not a stored FUTURE record.",
            )
        )
        nodes.append(
            _node(
                STAGE_PRIORITIZATION,
                STATUS_NOT_AVAILABLE,
                note="NOT AVAILABLE — Need & Impact is the FUTURE planning workflow.",
            )
        )
        nodes.append(_node(STAGE_ONGOING, STATUS_COMPLETED if current_stage != STAGE_ONGOING else STATUS_CURRENT))
        nodes.append(_node(STAGE_PLAN, _mark(STAGE_PLAN, current_stage, facts.has_plan)))
        nodes.append(_node(STAGE_CLAIM, _mark(STAGE_CLAIM, current_stage, facts.has_claim)))
        evidence_present = facts.has_pce_evidence or facts.has_documents or facts.has_images
        nodes.append(
            _node(
                STAGE_EVIDENCE,
                _mark(STAGE_EVIDENCE, current_stage, evidence_present),
            )
        )
        milestone_present = facts.milestone_count > 0
        milestone_status = _mark(STAGE_MILESTONE, current_stage, milestone_present)
        if not milestone_present:
            milestone_status = STATUS_NOT_AVAILABLE
        nodes.append(_node(STAGE_MILESTONE, milestone_status))
        risk_status = _mark(STAGE_RISK_FUSION, current_stage, facts.risk_appropriate)
        if facts.risk_insufficient and current_stage == STAGE_RISK_FUSION:
            risk_status = STATUS_INCONCLUSIVE
        nodes.append(_node(STAGE_RISK_FUSION, risk_status))
        nodes.append(
            _node(STAGE_INVESTIGATION, _mark(STAGE_INVESTIGATION, current_stage, True))
        )
        decision_present = facts.has_officer_investigation_decision
        nodes.append(
            _node(
                STAGE_OFFICER_DECISION,
                _mark(STAGE_OFFICER_DECISION, current_stage, decision_present or current_stage == STAGE_OFFICER_DECISION),
            )
        )
        nodes.append(
            _node(
                STAGE_COMPLETION,
                STATUS_PENDING,
                note="PENDING — source STATUS is not completed.",
            )
        )
        nodes.append(
            _node(
                STAGE_FINAL_INVESTIGATION,
                STATUS_NOT_AVAILABLE,
                note="NOT AVAILABLE until the work is completed.",
            )
        )
        return nodes

    # COMPLETED
    nodes.append(
        _node(
            STAGE_FUTURE,
            STATUS_NOT_AVAILABLE,
            note="NOT AVAILABLE — source STATUS maps to COMPLETED.",
        )
    )
    nodes.append(
        _node(
            STAGE_PRIORITIZATION,
            STATUS_NOT_AVAILABLE,
            note="NOT AVAILABLE — Need & Impact is the FUTURE planning workflow.",
        )
    )
    nodes.append(_node(STAGE_ONGOING, STATUS_COMPLETED if facts.has_plan or facts.has_claim else STATUS_NOT_AVAILABLE))
    nodes.append(_node(STAGE_PLAN, STATUS_COMPLETED if facts.has_plan else STATUS_NOT_AVAILABLE))
    nodes.append(_node(STAGE_CLAIM, STATUS_COMPLETED if facts.has_claim else STATUS_NOT_AVAILABLE))
    evidence_present = facts.has_pce_evidence or facts.has_documents or facts.has_images
    if facts.completed_insufficient and not evidence_present:
        nodes.append(_node(STAGE_EVIDENCE, STATUS_INCONCLUSIVE, note="INCONCLUSIVE — insufficient final evidence."))
    else:
        nodes.append(_node(STAGE_EVIDENCE, STATUS_COMPLETED if evidence_present else STATUS_NOT_AVAILABLE))
    nodes.append(
        _node(STAGE_MILESTONE, STATUS_COMPLETED if facts.milestone_count else STATUS_NOT_AVAILABLE)
    )
    if facts.risk_insufficient:
        nodes.append(_node(STAGE_RISK_FUSION, STATUS_INCONCLUSIVE, note="INCONCLUSIVE — Risk Fusion V2 has insufficient evidence."))
    else:
        nodes.append(_node(STAGE_RISK_FUSION, STATUS_COMPLETED if facts.risk_appropriate else STATUS_NOT_AVAILABLE))
    nodes.append(_node(STAGE_INVESTIGATION, STATUS_COMPLETED if not facts.completed_insufficient else STATUS_INCONCLUSIVE))
    nodes.append(
        _node(
            STAGE_OFFICER_DECISION,
            STATUS_CURRENT
            if current_stage == STAGE_OFFICER_DECISION
            else (STATUS_COMPLETED if facts.has_officer_investigation_decision else STATUS_PENDING),
        )
    )
    nodes.append(_node(STAGE_COMPLETION, STATUS_COMPLETED, note="Source STATUS maps to COMPLETED. Completion date was not invented."))
    final_status = STATUS_INCONCLUSIVE if facts.completed_insufficient else STATUS_CURRENT
    if current_stage == STAGE_OFFICER_DECISION and not facts.completed_insufficient:
        final_status = STATUS_COMPLETED
    nodes.append(
        _node(
            STAGE_FINAL_INVESTIGATION,
            final_status,
            note="INCONCLUSIVE" if facts.completed_insufficient else "Final case summary from stored evidence only.",
        )
    )
    return nodes


def split_completed_pending(timeline: list[TimelineNode]) -> tuple[list[str], list[str]]:
    completed = [item.stage for item in timeline if item.status == STATUS_COMPLETED]
    pending = [item.stage for item in timeline if item.status in {STATUS_PENDING, STATUS_CURRENT}]
    return completed, pending
