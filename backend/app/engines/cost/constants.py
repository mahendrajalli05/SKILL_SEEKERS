"""Cost Intelligence V1.1 constants.

Allocation-vs-peers only. No Isolation Forest, material-price adjustment,
expenditure comparison, or fused Investigation Priority.
"""

from __future__ import annotations

ENGINE_NAME = "cost"
ENGINE_VERSION = "cost-peer-v1.1"
EVIDENCE_TYPE = "allocation_cost_anomaly"
SIGNAL_KIND = "allocation_cost_anomaly"

# Minimum comparable works required before an anomaly score is produced.
MIN_PEER_COUNT = 5

# How many nearest peers to return as display comparables.
MAX_DISPLAY_COMPARABLES = 10

# Review flag on the mapped 0–100 score. Not a legal or business risk label.
# Equals |modified z| = 2.1 on the log-MAD scale (100 maps to |z| = 3.5).
FLAG_SCORE_THRESHOLD = 60

# Iglewicz-Hoaglin modified z-score that maps to Cost Anomaly 100.
MODIFIED_Z_REFERENCE = 3.5

# When log-MAD is 0, a 4× (or 1/4×) ratio vs median maps to score 100.
IDENTICAL_PEER_RATIO_FOR_MAX = 4.0

LOOSE_WORK_TYPE_SIMILARITY = 0.35

# Jaccard of observed title tokens for "precise" work-type grouping.
PRECISE_WORK_TYPE_SIMILARITY = 0.50

ANDHRA_PRADESH_CANONICAL = "Andhra Pradesh"

AMOUNT_UNIT_NOTE = (
    "Source amount unit is unspecified. Values are compared as recorded "
    "allocation amounts, not as a labelled rupee series."
)

SIGNAL_SEPARATION_NOTE = (
    "This signal is Allocation Cost Anomaly: recorded allocation versus "
    "comparable works. It is not an expenditure anomaly, over-billing, "
    "physical-quantity mismatch, or a legal finding."
)

SCOPE_CONSTITUENCY_CATEGORY_WORK_TYPE = "constituency_category_work_type"
SCOPE_CONSTITUENCY_CATEGORY = "constituency_category"
SCOPE_STATE_CATEGORY_WORK_TYPE = "state_category_work_type"
SCOPE_STATE_BROADER_WORK_TYPE = "state_broader_work_type"

SCOPE_ORDER = (
    SCOPE_CONSTITUENCY_CATEGORY_WORK_TYPE,
    SCOPE_CONSTITUENCY_CATEGORY,
    SCOPE_STATE_CATEGORY_WORK_TYPE,
    SCOPE_STATE_BROADER_WORK_TYPE,
)

SCOPE_LABELS = {
    SCOPE_CONSTITUENCY_CATEGORY_WORK_TYPE: (
        "same geographic constituency, same category, and similar work title"
    ),
    SCOPE_CONSTITUENCY_CATEGORY: (
        "same geographic constituency and broader category"
    ),
    SCOPE_STATE_CATEGORY_WORK_TYPE: (
        "same Andhra Pradesh state, same category, and similar work title"
    ),
    SCOPE_STATE_BROADER_WORK_TYPE: (
        "same Andhra Pradesh state and broader comparable work title"
    ),
}

SCOPE_CONFIDENCE_BASE = {
    SCOPE_CONSTITUENCY_CATEGORY_WORK_TYPE: 55,
    SCOPE_CONSTITUENCY_CATEGORY: 32,
    SCOPE_STATE_CATEGORY_WORK_TYPE: 35,
    SCOPE_STATE_BROADER_WORK_TYPE: 25,
}

# Held-out HYBRID evaluation labels only. Never used as model inputs.
FORBIDDEN_MODEL_INPUT_COLUMNS = frozenset(
    {
        "scenario_type",
        "demo_case_id",
        "mixed_signals",
        "anomaly_notes",
        "overlap_group_id",
        "coordinate_source",
        "synthetic_disclaimer",
        "record_mode",
        "enrichment_source",
        "synthetic_as_of_date",
        "synthetic_record_id",
    }
)
