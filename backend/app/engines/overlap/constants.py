"""Overlap / Duplicate Intelligence V1 constants.

Identifies potential overlap or potential duplicate MPLADS works.
Does not assign fused Investigation Priority and does not conclude fraud.
HYBRID scenario labels are never model inputs.
"""

from __future__ import annotations

from app.engines.cost.constants import (
    FORBIDDEN_MODEL_INPUT_COLUMNS as COST_FORBIDDEN_MODEL_INPUT_COLUMNS,
)

ENGINE_NAME = "overlap"
ENGINE_VERSION = "overlap-multi-v1"
EVIDENCE_TYPE = "potential_overlap"
SIGNAL_KIND = "potential_overlap"

# Sentence Transformers model when the optional package is installed.
SENTENCE_TRANSFORMER_MODEL = "all-MiniLM-L6-v2"
HASHED_EMBEDDER_NAME = "hashed-token-charngram-v1"
HASHED_EMBEDDING_DIM = 256

# Candidate generation (blocking). Not an all-pairs scan of 56,138 rows.
MAX_FULL_BLOCK_SIZE = 80
MAX_CANDIDATES_PER_SUBJECT = 250
MAX_DISPLAY_MATCHES = 10
DATE_CANDIDATE_WINDOW_DAYS = 180
GEO_CELL_DEGREES = 0.005  # ~550 m candidate cells; 500 m is the scored radius

# Scoring / classification. Deterministic and documented in OVERLAP_V1_REPORT.md.
DATE_DECAY_DAYS = 90
DATE_PROXIMATE_DAYS = 45
GPS_PROXIMITY_M = 500.0
AMOUNT_SIMILAR_MIN = 0.80
LOCATION_SIMILAR_MIN = 0.50
SEMANTIC_CANDIDATE_MIN = 0.55
SEMANTIC_OVERLAP_MIN = 0.72
SEMANTIC_HIGH = 0.85
SEMANTIC_NEAR_DUPLICATE = 0.92
OVERALL_OVERLAP_MIN = 0.58
MIN_SUPPORTING_FOR_DUPLICATE = 2
FLAG_SCORE_THRESHOLD = 60

WEIGHT_SEMANTIC = 0.40
WEIGHT_CONSTITUENCY = 0.15
WEIGHT_CATEGORY = 0.10
WEIGHT_AMOUNT = 0.15
WEIGHT_DATE = 0.10
WEIGHT_LOCATION = 0.10
WEIGHT_GPS = 0.25

REAL_CONFIDENCE_CAP = 66
HYBRID_GPS_CONFIDENCE_CAP = 70
MISSING_DESCRIPTION_CONFIDENCE = 8

# Observed generic title tokens used only for blocking. Not official work types.
WEAK_BLOCK_TOKENS = frozenset(
    {
        "construction",
        "construct",
        "building",
        "work",
        "works",
        "purchase",
        "purchasing",
        "provide",
        "providing",
        "provision",
        "development",
        "develop",
        "repair",
        "renovation",
        "improvement",
        "new",
        "old",
        "na",
        "mp",
        "ws",
        "scheme",
        "under",
        "including",
        "various",
        "etc",
        "any",
        "other",
    }
)

FORBIDDEN_MODEL_INPUT_COLUMNS = frozenset(COST_FORBIDDEN_MODEL_INPUT_COLUMNS)

SIGNAL_SEPARATION_NOTE = (
    "This signal is Potential Overlap / Potential Duplicate: multi-signal "
    "similarity of recorded works. It is not Investigation Priority and is "
    "not a legal finding."
)

REAL_LIMITATION_NOTE = (
    "The real extract has work text, category, constituency, allocation, "
    "recommendation date, and sparse place text. It does not contain official "
    "work IDs, verified district, vendor, verified expenditure, GPS, sanction "
    "date, or completion date. Geographic evidence is reported unavailable "
    "when place text and coordinates are absent."
)

HYBRID_TEST_NOTE = (
    "HYBRID/TEST: synthetic coordinates are used for controlled GPS-proximity "
    "testing only. They are not official MPLADS GPS and must not be cited as "
    "real location measurements."
)

GPS_UNAVAILABLE_NOTE = (
    "Geographic evidence unavailable: the real extract has no GPS coordinates "
    "and place text is missing or insufficient on one or both works."
)

__all__ = [
    "AMOUNT_SIMILAR_MIN",
    "DATE_CANDIDATE_WINDOW_DAYS",
    "DATE_DECAY_DAYS",
    "DATE_PROXIMATE_DAYS",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "EVIDENCE_TYPE",
    "FLAG_SCORE_THRESHOLD",
    "FORBIDDEN_MODEL_INPUT_COLUMNS",
    "GEO_CELL_DEGREES",
    "GPS_PROXIMITY_M",
    "GPS_UNAVAILABLE_NOTE",
    "HASHED_EMBEDDER_NAME",
    "HASHED_EMBEDDING_DIM",
    "HYBRID_GPS_CONFIDENCE_CAP",
    "HYBRID_TEST_NOTE",
    "LOCATION_SIMILAR_MIN",
    "MAX_CANDIDATES_PER_SUBJECT",
    "MAX_DISPLAY_MATCHES",
    "MAX_FULL_BLOCK_SIZE",
    "MIN_SUPPORTING_FOR_DUPLICATE",
    "MISSING_DESCRIPTION_CONFIDENCE",
    "OVERALL_OVERLAP_MIN",
    "REAL_CONFIDENCE_CAP",
    "REAL_LIMITATION_NOTE",
    "SEMANTIC_CANDIDATE_MIN",
    "SEMANTIC_HIGH",
    "SEMANTIC_NEAR_DUPLICATE",
    "SEMANTIC_OVERLAP_MIN",
    "SENTENCE_TRANSFORMER_MODEL",
    "SIGNAL_KIND",
    "SIGNAL_SEPARATION_NOTE",
    "WEAK_BLOCK_TOKENS",
    "WEIGHT_AMOUNT",
    "WEIGHT_CATEGORY",
    "WEIGHT_CONSTITUENCY",
    "WEIGHT_DATE",
    "WEIGHT_GPS",
    "WEIGHT_LOCATION",
    "WEIGHT_SEMANTIC",
]
