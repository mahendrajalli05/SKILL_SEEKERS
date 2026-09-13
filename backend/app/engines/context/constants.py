"""Real Contextual Data Enrichment V1 constants.

External public context only. Does not change Cost V1.1, Need & Impact V1,
Risk Fusion V1.1, or Risk Fusion V2 scoring.
"""

from __future__ import annotations

ENGINE_NAME = "context"
ENGINE_VERSION = "contextual-data-enrichment-v1"

GOVERNANCE_NOTE = (
    "External contextual indicators are supporting context only. "
    "They are not project-specific facts, not expenditure, not beneficiary counts, "
    "and not a legal finding. Absence of a value is not treated as zero. "
    "AI recommends. Authorized officers decide."
)

STATUS_AVAILABLE = "AVAILABLE"
STATUS_UNAVAILABLE = "UNAVAILABLE"
STATUS_INCONCLUSIVE = "INCONCLUSIVE"

FAILURE_SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
FAILURE_TIMEOUT = "TIMEOUT"
FAILURE_MALFORMED_SOURCE = "MALFORMED_SOURCE"
FAILURE_UNSUPPORTED_GEOGRAPHY = "UNSUPPORTED_GEOGRAPHY"
FAILURE_MISSING_GEOGRAPHY = "MISSING_GEOGRAPHY"
FAILURE_MISSING_VALUE = "MISSING_VALUE"
FAILURE_INCOMPATIBLE_UNIT = "INCOMPATIBLE_UNIT"
FAILURE_STALE_DATASET = "STALE_DATASET"
FAILURE_AMBIGUOUS_VERSION = "AMBIGUOUS_SOURCE_VERSION"
FAILURE_INVALID_TRANSFORMATION = "INVALID_TRANSFORMATION"
FAILURE_UNAVAILABLE_INDICATOR = "UNAVAILABLE_INDICATOR"
FAILURE_REQUIRES_CONFIGURATION = "SOURCE_UNAVAILABLE_REQUIRES_CONFIGURATION"

GEO_STATE = "STATE"
GEO_DISTRICT = "DISTRICT"
GEO_CONSTITUENCY = "CONSTITUENCY"
GEO_BLOCK = "BLOCK"
GEO_LOCALITY = "LOCALITY"
GEOGRAPHIC_LEVELS = (GEO_STATE, GEO_DISTRICT, GEO_CONSTITUENCY, GEO_BLOCK, GEO_LOCALITY)

KIND_OBSERVED_EXTERNAL = "OBSERVED_EXTERNAL_INDICATOR"
KIND_DERIVED_CONTEXT = "DERIVED_CONTEXT"
KIND_PROJECT_FACT = "PROJECT_SPECIFIC_FACT"

INDICATOR_STATE_POPULATION = "state_population"
INDICATOR_REFERENCE_COST = "reference_unit_rate"
INDICATOR_INFRASTRUCTURE = "infrastructure_availability"
INDICATOR_HOUSEHOLD_ELECTRICITY = "household_electricity_pct"
INDICATOR_DRINKING_WATER = "improved_drinking_water_pct"
INDICATOR_SANITATION = "improved_sanitation_pct"

ALLOCATION_UNIT = "unspecified_allocation_amount"
EXPENDITURE_UNIT = "project_expenditure"

NEW_PROJECT_ASSESSMENT = "NEW_PROJECT_ASSESSMENT"
NEW_PROJECT_ID = 0
NEW_INTERNAL_ID = "new-project-assessment"

POPULATION_SOURCE_ID = "mohfw_ncp_population_projections_2011_2036"
HYBRID_COST_SOURCE_ID = "hybrid_reference_cost_test"
CPWD_SOURCE_ID = "cpwd_delhi_schedule_of_rates"
AP_SOR_SOURCE_ID = "ap_pwd_schedule_of_rates"
DATA_GOV_SOURCE_ID = "data_gov_in_ckan_api"
NFHS_SOURCE_ID = "nfhs5_state_household_amenities"
CENSUS_DISTRICT_SOURCE_ID = "census_2011_pca_district"

# Nearest published projection year may be used when the absolute gap is
# at most 2 years (half of the 5-year table step). Larger gaps stay INCONCLUSIVE
# for contemporaneous matching; the observed series value may still be shown.
NEAREST_YEAR_MAX_GAP = 2
PROJECTION_YEARS = (2011, 2016, 2021, 2026, 2031, 2036)

# Documented numeric bounds from Table-21 (Lakshadweep 64,000 to Uttar Pradesh
# 258,990,000 in the published thousands×1000 series) with a conservative margin.
POPULATION_MIN_PERSONS = 10_000
POPULATION_MAX_PERSONS = 400_000_000

REAL_CONFIDENCE = 0.82
NEAREST_YEAR_CONFIDENCE = 0.70
INCONCLUSIVE_CONFIDENCE = 0.22
UNAVAILABLE_CONFIDENCE = 0.12
HYBRID_FIXTURE_CONFIDENCE = 0.40
SYNTHETIC_CONFIDENCE = 0.30

REGISTRY_RELATIVE = "data/external/sources/registry.json"

NON_GEOGRAPHIC_CONSTITUENCY_TOKENS = (
    "sitting rajya sabha",
    "nominated rajya sabha",
    "rajya sabha",
    "nominated",
)

FORBIDDEN_OUTPUT_TERMS = (
    "fraud",
    "fraudulent",
    "fraud probability",
    "wrongdoing probability",
    "corruption",
    "guilty",
)

LIMITATIONS = (
    GOVERNANCE_NOTE,
    "State population is an external statistical indicator, not a project beneficiary count.",
    "Official CPWD / AP PWD unit rates were not available as a verified machine-readable public extract.",
    "NFHS-5 and Census 2011 district amenities were not bundled as verified structured extracts.",
    "District is not fabricated from IDA text or constituency names.",
    "MPLADS allocation unit is unspecified in the extract; it is not a unit rate.",
    "Project expenditure is unavailable in the current real extract.",
    "Contextual evidence is not fused into Investigation Priority.",
    "Need & Impact V1 formula is unchanged; missing need inputs remain INCONCLUSIVE rather than zero.",
    "Cost Intelligence V1.1 allocation-vs-peers score is unchanged by external reference rates.",
)
