"""Milestone Advisor V1 constants.

Decision-support only. Does not release funds, approve payments, or
change Cost / Time / Overlap / Compliance / Risk Fusion outputs.
"""

from __future__ import annotations

ENGINE_NAME = "milestone"
ENGINE_VERSION = "milestone-advisor-v1"
SIGNAL_TYPE = "milestone"

GOVERNANCE_NOTE = (
    "Milestone recommendation only. Authorized officials make the final "
    "administrative decision. SARVSAKSHI does not release funds."
)

HYBRID_NOTICE = (
    "Prototype simulation: some execution, financial, location, or "
    "milestone fields are synthetic and are not official MPLADS records."
)

SYNTHETIC_VALUE_NOTE = (
    "SYNTHETIC prototype value. Not an official MPLADS expenditure, "
    "progress, or milestone record."
)

SCORES_UNCHANGED_NOTE = (
    "Officer milestone action stored. Investigation Priority and Evidence "
    "Confidence were not changed. Intelligence engine outputs were not altered."
)

NO_PAYMENT_NOTE = (
    "No payment was executed. This prototype does not integrate with PFMS "
    "and does not release or sanction funds."
)

TIMELINE_SLOTS = ("M1", "M2", "M3", "M4")
COMPLETION_SLOT = "COMPLETION"

DEFAULT_MILESTONE_NAMES = {
    1: "M1",
    2: "M2",
    3: "M3",
    4: "M4",
}

REAL_CONFIDENCE_CAP = 0.90
HYBRID_CONFIDENCE_CAP = 0.72
SYNTHETIC_CONFIDENCE_CAP = 0.55
INSUFFICIENT_CONFIDENCE = 0.20

FORBIDDEN_OUTPUT_TERMS = (
    "fraud",
    "fraudulent",
    "fraud probability",
    "fraud detected",
    "funds released",
    "payment released",
    "payment executed",
    "pfms payment",
    "sanction approved",
    "automatic sanction",
)

LIMITATIONS = (
    "Milestone states are SARVSAKSHI workflow states, not official MPLADS status values.",
    "Recommendations are decision-support only. Authorized officers decide.",
    "SARVSAKSHI does not release funds and does not integrate with PFMS.",
    "REAL mode does not invent expenditure, execution dates, or milestone amounts.",
    "HYBRID synthetic milestone and execution values are labelled SYNTHETIC.",
    "Risk Fusion V1.1 is an input display only. Milestone weighting is not added to fusion.",
    "Time Intelligence is reused as a stored signal. Duration is not fabricated in REAL mode.",
)

AUDIT_CREATE = "milestone_create"
AUDIT_ASSESS = "milestone_assess"
AUDIT_DECISION = "milestone_decision"
ENTITY_TYPE = "milestone"
DECISION_ENTITY_TYPE = "milestone_decision"
