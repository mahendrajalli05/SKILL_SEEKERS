"""Relationship Graph V1 constants.

Independent intelligence/evidence engine. Does not modify Cost, Time,
Overlap, Compliance, Evidence Object scoring, or Risk Fusion V1.1.
Does not assign Investigation Priority and does not conclude fraud.
"""

from __future__ import annotations

from app.engines.cost.constants import (
    FORBIDDEN_MODEL_INPUT_COLUMNS as COST_FORBIDDEN_MODEL_INPUT_COLUMNS,
)
from app.engines.overlap.constants import AMOUNT_SIMILAR_MIN, DATE_PROXIMATE_DAYS

ENGINE_NAME = "graph"
ENGINE_VERSION = "relationship-graph-v1"
EVIDENCE_TYPE = "relationship_graph"
SIGNAL_KIND = "relationship_graph"

# Candidate / neighborhood caps. Not an all-pairs 56,138-node graph.
MAX_CLUSTER_PEERS = 40
MAX_SIMILAR_EDGES = 50
MAX_DISPLAY_RELATIONSHIPS = 40
MAX_DISPLAY_NODES = 80

# Relationship attributes reused from Overlap Intelligence V1.
CLOSE_DATE_DAYS = 60
AMOUNT_SIMILAR_THRESHOLD = AMOUNT_SIMILAR_MIN  # 0.80
OVERLAP_DATE_PROXIMATE_DAYS = DATE_PROXIMATE_DAYS  # 45; graph "close dates" uses 60

# Finding thresholds. High degree is not automatically a pattern of interest.
PATTERN_MIN_SIMILAR = 3
PATTERN_MIN_SAME_CONSTITUENCY = 3
PATTERN_MIN_SAME_IDA = 2
PATTERN_MIN_CLOSE_DATES = 2
PATTERN_EXAMPLE_SIMILAR = 6
PATTERN_EXAMPLE_SAME_CONSTITUENCY = 5
PATTERN_EXAMPLE_SAME_IDA = 4
HIGH_CONNECTIVITY_MIN_SIMILAR = 5
HIGH_CONNECTIVITY_MIN_CLUSTER = 15

REAL_CONFIDENCE_CAP = 64
HYBRID_CONFIDENCE_CAP = 70
INSUFFICIENT_CONFIDENCE = 16
ISOLATED_CONFIDENCE = 28

FORBIDDEN_MODEL_INPUT_COLUMNS = frozenset(COST_FORBIDDEN_MODEL_INPUT_COLUMNS)

# Fields the real extract does not contain. Never stored on graph records.
FABRICATED_GRAPH_FIELDS = frozenset(
    {
        "latitude",
        "longitude",
        "gps",
        "vendor",
        "vendor_name",
        "district",
        "implementing_district",
        "expenditure_amount",
        "sanctioned_amount",
        "sanction_date",
        "completion_date",
        "date_of_completion",
        "unique_work_number",
        "official_work_id",
        "scenario_type",
        "demo_case_id",
        "mixed_signals",
        "anomaly_notes",
        "overlap_group_id",
        "coordinate_source",
    }
)

SIGNAL_SEPARATION_NOTE = (
    "This signal is Relationship Graph connectivity: observed entity links "
    "and Overlap Intelligence similarity. A large number of connections is "
    "not automatically a pattern of interest. It is not Investigation Priority "
    "and is not a legal finding."
)

REAL_LIMITATION_NOTE = (
    "The real extract has MP name, work description, category, state, "
    "constituency, IDA, allocation, and recommendation date. It does not contain "
    "official work IDs, verified district, vendor, verified expenditure, GPS, "
    "sanction date, or completion date. Those fields are not graph inputs."
)

HYBRID_TEST_NOTE = (
    "HYBRID/TEST: synthetic GPS may support Overlap SIMILAR_TO edges for "
    "controlled evaluation only. GPS is not a REAL graph node or edge type."
)

GOVERNANCE_NOTE = (
    "Relationship findings are investigation aids. They are not a legal "
    "finding. AI recommends. Authorized officers decide."
)

__all__ = [
    "AMOUNT_SIMILAR_THRESHOLD",
    "CLOSE_DATE_DAYS",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "EVIDENCE_TYPE",
    "FABRICATED_GRAPH_FIELDS",
    "FORBIDDEN_MODEL_INPUT_COLUMNS",
    "GOVERNANCE_NOTE",
    "HIGH_CONNECTIVITY_MIN_CLUSTER",
    "HIGH_CONNECTIVITY_MIN_SIMILAR",
    "HYBRID_CONFIDENCE_CAP",
    "HYBRID_TEST_NOTE",
    "INSUFFICIENT_CONFIDENCE",
    "ISOLATED_CONFIDENCE",
    "MAX_CLUSTER_PEERS",
    "MAX_DISPLAY_NODES",
    "MAX_DISPLAY_RELATIONSHIPS",
    "MAX_SIMILAR_EDGES",
    "OVERLAP_DATE_PROXIMATE_DAYS",
    "PATTERN_EXAMPLE_SAME_CONSTITUENCY",
    "PATTERN_EXAMPLE_SAME_IDA",
    "PATTERN_EXAMPLE_SIMILAR",
    "PATTERN_MIN_CLOSE_DATES",
    "PATTERN_MIN_SAME_CONSTITUENCY",
    "PATTERN_MIN_SAME_IDA",
    "PATTERN_MIN_SIMILAR",
    "REAL_CONFIDENCE_CAP",
    "REAL_LIMITATION_NOTE",
    "SIGNAL_KIND",
    "SIGNAL_SEPARATION_NOTE",
]
