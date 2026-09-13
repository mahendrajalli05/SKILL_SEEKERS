"""End-to-End Project Lifecycle Orchestration V1 constants.

This layer does not score intelligence. It consumes existing Need & Impact,
PCE, Milestone, Risk Fusion V2, evidence, and officer-decision services.
Prototype workflow labels only — not official MPLADS status values.
"""

from __future__ import annotations

ENGINE_NAME = "lifecycle"
ENGINE_VERSION = "lifecycle-orchestration-v1"

GOVERNANCE_NOTE = (
    "SARVSAKSHI workflow state is an application lifecycle label. "
    "It is not an official MPLADS status. Source status is the observed extract STATUS. "
    "AI recommends. Authorized officers decide. "
    "This layer does not sanction a project, release funds, or determine fraud."
)

WORKFLOW_LABEL = "SARVSAKSHI workflow state"
SOURCE_STATUS_LABEL = "Source status"

NO_SANCTION_NOTE = (
    "Priority recommendation only. Authorized officials make final administrative "
    "decisions. This prototype does not sanction a project or release funds."
)
NO_PAYMENT_NOTE = (
    "No automatic payment. PFMS is not integrated. Officer actions do not release funds."
)
NO_FRAUD_NOTE = (
    "Investigation Priority is not a legal fraud finding and not a fraud probability."
)

# Administrative workflow states for FUTURE works only.
PLANNING = "PLANNING"
PRIORITIZED = "PRIORITIZED"
DEFERRED = "DEFERRED"
NEEDS_MORE_INFORMATION = "NEEDS_MORE_INFORMATION"

PLANNING_STATES = (PLANNING, PRIORITIZED, DEFERRED, NEEDS_MORE_INFORMATION)

# Timeline nodes. Not every project contains every node.
STAGE_FUTURE = "FUTURE"
STAGE_PRIORITIZATION = "PRIORITIZATION"
STAGE_ONGOING = "ONGOING"
STAGE_PLAN = "PLAN"
STAGE_CLAIM = "CLAIM"
STAGE_EVIDENCE = "EVIDENCE"
STAGE_MILESTONE = "MILESTONE"
STAGE_RISK_FUSION = "RISK_FUSION"
STAGE_INVESTIGATION = "INVESTIGATION"
STAGE_OFFICER_DECISION = "OFFICER_DECISION"
STAGE_COMPLETION = "COMPLETION"
STAGE_FINAL_INVESTIGATION = "FINAL_INVESTIGATION"

TIMELINE_STAGES = (
    STAGE_FUTURE,
    STAGE_PRIORITIZATION,
    STAGE_ONGOING,
    STAGE_PLAN,
    STAGE_CLAIM,
    STAGE_EVIDENCE,
    STAGE_MILESTONE,
    STAGE_RISK_FUSION,
    STAGE_INVESTIGATION,
    STAGE_OFFICER_DECISION,
    STAGE_COMPLETION,
    STAGE_FINAL_INVESTIGATION,
)

STATUS_COMPLETED = "COMPLETED"
STATUS_CURRENT = "CURRENT"
STATUS_PENDING = "PENDING"
STATUS_NOT_AVAILABLE = "NOT AVAILABLE"
STATUS_INCONCLUSIVE = "INCONCLUSIVE"

# Officer planning actions (FUTURE). Do not sanction.
ACTION_PRIORITIZE = "PRIORITIZE"
ACTION_DEFER = "DEFER"
ACTION_NEED_MORE_INFORMATION = "NEED_MORE_INFORMATION"
ACTION_RETURN_TO_PLANNING = "RETURN_TO_PLANNING"

PLANNING_ACTIONS = (
    ACTION_PRIORITIZE,
    ACTION_DEFER,
    ACTION_NEED_MORE_INFORMATION,
    ACTION_RETURN_TO_PLANNING,
)

PLANNING_ACTION_TO_STATE = {
    ACTION_PRIORITIZE: PRIORITIZED,
    ACTION_DEFER: DEFERRED,
    ACTION_NEED_MORE_INFORMATION: NEEDS_MORE_INFORMATION,
    ACTION_RETURN_TO_PLANNING: PLANNING,
}

CHECKPOINT_FUTURE = (
    ACTION_PRIORITIZE,
    ACTION_DEFER,
    ACTION_NEED_MORE_INFORMATION,
)
CHECKPOINT_ONGOING = (
    "PROCEED",
    "HOLD",
    "INSPECT",
    "REVIEW",
    "NEED MORE INFORMATION",
    "CONFIRM CONCERN",
    "DISMISS",
)
CHECKPOINT_COMPLETED = (
    "CONFIRM CONCERN",
    "DISMISS",
    "NEED MORE INFORMATION",
    "INSPECT",
    "REVIEW",
)

PLANNING_DECISION_AUDIT = "lifecycle_planning_decision"
PLANNING_ENTITY_TYPE = "lifecycle_decision"

FROZEN_FUSION_V2_VERSION = "risk-fusion-v2"
FROZEN_FUSION_V2_WEIGHTS = {
    "cost": 0.14,
    "time": 0.10,
    "overlap": 0.10,
    "compliance": 0.10,
    "graph": 0.08,
    "document": 0.06,
    "image": 0.06,
    "forensics": 0.05,
    "geospatial": 0.08,
    "satellite": 0.07,
    "citizen": 0.06,
    "milestone": 0.05,
    "pce": 0.05,
    "need": 0.00,
}

WEIGHT_NOTE = (
    "Lifecycle V1 does not add or change Risk Fusion V2 weights. "
    "Investigation Priority comes from stored or recomputed Risk Fusion V2."
)
