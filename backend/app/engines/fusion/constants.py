"""Risk Fusion V1.1 constants.

Prototype weights only. These are NOT official MoSPI weights.
This layer consumes Evidence Objects. It does not reimplement Cost,
Time, Overlap, or Compliance scoring and does not output a fraud score.

V1.1 keeps the V1 missing-signal penalty and displays Investigation Priority
as Raw Risk / 0.70. Weights of unavailable signals are not redistributed
onto currently available signals.
"""

from __future__ import annotations

from app.domain.enums import SignalType
from app.engines.cost.constants import (
    FORBIDDEN_MODEL_INPUT_COLUMNS as COST_FORBIDDEN_MODEL_INPUT_COLUMNS,
)

ENGINE_NAME = "fusion"
ENGINE_VERSION = "risk-fusion-v1.1"
CONFIG_VERSION = "risk-fusion-v1.1"

FORBIDDEN_MODEL_INPUT_COLUMNS = frozenset(COST_FORBIDDEN_MODEL_INPUT_COLUMNS)

WEIGHT_NOTE = (
    "Prototype weights only. These are not official MoSPI weights."
)

GOVERNANCE_NOTE = (
    "Investigation Priority is an evidence-fusion ranking for review. "
    "It is not a legal finding and not a probability of wrongdoing. "
    "AI recommends. Authorized officers decide."
)

# Planned prototype weights. Sum is 1.00. Do not renormalize silently.
COST_WEIGHT = 0.25
SCHEDULE_WEIGHT = 0.15
OVERLAP_WEIGHT = 0.15
COMPLIANCE_WEIGHT = 0.15

INTEGRATED_SIGNAL_IDS = (
    "cost",
    "schedule",
    "overlap",
    "compliance",
)

INTEGRATED_WEIGHTS = {
    "cost": COST_WEIGHT,
    "schedule": SCHEDULE_WEIGHT,
    "overlap": OVERLAP_WEIGHT,
    "compliance": COMPLIANCE_WEIGHT,
}

INTEGRATED_WEIGHT_SUM = round(sum(INTEGRATED_WEIGHTS.values()), 2)  # 0.70

# Remaining 30% is reserved for engines that are not yet integrated.
# Weights are kept explicit so they are never silently redistributed.
FUTURE_SIGNAL_WEIGHTS = {
    "field_evidence": 0.05,
    "relationship_graph": 0.05,
    "citizen_evidence": 0.04,
    "geospatial": 0.04,
    "image": 0.04,
    "document": 0.04,
    "milestone": 0.04,
}

FUTURE_WEIGHT_SUM = round(sum(FUTURE_SIGNAL_WEIGHTS.values()), 2)  # 0.30
PLANNED_WEIGHT_SUM = round(INTEGRATED_WEIGHT_SUM + FUTURE_WEIGHT_SUM, 2)  # 1.00

SIGNAL_DISPLAY_NAMES = {
    "cost": "Cost",
    "schedule": "Schedule",
    "overlap": "Overlap",
    "compliance": "Compliance",
    "field_evidence": "Field evidence",
    "relationship_graph": "Relationship graph",
    "citizen_evidence": "Citizen evidence",
    "geospatial": "Geospatial",
    "image": "Image",
    "document": "Document",
    "milestone": "Milestone",
}

SIGNAL_TYPE_TO_SLOT = {
    SignalType.ALLOCATION_COST_ANOMALY: "cost",
    SignalType.TIME_ANOMALY: "schedule",
    SignalType.POTENTIAL_OVERLAP: "overlap",
    SignalType.MPLADS_COMPLIANCE: "compliance",
}

SLOT_TO_SIGNAL_TYPE = {slot: signal for signal, slot in SIGNAL_TYPE_TO_SLOT.items()}

# Cost/Time/Overlap review flag on engine scores. Used only to classify
# a contributing signal as flagged vs not flagged. Fusion does not change
# those scores.
ENGINE_FLAG_THRESHOLD = 60

# Investigation Priority bands on the V1.1 0–100 display scale.
# Raw Risk still uses un-renormalized weights (theoretical max 70).
# Display IP = Raw Risk / 0.70, then recommendations use that score.
LOW_PRIORITY_MAX = 24
MEDIUM_PRIORITY_MAX = 44
INSPECT_ACTION_MAX = 59

# Evidence Confidence mix (weights sum to 1.00).
EC_COVERAGE_WEIGHT = 0.40
EC_QUALITY_WEIGHT = 0.35
EC_INDEPENDENCE_WEIGHT = 0.15
EC_FUTURE_COVERAGE_WEIGHT = 0.10  # always 0 in V1; documents the reserved 30%

EC_REAL_CAP = 90
EC_HYBRID_CAP = 72
EC_SYNTHETIC_CAP = 55
EC_NONE_ASSESSABLE_CAP = 18

# Compliance has no engine 0–100 anomaly score. Fusion maps evidence
# disposition/severity/rule_ids only (does not re-evaluate rules).
COMPLIANCE_SEVERITY_SCORE = {
    "info": 40,
    "watch": 60,
    "attention": 80,
}
COMPLIANCE_EXTRA_RULE_POINTS = 10
COMPLIANCE_EXTRA_RULE_CAP = 20

PEER_QUALITY_BLEND = 0.30
OBJECT_CONFIDENCE_BLEND = 0.70

FUTURE_UNAVAILABLE_REASON = (
    "Not yet integrated into Risk Fusion V1.1. No evidence was invented."
)

MISSING_INTEGRATED_REASON = (
    "No Evidence Object is available for this signal in the requested data mode."
)

NOT_ASSESSABLE_REASON = (
    "The Evidence Object is NOT_ASSESSABLE. Fusion does not treat that as low risk."
)

INCONCLUSIVE_SIGNAL_REASON = (
    "The Evidence Object is INCONCLUSIVE (insufficient engine evidence). "
    "Fusion does not treat that as a low-risk score of 0."
)

COST_INCLUDED_IN_HYBRID_NOTE = (
    "Cost Intelligence V1.1 has no HYBRID-TEST mode. Observed allocation-vs-peers "
    "REAL evidence is fused with HYBRID Time/Overlap/Compliance evidence when "
    "data_mode=HYBRID is requested. Cost scores are not modified."
)
