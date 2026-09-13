"""ML Training & Inference V1 constants.

This layer does not replace Cost V1.1, Time V1, Overlap V1, Compliance,
or Risk Fusion. It does not produce a fraud probability.
"""

from __future__ import annotations

from app.engines.cost.constants import FORBIDDEN_MODEL_INPUT_COLUMNS as COST_FORBIDDEN

RANDOM_SEED = 26102
FEATURE_SCHEMA_COST = "cost-features-v1"
FEATURE_SCHEMA_TIME = "time-features-v1"
COST_MODEL_NAME = "cost-anomaly-v1"
TIME_MODEL_NAME = "time-anomaly-v1"
COST_MODEL_TYPE = "IsolationForest"
TIME_MODEL_TYPE = "IsolationForest"
COST_ENGINE_NAME = "ml-cost-anomaly"
TIME_ENGINE_NAME = "ml-time-anomaly"
MODEL_LAYER_VERSION = "ml-training-inference-v1"

FORBIDDEN_MODEL_INPUT_COLUMNS = frozenset(COST_FORBIDDEN)

REQUIRED_COST_FIELDS = ("allocation_amount", "category")
OPTIONAL_COST_FIELDS = (
    "state",
    "constituency",
    "work_description",
    "recommendation_date",
    "status",
    "house",
)

GOVERNANCE_NOTE = (
    "ML anomaly scores are unsupervised distributional signals. "
    "They are not a fraud probability, legal finding, sanction, or payment release. "
    "Cost Intelligence V1.1 remains the authoritative interpretable peer baseline."
)

TIME_LIMITATION = (
    "No REAL MPLADS execution start or completion dates exist in the extract. "
    "The time ML artifact is a HYBRID_TEST architecture check only. "
    "It did not learn real MPLADS historical delay rates."
)

OVERLAP_NOTE = (
    "Overlap Intelligence V1 remains the production similarity signal. "
    "No duplicate overlap model is trained."
)

COMPLIANCE_NOTE = (
    "Compliance remains a deterministic rule engine. It is not replaced by ML."
)

RISK_NOTE = (
    "Risk Fusion V2 remains the primary evidence-fusion layer. "
    "ML scores are optional signals and are not fused into Investigation Priority in this slice."
)

NEW_PROJECT_ASSESSMENT = "NEW_PROJECT_ASSESSMENT"
PROJECT_STORED_EVIDENCE = "PROJECT_STORED_EVIDENCE"
ML_EVIDENCE_ENGINE = "ml"
ML_EVIDENCE_LAYER = "ml-evidence-integration-v1"

NEW_PROJECT_RISK_REASON = (
    "Investigation Priority requires stored Evidence Objects for an existing project. "
    "A new project that has not been recorded has no historical evidence to fuse."
)

NEW_PROJECT_EVIDENCE_NOTE = (
    "NEW_PROJECT_ASSESSMENT is a proposal-time ML signal. It is not stored project "
    "evidence, not historical Evidence Object history, and not fused into "
    "Investigation Priority."
)

ML_EVIDENCE_NOTE = (
    "ML anomaly score is an unsupervised distributional rank versus the training "
    "set. It measures unusualness relative to the model's reference distribution "
    "only and is not fused into Investigation Priority or Evidence Confidence. "
    "The model cannot determine legal wrongdoing."
)

AMOUNT_UNIT_NOTE = (
    "Source amount unit is unspecified. Values are compared as recorded allocation amounts."
)

DEFAULT_CONTAMINATION = 0.05
DEFAULT_N_ESTIMATORS = 100
TFIDF_MAX_FEATURES = 256
TFIDF_MIN_DF = 3
SVD_COMPONENTS = 8
TRAIN_FRACTION = 0.70
VAL_FRACTION = 0.15
TEST_FRACTION = 0.15
CONTRIBUTION_TOP_K = 5
ANOMALY_SCORE_FLAG = 80
