"""Need & Impact / Future Project Prioritization V1 constants.

Decision-support only. Not a funding approval or sanction formula.
Prototype weights are documented and are not official MPLADS weights.
"""

from __future__ import annotations

from datetime import date

ENGINE_NAME = "need"
ENGINE_VERSION = "need-impact-v1"

WEIGHT_NOTE = "Prototype weighting — not an official MPLADS sanction formula."
GOVERNANCE_NOTE = (
    "Priority recommendation only. Authorized officials make final "
    "administrative decisions. Prototype weighting — not an official "
    "MPLADS sanction formula. This is a planning simulation only. "
    "It does not sanction a project, approve funds, or release payments."
)

PRIORITY_RECOMMENDATION_ONLY = (
    "Priority recommendation only. Authorized officials make final "
    "administrative decisions."
)

PLANNING_SIMULATION_NOTE = (
    "PLANNING SIMULATION only. Hypothetical budget ranking does not execute "
    "payments or sanctions."
)

# --- Priority class labels (officer-facing, not a sanction) ---
HIGH_PRIORITY = "HIGH PRIORITY"
MEDIUM_PRIORITY = "MEDIUM PRIORITY"
LOW_PRIORITY = "LOW PRIORITY"
INCONCLUSIVE = "INCONCLUSIVE"

# Priority Score bands on the 0–100 prototype scale.
HIGH_PRIORITY_MIN = 70.0
MEDIUM_PRIORITY_MIN = 40.0

# --- Combined Priority Score weights (sum 1.00) ---
NEED_WEIGHT = 0.45
IMPACT_WEIGHT = 0.40
URGENCY_WEIGHT = 0.15

PRIORITY_WEIGHTS = {
    "need": NEED_WEIGHT,
    "impact": IMPACT_WEIGHT,
    "urgency": URGENCY_WEIGHT,
}

# Need Score component weights (sum 1.00). Unavailable components are
# omitted and remaining weights are renormalized. Historical project count
# and historical funding are intentionally absent.
NEED_COMPONENT_WEIGHTS = {
    "population": 0.30,
    "infrastructure_gap": 0.25,
    "underserved_area": 0.20,
    "disaster_context": 0.25,
}

# Impact Score component weights (sum 1.00).
IMPACT_COMPONENT_WEIGHTS = {
    "beneficiary_count": 0.30,
    "essential_service_relevance": 0.30,
    "community_coverage": 0.20,
    "infrastructure_gap": 0.20,
}

# REAL work-type mapping is Impact only. It is not a census need measure.
ESSENTIAL_SERVICE_HIGH_SCORE = 85.0
ESSENTIAL_SERVICE_MEDIUM_SCORE = 60.0
ESSENTIAL_SERVICE_LOW_SCORE = 25.0

# Prototype beneficiary-count → 0–100 bands. Not official MPLADS bands.
BENEFICIARY_BANDS: tuple[tuple[int, float], ...] = (
    (1, 20.0),
    (100, 40.0),
    (500, 55.0),
    (1_000, 70.0),
    (5_000, 85.0),
    (10_000, 95.0),
)

# Waiting-time urgency for FUTURE/proposed works. Prototype only.
URGENCY_WAITING_BANDS: tuple[tuple[int, float], ...] = (
    (0, 20.0),
    (180, 35.0),
    (365, 55.0),
    (730, 75.0),
)
URGENCY_WAITING_MAX = 88.0
DISASTER_TEXT_URGENCY = 90.0

REAL_AS_OF_DATE = date(2026, 9, 10)

# Evidence Confidence caps (0–1). Census-style inputs are absent in REAL.
REAL_CONFIDENCE_CAP = 0.45
HYBRID_CONFIDENCE_CAP = 0.72
SYNTHETIC_CONFIDENCE_CAP = 0.55
UNAVAILABLE_CONFIDENCE = 0.18
PARTIAL_CONFIDENCE_CAP = 0.35

CRORE_RUPEES = 10_000_000
AMOUNT_UNIT_NOTE = (
    "Requested allocation uses the observed extract amount. The source unit "
    "is unspecified. Budget simulation may treat 1 crore as 10,000,000 of "
    "that same unspecified unit."
)

HYBRID_ENRICHMENT_RELATIVE_PATH = "data/synthetic/need_impact_test_enrichment.json"
HYBRID_ENRICHMENT_LABEL = "TEST/SYNTHETIC"

SYNTHETIC_VALUE_NOTE = (
    "TEST/SYNTHETIC prototype enrichment. Not an official MPLADS, census, "
    "or infrastructure statistic. Do not treat as a government fact."
)

CONTEXT_NOT_NEED_NOTE = (
    "Historical project counts and historical funding are contextual evidence "
    "only. They are not used as a Need Score and do not prove community need. "
    "A constituency is not ranked lower because it has fewer recorded MPLADS works."
)

MP_NOT_GEOGRAPHY_NOTE = (
    "Constituency is the primary geographic context. MP name is not used as "
    "a geographic substitute. District-level information is not fabricated."
)

UNAVAILABLE_NEED_INPUTS = (
    "population",
    "infrastructure_availability",
    "underserved_area_indicators",
    "beneficiary_count",
    "expected_community_coverage",
    "disaster_statistics",
    "census_or_sc_st_composition",
)

FORBIDDEN_OUTPUT_TERMS = (
    "fraud",
    "fraudulent",
    "fraud probability",
    "sanction approved",
    "sanction denied",
)

LIMITATIONS = (
    "The current real MPLADS extract has no verified population, infrastructure-gap, "
    "or beneficiary dataset for every locality.",
    "Unavailable need/impact fields are marked unavailable or INCONCLUSIVE. Values are not invented.",
    "Historical MPLADS work counts are not a proxy for community need.",
    "Historical funding is not used as a Need Score.",
    "Work-type essential-service relevance is a prototype mapping from observed category/description, not a census measure.",
    "Prototype weights are not an official MPLADS sanction formula.",
    "Priority class is a decision-support recommendation, not a funding approval.",
    "Hypothetical budget ranking is a planning simulation only.",
    "SYNTHETIC need/impact enrichment is labelled TEST/SYNTHETIC and is not a government fact.",
)

# Observed-text tokens. Not an official MPLADS sector taxonomy.
ESSENTIAL_HIGH_TOKENS = frozenset(
    {
        "drinking",
        "water",
        "sanitation",
        "toilet",
        "sewer",
        "sewerage",
        "hospital",
        "health",
        "phc",
        "anganwadi",
        "school",
        "education",
        "classroom",
        "ambulance",
        "potable",
    }
)
ESSENTIAL_MEDIUM_TOKENS = frozenset(
    {
        "road",
        "bridge",
        "street",
        "light",
        "electricity",
        "irrigation",
        "drain",
        "drainage",
        "community",
        "hall",
        "park",
        "library",
        "sports",
        "skill",
        "lighting",
        "pathway",
    }
)
ESSENTIAL_LOW_TOKENS = frozenset(
    {
        "statue",
        "beautification",
        "fountain",
        "ornamental",
        "memorial",
        "monument",
    }
)
DISASTER_TOKENS = frozenset(
    {
        "flood",
        "cyclone",
        "drought",
        "earthquake",
        "tsunami",
        "disaster",
        "relief",
        "emergency",
    }
)

HIGH_CATEGORY_TOKENS = frozenset(
    {
        "drinking water",
        "education",
        "health",
        "sanitation",
        "family welfare",
    }
)
MEDIUM_CATEGORY_TOKENS = frozenset(
    {
        "roads",
        "pathways",
        "bridges",
        "electricity",
        "irrigation",
        "sports",
        "animal husbandry",
        "other public",
    }
)
LOW_CATEGORY_TOKENS = frozenset(
    {
        "beautification",
        "statue",
        "monument",
    }
)

MAX_RANK_CANDIDATES = 50
