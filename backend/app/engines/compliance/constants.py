"""Compliance Engine V1 constants.

Deterministic MPLADS rule engine. Not an ML model. Does not assign fused
Investigation Priority and does not conclude a legal finding.
HYBRID scenario labels are never rule inputs.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from app.config import REPO_ROOT
from app.engines.cost.constants import (
    FORBIDDEN_MODEL_INPUT_COLUMNS as COST_FORBIDDEN_MODEL_INPUT_COLUMNS,
)

ENGINE_NAME = "compliance"
ENGINE_VERSION = "compliance-rules-v1"
EVIDENCE_TYPE = "mplads_compliance"
SIGNAL_KIND = "mplads_compliance"

DEFAULT_RULES_PATH = REPO_ROOT / "rules" / "mplads_compliance_v1.json"

# Documented observation clock for REAL vintage. Matches extract download date.
# Not a sanction date and not used to invent execution duration.
REAL_OBSERVATION_DATE = date(2026, 9, 9)

DEFAULT_HYBRID_AS_OF_DATE = date(2024, 6, 30)

FORBIDDEN_MODEL_INPUT_COLUMNS = frozenset(COST_FORBIDDEN_MODEL_INPUT_COLUMNS)

ALLOWED_SEVERITIES = frozenset({"info", "watch", "attention"})
ALLOWED_OPERATORS = frozenset(
    {
        "date_diff_gt",
        "duration_gt",
        "numeric_gt",
        "numeric_lt",
        "no_recorded_spend_after_days",
        "boolean_true",
        "boolean_true_not_triggered",
        "blank_triggers",
        "repair_admissible",
    }
)

SEVERITY_RANK = {
    "info": 0,
    "watch": 1,
    "attention": 2,
}

RULE_ID_PATTERN = r"^R\d{3}$"

SIGNAL_SEPARATION_NOTE = (
    "This signal is MPLADS guideline-rule evaluation. It is not Investigation "
    "Priority and is not a legal finding."
)

HYBRID_TEST_NOTE = (
    "HYBRID/TEST: synthetic execution and expenditure fields are used for "
    "controlled testing only. They are not official MPLADS values and must "
    "not be cited as real government findings."
)

REAL_LIMITATION_NOTE = (
    "The real extract has recommendation date, observed status, IDA text, "
    "allocation, and related recorded fields. It does not contain verified "
    "district, vendor, GPS, verified expenditure, verified sanction date, "
    "verified completion date, or a labelled amount unit."
)

UNAVAILABLE_AMOUNT_UNIT_NOTE = (
    "Source amount unit is unspecified. Rupee ceilings from the Guidelines "
    "are not applied to allocation_amount."
)


def rules_path(override: Path | None = None) -> Path:
    return override or DEFAULT_RULES_PATH


__all__ = [
    "ALLOWED_OPERATORS",
    "ALLOWED_SEVERITIES",
    "DEFAULT_HYBRID_AS_OF_DATE",
    "DEFAULT_RULES_PATH",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "EVIDENCE_TYPE",
    "FORBIDDEN_MODEL_INPUT_COLUMNS",
    "HYBRID_TEST_NOTE",
    "REAL_LIMITATION_NOTE",
    "REAL_OBSERVATION_DATE",
    "RULE_ID_PATTERN",
    "SEVERITY_RANK",
    "SIGNAL_KIND",
    "SIGNAL_SEPARATION_NOTE",
    "UNAVAILABLE_AMOUNT_UNIT_NOTE",
    "rules_path",
]
