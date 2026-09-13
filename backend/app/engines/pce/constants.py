"""Plan–Claim–Evidence V1 constants.

Deterministic consistency checks only. Does not conclude fraud, does not
invent unit rates, and does not change Cost/Time/Overlap/Compliance/Fusion.
"""

from __future__ import annotations

ENGINE_NAME = "pce"
ENGINE_VERSION = "plan-claim-evidence-v1"
SIGNAL_TYPE = "plan_claim_evidence"

# Relative difference above this value is a MISMATCH when both values exist.
# 19 lakh vs 20 lakh (5%) is CONSISTENT. 800 vs 2,000 sq.ft (60%) is a MISMATCH.
RELATIVE_MISMATCH_THRESHOLD = 0.10

ALLOWED_DOCUMENT_TYPES = frozenset(
    {
        "pdf",
        "document",
        "blueprint",
        "boq",
        "image",
        "photo",
        "supporting_document",
        "inspection",
        "citizen",
        "metadata",
        "gps",
        "timestamp",
    }
)

IMAGE_DOCUMENT_TYPES = frozenset({"image", "photo"})

COMPLETION_TOKENS = frozenset(
    {
        "completed",
        "complete",
        "100",
        "100%",
        "fully completed",
        "work completed",
        "finished",
    }
)

UNAVAILABLE_DIMENSIONS_REASON = (
    "Dimensions/quantity are not present in the current public MPLADS extract "
    "and were not supplied on the recorded plan."
)
UNAVAILABLE_EXPENDITURE_REASON = (
    "Expenditure is not present in the current public MPLADS extract and was "
    "not supplied on the recorded claim."
)
NO_UNIT_RATES_REASON = (
    "Unit rates and material prices are not available. Quantity-to-cost "
    "conversion was not performed."
)
GOVERNANCE_NOTE = (
    "Plan–Claim–Evidence compares recorded plan, claim, and evidence fields. "
    "Results are CONSISTENT, MISMATCH, or INCONCLUSIVE. This is not a legal "
    "finding of wrongdoing. AI recommends. Authorized officers decide."
)

# Local verification confidence caps. Not fused Investigation Priority.
REAL_CONFIDENCE_CAP = 0.90
HYBRID_CONFIDENCE_CAP = 0.72
SYNTHETIC_CONFIDENCE_CAP = 0.55
