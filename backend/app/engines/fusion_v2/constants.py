"""Risk Fusion V2 constants and evidence catalog.

Prototype design parameters only. These are NOT official MoSPI / MPLADS
weights. This layer consumes stored Evidence Objects. It does not
reimplement frozen V1/V1.1 engines and does not output a fraud score.
"""

from __future__ import annotations

from app.domain.enums import SignalType
from app.engines.cost.constants import (
    FORBIDDEN_MODEL_INPUT_COLUMNS as COST_FORBIDDEN_MODEL_INPUT_COLUMNS,
)
from app.engines.fusion.constants import (
    COMPLIANCE_EXTRA_RULE_CAP,
    COMPLIANCE_EXTRA_RULE_POINTS,
    COMPLIANCE_SEVERITY_SCORE,
)

ENGINE_NAME = "fusion_v2"
ENGINE_VERSION = "risk-fusion-v2"
CONFIG_VERSION = "risk-fusion-v2"

FORBIDDEN_MODEL_INPUT_COLUMNS = frozenset(COST_FORBIDDEN_MODEL_INPUT_COLUMNS)

WEIGHT_NOTE = (
    "Prototype weights only. These are not official MoSPI or MPLADS weights."
)

GOVERNANCE_NOTE = (
    "Investigation Priority is an evidence-fusion ranking for review. "
    "It is not a legal finding and not a probability of wrongdoing. "
    "AI recommends. Authorized officers decide. "
    "This result does not sanction a project or release funds."
)

# ---------------------------------------------------------------------------
# V2 evidence groups. Planned weights sum to 1.00.
# Missing group weights are NOT redistributed.
# Need & Impact is catalogued but not used as an investigation-risk input.
# ---------------------------------------------------------------------------

GROUP_COST = "cost"
GROUP_TIME = "time"
GROUP_OVERLAP = "overlap"
GROUP_COMPLIANCE = "compliance"
GROUP_GRAPH = "graph"
GROUP_DOCUMENT = "document"
GROUP_IMAGE = "image"
GROUP_FORENSICS = "forensics"
GROUP_GEOSPATIAL = "geospatial"
GROUP_SATELLITE = "satellite"
GROUP_CITIZEN = "citizen"
GROUP_MILESTONE = "milestone"
GROUP_PCE = "pce"
GROUP_NEED = "need"

GROUP_ORDER = (
    GROUP_COST,
    GROUP_TIME,
    GROUP_OVERLAP,
    GROUP_COMPLIANCE,
    GROUP_GRAPH,
    GROUP_DOCUMENT,
    GROUP_IMAGE,
    GROUP_FORENSICS,
    GROUP_GEOSPATIAL,
    GROUP_SATELLITE,
    GROUP_CITIZEN,
    GROUP_MILESTONE,
    GROUP_PCE,
    GROUP_NEED,
)

GROUP_DISPLAY_NAMES = {
    GROUP_COST: "Cost",
    GROUP_TIME: "Time",
    GROUP_OVERLAP: "Overlap",
    GROUP_COMPLIANCE: "Compliance",
    GROUP_GRAPH: "Relationship graph",
    GROUP_DOCUMENT: "Document / blueprint",
    GROUP_IMAGE: "Image evidence",
    GROUP_FORENSICS: "Image forensics",
    GROUP_GEOSPATIAL: "Geospatial",
    GROUP_SATELLITE: "Satellite / remote sensing",
    GROUP_CITIZEN: "Citizen / Jan-Sakshi",
    GROUP_MILESTONE: "Milestone",
    GROUP_PCE: "Plan / claim / evidence",
    GROUP_NEED: "Need / impact",
}

# Maximum contribution = planned weight * 100 when the group scores 100
# and is not correlation-discounted.
GROUP_WEIGHTS = {
    GROUP_COST: 0.14,
    GROUP_TIME: 0.10,
    GROUP_OVERLAP: 0.10,
    GROUP_COMPLIANCE: 0.10,
    GROUP_GRAPH: 0.08,
    GROUP_DOCUMENT: 0.06,
    GROUP_IMAGE: 0.06,
    GROUP_FORENSICS: 0.05,
    GROUP_GEOSPATIAL: 0.08,
    GROUP_SATELLITE: 0.07,
    GROUP_CITIZEN: 0.06,
    GROUP_MILESTONE: 0.05,
    GROUP_PCE: 0.05,
    GROUP_NEED: 0.00,
}

PLANNED_WEIGHT_SUM = round(sum(GROUP_WEIGHTS.values()), 4)  # 1.00

# Default confidence factor applied to a group's mapped score:
# adjusted = raw * (CONFIDENCE_FLOOR + CONFIDENCE_SPAN * group_confidence)
CONFIDENCE_FLOOR = 0.55
CONFIDENCE_SPAN = 0.45
LOW_CONFIDENCE_THRESHOLD = 0.30

# Correlation keep-factors: the weaker of a correlated pair is multiplied.
CORR_SEMANTIC_KEEP = 0.25
CORR_SEMANTIC_PARTIAL_KEEP = 0.50
CORR_IMAGE_FAMILY_KEEP = 0.50
CORR_PCE_MILESTONE_KEEP = 0.30
CORR_DOCUMENT_PCE_KEEP = 0.35
CORR_CITIZEN_GEO_KEEP = 0.40

CORR_SEMANTIC = "SEMANTIC_SIMILARITY"
CORR_IMAGE_FAMILY = "IMAGE_FAMILY"
CORR_LOCATION = "LOCATION_FAMILY"
CORR_PCE_MILESTONE = "PLAN_CLAIM_PROGRESS"
CORR_DOCUMENT_PCE = "PLAN_CLAIM_DOC"
CORR_CITIZEN_GEO = "FIELD_LOCATION"

# Group → primary correlation family (for independence counting).
GROUP_CORRELATION_FAMILY = {
    GROUP_COST: "INDEPENDENT_COST",
    GROUP_TIME: "INDEPENDENT_TIME",
    GROUP_OVERLAP: CORR_SEMANTIC,
    GROUP_COMPLIANCE: "INDEPENDENT_COMPLIANCE",
    GROUP_GRAPH: CORR_SEMANTIC,
    GROUP_DOCUMENT: CORR_DOCUMENT_PCE,
    GROUP_IMAGE: CORR_IMAGE_FAMILY,
    GROUP_FORENSICS: CORR_IMAGE_FAMILY,
    GROUP_GEOSPATIAL: CORR_LOCATION,
    GROUP_SATELLITE: CORR_LOCATION,
    GROUP_CITIZEN: "INDEPENDENT_CITIZEN",
    GROUP_MILESTONE: CORR_PCE_MILESTONE,
    GROUP_PCE: CORR_PCE_MILESTONE,
    GROUP_NEED: "NOT_INVESTIGATION",
}

# Source reliability mix for Evidence Confidence (not Investigation Priority).
RELIABILITY_REAL = 1.00
RELIABILITY_HYBRID = 0.80
RELIABILITY_SYNTHETIC = 0.55

EC_COVERAGE_WEIGHT = 0.25
EC_QUALITY_WEIGHT = 0.20
EC_INDEPENDENCE_WEIGHT = 0.20
EC_EXTRACTION_WEIGHT = 0.15
EC_RELIABILITY_WEIGHT = 0.10
EC_COMPLETENESS_WEIGHT = 0.10

EC_REAL_CAP = 92
EC_HYBRID_CAP = 74
EC_SYNTHETIC_CAP = 56
EC_NONE_ASSESSABLE_CAP = 20
EC_CONFLICT_PENALTY = 0.18

# Investigation Priority bands (prototype, not official).
LOW_PRIORITY_MAX = 24
MEDIUM_PRIORITY_MAX = 44
LOW_CONFIDENCE_RECOMMEND = 40
VERY_LOW_CONFIDENCE = 28

# Engine-score review flag reused only to classify polarity. Not a legal cutoff.
ENGINE_FLAG_THRESHOLD = 60

# Citizen evidence is supporting only.
CITIZEN_SINGLE_CAP = 40
CITIZEN_MULTI_CAP = 70
CITIZEN_MULTI_MIN_REPORTS = 3

# Weak optional AI-generation forensic signal.
FORENSICS_AI_CAP = 50

# Effective contribution (0–100 scale points) that counts as a "major"
# synthetic/hybrid disclosure trigger.
MAJOR_CONTRIBUTION_POINTS = 5.0

MAPPED_SCORE_NOTE = (
    "Mapped scores for engines that do not emit a 0–100 anomaly score are "
    "prototype fusion mappings from disposition/signal type. They do not "
    "change the underlying engine."
)

UNAVAILABLE_REASON = (
    "No Evidence Object is available for this group in the requested data mode. "
    "Unavailable is not treated as zero-risk evidence and is not treated as suspicious."
)

NOT_ASSESSABLE_REASON = (
    "The Evidence Object is NOT_ASSESSABLE. Fusion does not treat that as low risk."
)

INCONCLUSIVE_REASON = (
    "The Evidence Object is INCONCLUSIVE. Fusion does not treat that as a "
    "low-risk score of 0 and does not treat it as suspicious."
)

NEED_NOT_INVESTIGATION_REASON = (
    "Need & Impact is a planning-priority score. It is not fused into "
    "Investigation Priority unless an integrity finding is present. High need "
    "is not high investigation priority."
)

COST_INCLUDED_IN_HYBRID_NOTE = (
    "Cost Intelligence V1.1 has no HYBRID-TEST mode. Observed allocation-vs-peers "
    "REAL evidence is fused with HYBRID evidence when data_mode=HYBRID is requested. "
    "Cost scores are not modified."
)

SYNTHETIC_DISCLOSURE = (
    "A major contribution relies on SYNTHETIC evidence. This is a test result, "
    "not a government finding."
)

HYBRID_DISCLOSURE = (
    "A major contribution relies on HYBRID/TEST enrichment. Synthetic fields "
    "are not official MPLADS values."
)

NO_SANCTION_NOTE = (
    "No automatic sanction and no automatic payment release are produced."
)

SIGNAL_TYPE_TO_GROUP: dict[str, str] = {
    SignalType.ALLOCATION_COST_ANOMALY.value: GROUP_COST,
    SignalType.TIME_ANOMALY.value: GROUP_TIME,
    SignalType.POTENTIAL_OVERLAP.value: GROUP_OVERLAP,
    SignalType.MPLADS_COMPLIANCE.value: GROUP_COMPLIANCE,
    SignalType.RELATIONSHIP_GRAPH.value: GROUP_GRAPH,
    SignalType.DOCUMENT.value: GROUP_DOCUMENT,
    SignalType.IMAGE.value: GROUP_IMAGE,
    SignalType.IMAGE_EXACT_DUPLICATE.value: GROUP_IMAGE,
    SignalType.IMAGE_POTENTIAL_REUSE.value: GROUP_IMAGE,
    SignalType.IMAGE_METADATA.value: GROUP_IMAGE,
    SignalType.IMAGE_QUALITY.value: GROUP_IMAGE,
    SignalType.IMAGE_FORENSIC_MANIPULATION.value: GROUP_FORENSICS,
    SignalType.IMAGE_FORENSIC_AI_GENERATION.value: GROUP_FORENSICS,
    SignalType.IMAGE_FORENSIC_METADATA.value: GROUP_FORENSICS,
    SignalType.IMAGE_FORENSIC_INCONCLUSIVE.value: GROUP_FORENSICS,
    SignalType.GEOSPATIAL.value: GROUP_GEOSPATIAL,
    SignalType.GEOSPATIAL_LOCATION_CONSISTENCY.value: GROUP_GEOSPATIAL,
    SignalType.GEOSPATIAL_LOCATION_MISMATCH.value: GROUP_GEOSPATIAL,
    SignalType.GEOSPATIAL_INCONCLUSIVE.value: GROUP_GEOSPATIAL,
    SignalType.CITIZEN.value: GROUP_CITIZEN,
    SignalType.CITIZEN_LOCATION.value: GROUP_CITIZEN,
    SignalType.CITIZEN_FEEDBACK.value: GROUP_CITIZEN,
    SignalType.CITIZEN_IMAGE.value: GROUP_CITIZEN,
    SignalType.CITIZEN_AGGREGATE.value: GROUP_CITIZEN,
    SignalType.MILESTONE.value: GROUP_MILESTONE,
    SignalType.PLAN_CLAIM_EVIDENCE.value: GROUP_PCE,
    SignalType.NEED_ASSESSMENT.value: GROUP_NEED,
    SignalType.IMPACT_ASSESSMENT.value: GROUP_NEED,
    SignalType.PRIORITY_ASSESSMENT.value: GROUP_NEED,
    SignalType.SATELLITE.value: GROUP_SATELLITE,
    SignalType.SATELLITE_AVAILABILITY.value: GROUP_SATELLITE,
    SignalType.SATELLITE_LOCATION.value: GROUP_SATELLITE,
    SignalType.SATELLITE_CHANGE.value: GROUP_SATELLITE,
    SignalType.SATELLITE_TEMPORAL.value: GROUP_SATELLITE,
    SignalType.SATELLITE_INCONCLUSIVE.value: GROUP_SATELLITE,
}

# Fallback mapped scores when an Evidence Object has no 0–100 engine score.
MAPPED_FLAGGED_SCORES = {
    SignalType.IMAGE_EXACT_DUPLICATE.value: 85,
    SignalType.IMAGE_POTENTIAL_REUSE.value: 72,
    SignalType.IMAGE_QUALITY.value: 40,
    SignalType.IMAGE_METADATA.value: 35,
    SignalType.IMAGE.value: 50,
    SignalType.IMAGE_FORENSIC_MANIPULATION.value: 80,
    SignalType.IMAGE_FORENSIC_AI_GENERATION.value: FORENSICS_AI_CAP,
    SignalType.IMAGE_FORENSIC_METADATA.value: 45,
    SignalType.GEOSPATIAL_LOCATION_MISMATCH.value: 78,
    SignalType.GEOSPATIAL.value: 60,
    SignalType.SATELLITE_LOCATION.value: 70,
    SignalType.SATELLITE_CHANGE.value: 70,
    SignalType.SATELLITE_TEMPORAL.value: 55,
    SignalType.SATELLITE.value: 60,
    SignalType.DOCUMENT.value: 55,
    SignalType.PLAN_CLAIM_EVIDENCE.value: 70,
    SignalType.MILESTONE.value: 60,
    SignalType.CITIZEN_AGGREGATE.value: 55,
    SignalType.CITIZEN_FEEDBACK.value: 35,
    SignalType.CITIZEN_IMAGE.value: 40,
    SignalType.CITIZEN_LOCATION.value: 45,
    SignalType.CITIZEN.value: 35,
}

# Conflict pairs: opposite polarity among these groups is CONFLICTING_EVIDENCE.
CONFLICT_PAIRS = (
    (GROUP_CITIZEN, GROUP_MILESTONE),
    (GROUP_CITIZEN, GROUP_PCE),
    (GROUP_CITIZEN, GROUP_SATELLITE),
    (GROUP_MILESTONE, GROUP_SATELLITE),
    (GROUP_PCE, GROUP_SATELLITE),
    (GROUP_GEOSPATIAL, GROUP_SATELLITE),
)

# Re-export V1.1 compliance mapping so V2 does not re-evaluate rules.
__all_compliance = (
    COMPLIANCE_SEVERITY_SCORE,
    COMPLIANCE_EXTRA_RULE_POINTS,
    COMPLIANCE_EXTRA_RULE_CAP,
)
