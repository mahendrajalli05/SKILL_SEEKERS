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
    """Stored for later P1 UI. Not used in this foundation slice."""

    PROCEED = "PROCEED"
    HOLD = "HOLD"
    INSPECT = "INSPECT"
