"""Time Intelligence V1 constants.

Dual mode:
- REAL: recommendation date + observed status only. No fabricated duration.
- HYBRID_TEST: synthetic planned/actual dates and progress for controlled tests.

Does not assign fused Investigation Priority. Does not use HYBRID scenario
labels as model inputs.
"""

from __future__ import annotations

from datetime import date

from app.engines.cost.constants import (
    FORBIDDEN_MODEL_INPUT_COLUMNS as COST_FORBIDDEN_MODEL_INPUT_COLUMNS,
)
from app.engines.cost.constants import (
    SCOPE_CONSTITUENCY_CATEGORY,
    SCOPE_CONSTITUENCY_CATEGORY_WORK_TYPE,
    SCOPE_LABELS,
    SCOPE_STATE_BROADER_WORK_TYPE,
    SCOPE_STATE_CATEGORY_WORK_TYPE,
)

ENGINE_NAME = "time"
ENGINE_VERSION = "time-peer-v1"
EVIDENCE_TYPE = "time_anomaly"
SIGNAL_KIND = "time_anomaly"

# Minimum comparable works required before a peer scope is selected.
MIN_PEER_COUNT = 5

MAX_DISPLAY_COMPARABLES = 10

# Review flag on the mapped 0–100 score. Not a legal or business risk label.
FLAG_SCORE_THRESHOLD = 60

# Iglewicz-Hoaglin modified z-score that maps to Time Anomaly 100.
MODIFIED_Z_REFERENCE = 3.5

# Delay equal to planned duration (took twice as long) maps to score 100.
PLAN_DELAY_RATIO_FOR_MAX = 1.0

# Ongoing: 80 percentage-point (time consumed − physical progress) maps to 100.
MISMATCH_POINTS_FOR_MAX = 80.0

ANDHRA_PRADESH_CANONICAL = "Andhra Pradesh"

# Documented observation clock for REAL vintage. Matches extract download date.
# This is not a completion date and is not used to invent execution duration.
REAL_OBSERVATION_DATE = date(2026, 9, 9)

# HYBRID prototype clock. Clock parameter only, not a learned feature.
DEFAULT_HYBRID_AS_OF_DATE = date(2024, 6, 30)

REAL_CONFIDENCE_CAP = 25
HYBRID_CONFIDENCE_CAP = 72

SCOPE_ORDER = (
    SCOPE_CONSTITUENCY_CATEGORY_WORK_TYPE,
    SCOPE_CONSTITUENCY_CATEGORY,
    SCOPE_STATE_CATEGORY_WORK_TYPE,
    SCOPE_STATE_BROADER_WORK_TYPE,
)

SCOPE_CONFIDENCE_BASE = {
    SCOPE_CONSTITUENCY_CATEGORY_WORK_TYPE: 55,
    SCOPE_CONSTITUENCY_CATEGORY: 32,
    SCOPE_STATE_CATEGORY_WORK_TYPE: 35,
    SCOPE_STATE_BROADER_WORK_TYPE: 25,
}

FORBIDDEN_MODEL_INPUT_COLUMNS = frozenset(COST_FORBIDDEN_MODEL_INPUT_COLUMNS)

SIGNAL_SEPARATION_NOTE = (
    "This signal is Time Anomaly: schedule and progress timing versus the plan "
    "and comparable works where available. It is not Investigation Priority "
    "and is not a legal finding."
)

HYBRID_TEST_NOTE = (
    "HYBRID/TEST: synthetic planned/actual dates and progress are used for "
    "controlled testing only. They do not represent actual MPLADS execution "
    "history and must not be cited as real delay statistics."
)

REAL_LIMITATION_NOTE = (
    "The real extract contains recommendation date and observed status only. "
    "It does not contain verified sanction date, start date, completion date, "
    "expenditure, or duration. Duration is not fabricated."
)

CAUSE_NOT_ESTABLISHED = (
    "Delay detected; cause not established from available data."
)

LINEAR_PROGRESS_NOTE = (
    "Expected progress uses a simple linear time-consumed mapping. "
    "It is not a verified construction S-curve or engineering estimate."
)

__all__ = [
    "ANDHRA_PRADESH_CANONICAL",
    "CAUSE_NOT_ESTABLISHED",
    "DEFAULT_HYBRID_AS_OF_DATE",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "EVIDENCE_TYPE",
    "FLAG_SCORE_THRESHOLD",
    "FORBIDDEN_MODEL_INPUT_COLUMNS",
    "HYBRID_CONFIDENCE_CAP",
    "HYBRID_TEST_NOTE",
    "LINEAR_PROGRESS_NOTE",
    "MAX_DISPLAY_COMPARABLES",
    "MIN_PEER_COUNT",
    "MISMATCH_POINTS_FOR_MAX",
    "MODIFIED_Z_REFERENCE",
    "PLAN_DELAY_RATIO_FOR_MAX",
    "REAL_CONFIDENCE_CAP",
    "REAL_LIMITATION_NOTE",
    "REAL_OBSERVATION_DATE",
    "SCOPE_CONFIDENCE_BASE",
    "SCOPE_CONSTITUENCY_CATEGORY",
    "SCOPE_CONSTITUENCY_CATEGORY_WORK_TYPE",
    "SCOPE_LABELS",
    "SCOPE_ORDER",
    "SCOPE_STATE_BROADER_WORK_TYPE",
    "SCOPE_STATE_CATEGORY_WORK_TYPE",
    "SIGNAL_KIND",
    "SIGNAL_SEPARATION_NOTE",
]
