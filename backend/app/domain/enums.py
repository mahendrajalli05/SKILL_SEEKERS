from enum import Enum


class LifecycleStage(str, Enum):
    FUTURE = "FUTURE"
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"
    UNKNOWN = "UNKNOWN"


class EvidenceStatus(str, Enum):
    CONSISTENT = "consistent"
    MISMATCH = "mismatch"
    INCONCLUSIVE = "inconclusive"
    NOT_ASSESSABLE = "not_assessable"


class EvidenceSeverity(str, Enum):
    INFO = "info"
    WATCH = "watch"
    ATTENTION = "attention"


class EvidenceEngine(str, Enum):
    COST = "cost"
    TIME = "time"
    OVERLAP = "overlap"
    COMPLIANCE = "compliance"
    GRAPH = "graph"
    NEED = "need"
    PCE = "pce"
    CITIZEN = "citizen"
    IMAGE = "image"
    GEO = "geo"
    DOCUMENT = "document"
    MILESTONE = "milestone"
    FORENSICS = "forensics"
    SATELLITE = "satellite"
    ML = "ml"
    CONTEXT = "context"


class DataMode(str, Enum):
    """How the evidence was produced. REAL must never be labelled SYNTHETIC."""

    REAL = "REAL"
    HYBRID = "HYBRID"
    SYNTHETIC = "SYNTHETIC"


class EvidenceDisposition(str, Enum):
    """Officer-facing assessment of one evidence object. Not a legal finding."""

    WHY_FLAGGED = "WHY_FLAGGED"
    WHY_NOT_FLAGGED = "WHY_NOT_FLAGGED"
    INCONCLUSIVE = "INCONCLUSIVE"
    NOT_ASSESSABLE = "NOT_ASSESSABLE"


class EvidenceFactKind(str, Enum):
    OBSERVATION = "OBSERVATION"
    DERIVED = "DERIVED"


class SignalType(str, Enum):
    """Canonical signal names for current and later engines."""

    ALLOCATION_COST_ANOMALY = "allocation_cost_anomaly"
    TIME_ANOMALY = "time_anomaly"
    POTENTIAL_OVERLAP = "potential_overlap"
    MPLADS_COMPLIANCE = "mplads_compliance"
    RELATIONSHIP_GRAPH = "relationship_graph"
    DOCUMENT = "document"
    IMAGE = "image"
    IMAGE_EXACT_DUPLICATE = "IMAGE_EXACT_DUPLICATE"
    IMAGE_POTENTIAL_REUSE = "IMAGE_POTENTIAL_REUSE"
    IMAGE_METADATA = "IMAGE_METADATA"
    IMAGE_QUALITY = "IMAGE_QUALITY"
    IMAGE_FORENSIC_MANIPULATION = "IMAGE_FORENSIC_MANIPULATION"
    IMAGE_FORENSIC_AI_GENERATION = "IMAGE_FORENSIC_AI_GENERATION"
    IMAGE_FORENSIC_METADATA = "IMAGE_FORENSIC_METADATA"
    IMAGE_FORENSIC_INCONCLUSIVE = "IMAGE_FORENSIC_INCONCLUSIVE"
    GEOSPATIAL = "geospatial"
    GEOSPATIAL_LOCATION_CONSISTENCY = "GEOSPATIAL_LOCATION_CONSISTENCY"
    GEOSPATIAL_LOCATION_MISMATCH = "GEOSPATIAL_LOCATION_MISMATCH"
    GEOSPATIAL_INCONCLUSIVE = "GEOSPATIAL_INCONCLUSIVE"
    CITIZEN = "citizen"
    CITIZEN_LOCATION = "CITIZEN_LOCATION"
    CITIZEN_FEEDBACK = "CITIZEN_FEEDBACK"
    CITIZEN_IMAGE = "CITIZEN_IMAGE"
    CITIZEN_AGGREGATE = "CITIZEN_AGGREGATE"
    MILESTONE = "milestone"
    PLAN_CLAIM_EVIDENCE = "plan_claim_evidence"
    NEED_ASSESSMENT = "NEED_ASSESSMENT"
    IMPACT_ASSESSMENT = "IMPACT_ASSESSMENT"
    PRIORITY_ASSESSMENT = "PRIORITY_ASSESSMENT"
    SATELLITE = "satellite"
    SATELLITE_AVAILABILITY = "SATELLITE_AVAILABILITY"
    SATELLITE_LOCATION = "SATELLITE_LOCATION"
    SATELLITE_CHANGE = "SATELLITE_CHANGE"
    SATELLITE_TEMPORAL = "SATELLITE_TEMPORAL"
    SATELLITE_INCONCLUSIVE = "SATELLITE_INCONCLUSIVE"
    ML_ANOMALY_SIGNAL = "ML_ANOMALY_SIGNAL"
    REFERENCE_COST_CONTEXT = "REFERENCE_COST_CONTEXT"
    DEVELOPMENT_NEED_CONTEXT = "DEVELOPMENT_NEED_CONTEXT"
    INFRASTRUCTURE_CONTEXT = "INFRASTRUCTURE_CONTEXT"
    CONTEXT_UNAVAILABLE = "CONTEXT_UNAVAILABLE"
    CONTEXT_INCONCLUSIVE = "CONTEXT_INCONCLUSIVE"


class SourceType(str, Enum):
    MPLADS_PROJECT_RECORD = "mplads_project_record"
    HYBRID_ENRICHMENT = "hybrid_enrichment"
    SYNTHETIC_TEST_RECORD = "synthetic_test_record"
    GUIDELINE_RULE = "guideline_rule"
    PEER_PROJECT_RECORDS = "peer_project_records"
    GUIDELINE_CATALOG = "guideline_catalog"
    DOCUMENT_ARTIFACT = "document_artifact"
    IMAGE_ARTIFACT = "image_artifact"
    GEOSPATIAL_RECORD = "geospatial_record"
    CITIZEN_REPORT = "citizen_report"
    MILESTONE_CLAIM = "milestone_claim"
    PLAN_RECORD = "plan_record"
    CLAIM_STATEMENT = "claim_statement"
    OFFICER_UPLOAD = "officer_upload"
    SATELLITE_OBSERVATION = "satellite_observation"
    ML_MODEL = "ml_model"
    EXTERNAL_PUBLIC_DATASET = "external_public_dataset"


class AmountRole(str, Enum):
    UNKNOWN = "unknown"
    RECOMMENDED = "recommended"
    SANCTIONED = "sanctioned"
    UTILISED = "utilised"
    SPENT = "spent"
    OTHER = "other"


class OfficerDecisionType(str, Enum):
    CONFIRM_CONCERN = "confirm_concern"
    DISMISS = "dismiss"
    NEED_MORE_INFO = "need_more_info"


class MilestoneRecommendation(str, Enum):
    """Milestone Advisor V1 recommendation. Not a funding decision."""

    PROCEED = "PROCEED"
    HOLD = "HOLD"
    INSPECT = "INSPECT"
    INCONCLUSIVE = "INCONCLUSIVE"


class MilestoneStatus(str, Enum):
    """SARVSAKSHI workflow states. Not official MPLADS status values."""

    PLANNED = "PLANNED"
    CLAIMED = "CLAIMED"
    UNDER_REVIEW = "UNDER_REVIEW"
    PROCEED = "PROCEED"
    HOLD = "HOLD"
    INSPECT = "INSPECT"
    COMPLETED = "COMPLETED"


class MilestoneOfficerAction(str, Enum):
    """Recorded officer action. Does not release funds or change scores."""

    PROCEED = "PROCEED"
    HOLD = "HOLD"
    INSPECT = "INSPECT"
    NEED_MORE_INFORMATION = "NEED_MORE_INFORMATION"


class RiskSignalState(str, Enum):
    """How a fusion slot is treated. Unavailable is not the same as low risk."""

    ASSESSABLE = "ASSESSABLE"
    NOT_ASSESSABLE = "NOT_ASSESSABLE"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_YET_INTEGRATED = "NOT_YET_INTEGRATED"


class InvestigationPriorityBand(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class RecommendedAction(str, Enum):
    """Officer-facing recommendation. Not a legal or administrative decision."""

    MONITOR = "MONITOR"
    REVIEW = "REVIEW"
    INSPECT = "INSPECT"
    INVESTIGATE = "INVESTIGATE"
    NEED_MORE_INFORMATION = "NEED_MORE_INFORMATION"


class FusionExplanationType(str, Enum):
    WHY_FLAGGED = "WHY_FLAGGED"
    WHY_NOT_FLAGGED = "WHY_NOT_FLAGGED"
    INCONCLUSIVE = "INCONCLUSIVE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
