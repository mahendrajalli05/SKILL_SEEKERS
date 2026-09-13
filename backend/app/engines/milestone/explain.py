"""Milestone Advisor V1 explanations.

Identifies supporting, conflicting, and missing evidence plus intelligence
signals. Never uses fraud wording and never implies a payment release.
"""

from __future__ import annotations

from app.engines.milestone.assess import HOLD, INCONCLUSIVE, INSPECT, PROCEED
from app.engines.milestone.constants import GOVERNANCE_NOTE, NO_PAYMENT_NOTE
from app.engines.milestone.types import AssessmentInputs, AssessmentResult

_CONCERN_TEXT = {
    "pce_mismatch": "Plan → Claim → Evidence reported a mismatch for assessable fields.",
    "geo_mismatch": "Geospatial consistency reported a significant location inconsistency.",
    "image_reuse": "Image evidence reported exact duplicate or potential visual reuse.",
    "expenditure_inconsistency": "Claimed expenditure is inconsistent with the planned milestone amount or recorded evidence amount.",
    "progress_inconsistency": "Claimed progress is inconsistent with evidence-supported progress.",
    "schedule_mismatch": "Time Intelligence reported a schedule mismatch for this work.",
    "cost_flagged": "Cost Intelligence is flagged as a contributing investigation signal.",
    "compliance_flagged": "Compliance findings are flagged for review.",
    "overlap_flagged": "Overlap Intelligence is flagged as a contributing investigation signal.",
}


def build_why(
    inputs: AssessmentInputs,
    result: AssessmentResult,
    *,
    supporting: list[str] | None = None,
    missing: list[str] | None = None,
    signals: list[str] | None = None,
) -> AssessmentResult:
    supporting_evidence = list(supporting or [])
    missing_evidence = list(missing or [])
    intelligence = list(signals or [])
    conflicting = [_CONCERN_TEXT[key] for key in result.independent_concerns if key in _CONCERN_TEXT]

    if inputs.has_claim and inputs.has_required_evidence and not supporting_evidence:
        supporting_evidence.append("A milestone claim is recorded together with supporting attachments.")
    if inputs.pce_result == "CONSISTENT":
        supporting_evidence.append("Plan → Claim → Evidence is CONSISTENT for assessable fields.")
    if not inputs.has_required_evidence and "supporting attachments" not in " ".join(missing_evidence).casefold():
        missing_evidence.append("Required supporting evidence (document or progress image) is missing.")
    if not inputs.has_claim and "milestone claim" not in " ".join(missing_evidence).casefold():
        missing_evidence.append("No milestone claim is recorded.")
    if inputs.pce_result in {None, "INCONCLUSIVE"} and not conflicting:
        missing_evidence.append("Insufficient comparable plan, claim, or evidence values for a firm consistency result.")

    if result.recommendation == PROCEED:
        lead = (
            "Recommendation is PROCEED because the milestone claim is supported, "
            "required evidence is present, and no unresolved critical mismatch was identified."
        )
    elif result.recommendation == HOLD:
        lead = (
            "Recommendation is HOLD because an important mismatch exists, required "
            "evidence is missing, or expenditure/progress is inconsistent."
        )
    elif result.recommendation == INSPECT:
        lead = (
            "Recommendation is INSPECT because of strong conflicting evidence, "
            "location inconsistency, potential reused evidence, or multiple independent concerns."
        )
    else:
        lead = (
            "Recommendation is INCONCLUSIVE because the available plan, claim, and "
            "evidence are not sufficient for a meaningful readiness recommendation."
        )

    result.supporting_evidence = supporting_evidence
    result.conflicting_evidence = conflicting
    result.missing_evidence = missing_evidence
    result.intelligence_signals = intelligence
    result.explanation = (
        f"{lead} {GOVERNANCE_NOTE} {NO_PAYMENT_NOTE}"
    )
    return result
