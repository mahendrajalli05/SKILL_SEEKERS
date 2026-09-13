"""Shared Evidence Object V1 constants.

This layer stores auditable engine findings. It does not run Risk Fusion
and does not assign Investigation Priority.
"""

from __future__ import annotations

from app.domain.enums import EvidenceDisposition, EvidenceStatus, SignalType
from app.engines.cost.constants import (
    FORBIDDEN_MODEL_INPUT_COLUMNS as COST_FORBIDDEN_MODEL_INPUT_COLUMNS,
)

LAYER_NAME = "evidence"
LAYER_VERSION = "evidence-object-v1"

HYBRID_ENRICHMENT_RELATIVE_PATH = "data/synthetic/sarvsakshi_synthetic_enrichment.csv"
HYBRID_ENRICHMENT_SHA256 = "d1de1b151cd115f9e4c0ae291f585481527a1f02846cb593c66d6c819895f4f1"

FORBIDDEN_EVIDENCE_INPUT_COLUMNS = frozenset(COST_FORBIDDEN_MODEL_INPUT_COLUMNS)

FRAUD_CLAIM_PATTERN = r"\bfraud(ulent)?\b"

REAL_PROVENANCE_NOTE = (
    "real MPLADS project records from the cleaned work-level extract. "
    "internal_project_id is a SARVSAKSHI surrogate, not an official MPLADS work ID."
)

HYBRID_PROVENANCE_NOTE = (
    "HYBRID/TEST: observed MPLADS fields plus synthetic enrichment from "
    f"{HYBRID_ENRICHMENT_RELATIVE_PATH}. Synthetic fields are not official "
    "MPLADS values and must not be cited as government measurements."
)

SYNTHETIC_PROVENANCE_NOTE = (
    "SYNTHETIC test record; not a government project. For controlled testing only."
)

FUTURE_SIGNAL_TYPES = (
    SignalType.RELATIONSHIP_GRAPH,
    SignalType.DOCUMENT,
    SignalType.IMAGE,
    SignalType.IMAGE_EXACT_DUPLICATE,
    SignalType.IMAGE_POTENTIAL_REUSE,
    SignalType.IMAGE_METADATA,
    SignalType.IMAGE_QUALITY,
    SignalType.IMAGE_FORENSIC_MANIPULATION,
    SignalType.IMAGE_FORENSIC_AI_GENERATION,
    SignalType.IMAGE_FORENSIC_METADATA,
    SignalType.IMAGE_FORENSIC_INCONCLUSIVE,
    SignalType.GEOSPATIAL,
    SignalType.GEOSPATIAL_LOCATION_CONSISTENCY,
    SignalType.GEOSPATIAL_LOCATION_MISMATCH,
    SignalType.GEOSPATIAL_INCONCLUSIVE,
    SignalType.CITIZEN,
    SignalType.CITIZEN_LOCATION,
    SignalType.CITIZEN_FEEDBACK,
    SignalType.CITIZEN_IMAGE,
    SignalType.CITIZEN_AGGREGATE,
    SignalType.MILESTONE,
    SignalType.NEED_ASSESSMENT,
    SignalType.IMPACT_ASSESSMENT,
    SignalType.PRIORITY_ASSESSMENT,
    SignalType.SATELLITE,
    SignalType.SATELLITE_AVAILABILITY,
    SignalType.SATELLITE_LOCATION,
    SignalType.SATELLITE_CHANGE,
    SignalType.SATELLITE_TEMPORAL,
    SignalType.SATELLITE_INCONCLUSIVE,
    SignalType.ML_ANOMALY_SIGNAL,
    SignalType.REFERENCE_COST_CONTEXT,
    SignalType.DEVELOPMENT_NEED_CONTEXT,
    SignalType.INFRASTRUCTURE_CONTEXT,
    SignalType.CONTEXT_UNAVAILABLE,
    SignalType.CONTEXT_INCONCLUSIVE,
)

DISPOSITION_TO_STATUS = {
    EvidenceDisposition.WHY_FLAGGED: EvidenceStatus.MISMATCH,
    EvidenceDisposition.WHY_NOT_FLAGGED: EvidenceStatus.CONSISTENT,
    EvidenceDisposition.INCONCLUSIVE: EvidenceStatus.INCONCLUSIVE,
    EvidenceDisposition.NOT_ASSESSABLE: EvidenceStatus.NOT_ASSESSABLE,
}

OBSERVATION_FACT_KEYS = frozenset(
    {
        "actual_amount",
        "allocation_amount",
        "observed_category",
        "observed_status",
        "recommended_date",
        "ida",
        "constituency",
        "source_work",
        "work_description",
        "lifecycle_stage",
        "house",
        "planned_duration_days",
        "actual_duration_days",
        "elapsed_duration_days",
        "physical_progress_percent",
        "planned_start_date",
        "planned_completion_date",
        "actual_start_date",
        "actual_completion_date",
        "as_of_date",
    }
)
