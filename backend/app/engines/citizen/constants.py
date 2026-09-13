"""Jan-Sakshi / Citizen Evidence V1 constants.

Citizen submissions are supporting field evidence only.
They do not prove poor quality or project failure.
500 m is a SARVSAKSHI prototype verification rule, not an official MPLADS rule.
"""

from __future__ import annotations

from app.engines.geo.constants import DEFAULT_THRESHOLD_METERS

ENGINE_NAME = "citizen"
ENGINE_VERSION = "jan-sakshi-v1"

LOCATION_VERIFIED = "LOCATION_VERIFIED"
LOCATION_REJECTED = "LOCATION_REJECTED"
LOCATION_UNAVAILABLE = "LOCATION_UNAVAILABLE"
INCONCLUSIVE = "INCONCLUSIVE"

STATUS_ACCEPTED = "ACCEPTED"
STATUS_REJECTED = "REJECTED"
STATUS_INCONCLUSIVE = "INCONCLUSIVE"

TIMESTAMP_RECORDED = "TIMESTAMP_RECORDED"
TIMESTAMP_UNAVAILABLE = "TIMESTAMP_UNAVAILABLE"
TIMESTAMP_SERVER_ONLY = "TIMESTAMP_SERVER_ONLY"

ISSUE_WORK_QUALITY = "work_quality"
ISSUE_INCOMPLETE_WORK = "incomplete_work"
ISSUE_DELAYED_WORK = "delayed_work"
ISSUE_LOCATION_CONCERN = "location_concern"
ISSUE_SAFETY = "safety"
ISSUE_OTHER = "other"

ALLOWED_ISSUE_CATEGORIES = frozenset(
    {
        ISSUE_WORK_QUALITY,
        ISSUE_INCOMPLETE_WORK,
        ISSUE_DELAYED_WORK,
        ISSUE_LOCATION_CONCERN,
        ISSUE_SAFETY,
        ISSUE_OTHER,
    }
)

ISSUE_LABELS = {
    ISSUE_WORK_QUALITY: "Work quality",
    ISSUE_INCOMPLETE_WORK: "Incomplete work",
    ISSUE_DELAYED_WORK: "Delayed work",
    ISSUE_LOCATION_CONCERN: "Location concern",
    ISSUE_SAFETY: "Safety",
    ISSUE_OTHER: "Other",
}

SENTIMENT_POSITIVE = "positive"
SENTIMENT_NEGATIVE = "negative"
SENTIMENT_MIXED = "mixed"
SENTIMENT_NEUTRAL = "neutral"
SENTIMENT_INCONCLUSIVE = "INCONCLUSIVE"

SEVERITY_LOW = "low"
SEVERITY_MEDIUM = "medium"
SEVERITY_HIGH = "high"
SEVERITY_INCONCLUSIVE = "INCONCLUSIVE"

SAMPLE_INSUFFICIENT = "Insufficient citizen sample"
SAMPLE_LIMITED = "Limited citizen sample"
SAMPLE_COMMUNITY = "Community feedback signal available"

AGGREGATE_NONE = "NONE"
AGGREGATE_COMMUNITY_CONCERN = "POTENTIAL_COMMUNITY_CONCERN"
AGGREGATE_INCONCLUSIVE = "INCONCLUSIVE"

DUPLICATE_FLAG = "POTENTIAL_DUPLICATE_CITIZEN_EVIDENCE"

PCE_CONTRADICTION = "CITIZEN_CONTRADICTION"
PCE_CONCERN = "EVIDENCE_OF_CONCERN"
PCE_CONSISTENT = "CONSISTENT"
PCE_INCONCLUSIVE = "INCONCLUSIVE"

SIGNAL_LOCATION = "CITIZEN_LOCATION"
SIGNAL_FEEDBACK = "CITIZEN_FEEDBACK"
SIGNAL_IMAGE = "CITIZEN_IMAGE"
SIGNAL_AGGREGATE = "CITIZEN_AGGREGATE"

MIN_SATISFACTION = 1
MAX_SATISFACTION = 5
MIN_TEXT_CHARS = 12
MIN_TEXT_WORDS = 3

DEFAULT_RADIUS_METERS = DEFAULT_THRESHOLD_METERS
INSUFFICIENT_SAMPLE_MAX = 3
COMMUNITY_SIGNAL_MIN = 10
MIN_REPORTS_FOR_CONCERN = 3
RATE_LIMIT_COUNT = 20
RATE_LIMIT_WINDOW_SECONDS = 3600

REAL_CONFIDENCE_CAP = 0.50
HYBRID_CONFIDENCE_CAP = 0.40
SYNTHETIC_CONFIDENCE_CAP = 0.35
SINGLE_REPORT_CONFIDENCE = 0.18
UNAVAILABLE_CONFIDENCE = 0.16

THRESHOLD_NOTE = (
    "500 m is a SARVSAKSHI prototype verification rule. "
    "It is not an official MPLADS rule."
)

GOVERNANCE_NOTE = (
    "Jan-Sakshi citizen submissions are supporting field evidence only. "
    "One citizen report does not establish truth. The system does not determine "
    "a legal finding of wrongdoing, poor quality, or project failure. "
    "AI recommends. Authorized officers decide."
)

WATERMARK_NOTE = (
    "The watermark is an evidence-presentation aid. It is not proof that the "
    "image is authentic. The original uploaded image is not altered."
)

EXIF_NOTE = "reported metadata from uploaded file"

PRIVACY_NOTE = (
    "Citizen GPS is verification data and is not exposed in public-facing "
    "aggregate results. No unnecessary personally identifying information is collected."
)

SYNTHETIC_BADGE = "TEST/SYNTHETIC — not a genuine public citizen report."
HYBRID_NOTICE = (
    "HYBRID/TEST: real MPLADS work plus labelled SYNTHETIC prototype citizen evidence. "
    "Synthetic citizen submissions are not genuine public reports."
)

PCE_CLAIM_NOT_FALSE_NOTE = (
    "Citizen evidence of concern is supporting evidence only. "
    "The recorded claim is not marked false automatically."
)

LIMITATIONS = (
    "Citizen evidence is supporting evidence only.",
    "One citizen report does not establish truth.",
    "500 m is a prototype verification rule, not an official MPLADS rule.",
    "REAL project GPS is unavailable in the current public extract and is not invented.",
    "EXIF GPS and timestamps are reported metadata from the uploaded file.",
    "The watermark is a presentation aid, not proof of authenticity.",
    "Sentiment is not proof of project quality.",
    "Citizen evidence is not fused into Investigation Priority in V1.",
    "No personally identifying information is required for V1.",
)

FORBIDDEN_OUTPUT_TERMS = (
    "fraud",
    "fraudulent",
    "fraud probability",
    "fraud detected",
    "funds released",
    "payment released",
    "automatic sanction",
)

POSITIVE_TOKENS = (
    "good",
    "excellent",
    "satisfied",
    "useful",
    "working",
    "complete",
    "completed",
    "helpful",
    "clean",
    "well built",
    "well-built",
    "positive",
)

NEGATIVE_TOKENS = (
    "poor",
    "bad",
    "incomplete",
    "unfinished",
    "delay",
    "delayed",
    "unsafe",
    "broken",
    "cracked",
    "not working",
    "not complete",
    "complaint",
    "damaged",
    "missing",
    "absent",
)

INCOMPLETE_TOKENS = (
    "incomplete",
    "not complete",
    "unfinished",
    "not finished",
    "remaining",
    "half done",
    "partially done",
    "still pending",
)

DELAY_TOKENS = ("delay", "delayed", "late", "slow", "overdue")
QUALITY_TOKENS = ("poor quality", "cracked", "damaged", "substandard", "low quality", "badly built")
LOCATION_TOKENS = ("wrong location", "wrong place", "different site", "not at site", "elsewhere")
SAFETY_TOKENS = ("unsafe", "danger", "accident", "hazard", "injury")

COMPLETION_CLAIM_TOKENS = (
    "completed",
    "complete",
    "100%",
    "fully completed",
    "work completed",
    "finished",
    "road work is complete",
)

ENTITY_TYPE = "citizen_report"
AUDIT_SUBMIT = "citizen_submit"
AUDIT_VERIFY = "citizen_verify"
SOURCE_CITIZEN_UPLOAD = "citizen_upload"
