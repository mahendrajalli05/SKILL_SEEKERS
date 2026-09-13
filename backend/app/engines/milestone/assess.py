"""Deterministic Milestone Advisor V1 recommendation.

Evidence-first. Does not recommend from Investigation Priority alone.
Does not conclude fraud and does not release funds.
"""

from __future__ import annotations

from app.domain.enums import MilestoneRecommendation
from app.engines.milestone.constants import (
    HYBRID_CONFIDENCE_CAP,
    INSUFFICIENT_CONFIDENCE,
    REAL_CONFIDENCE_CAP,
    SYNTHETIC_CONFIDENCE_CAP,
)
from app.engines.milestone.types import AssessmentInputs, AssessmentResult
from app.engines.pce.types import ConsistencyStatus

PROCEED = MilestoneRecommendation.PROCEED.value
HOLD = MilestoneRecommendation.HOLD.value
INSPECT = MilestoneRecommendation.INSPECT.value
INCONCLUSIVE = MilestoneRecommendation.INCONCLUSIVE.value

_PCE_CONSISTENT = ConsistencyStatus.CONSISTENT.value
_PCE_MISMATCH = ConsistencyStatus.MISMATCH.value
_PCE_INCONCLUSIVE = ConsistencyStatus.INCONCLUSIVE.value


def _cap(data_mode: str) -> float:
    mode = data_mode.upper()
    if mode == "HYBRID":
        return HYBRID_CONFIDENCE_CAP
    if mode == "SYNTHETIC":
        return SYNTHETIC_CONFIDENCE_CAP
    return REAL_CONFIDENCE_CAP


def collect_concerns(inputs: AssessmentInputs) -> tuple[list[str], list[str]]:
    milestone: list[str] = []
    intelligence: list[str] = []
    if inputs.pce_result == _PCE_MISMATCH:
        milestone.append("pce_mismatch")
    if inputs.geo_mismatch:
        milestone.append("geo_mismatch")
    if inputs.image_reuse or inputs.exact_duplicate:
        milestone.append("image_reuse")
    if inputs.expenditure_inconsistency:
        milestone.append("expenditure_inconsistency")
    if inputs.progress_inconsistency:
        milestone.append("progress_inconsistency")
    if inputs.schedule_mismatch:
        milestone.append("schedule_mismatch")
    if inputs.cost_flagged:
        intelligence.append("cost_flagged")
    if inputs.compliance_flagged:
        intelligence.append("compliance_flagged")
    if inputs.overlap_flagged:
        intelligence.append("overlap_flagged")
    return milestone, intelligence


def recommend(inputs: AssessmentInputs) -> tuple[str, list[str]]:
    """Return (recommendation, independent_concern keys)."""
    milestone, intelligence = collect_concerns(inputs)
    concerns = [*milestone, *intelligence]
    strong = inputs.geo_mismatch or inputs.image_reuse or inputs.exact_duplicate
    if strong or len(milestone) >= 2 or (milestone and intelligence):
        return INSPECT, concerns
    if inputs.pce_result == _PCE_MISMATCH:
        return HOLD, concerns
    if inputs.has_claim and not inputs.has_required_evidence:
        return HOLD, concerns
    if inputs.expenditure_inconsistency or inputs.progress_inconsistency:
        return HOLD, concerns
    if inputs.schedule_mismatch:
        return HOLD, concerns
    if (
        inputs.has_claim
        and inputs.has_required_evidence
        and inputs.pce_result == _PCE_CONSISTENT
    ):
        return PROCEED, concerns
    return INCONCLUSIVE, concerns


def evidence_status_for(inputs: AssessmentInputs, recommendation: str) -> str:
    if inputs.pce_result == _PCE_MISMATCH:
        return "MISMATCH"
    if not inputs.has_required_evidence:
        return "INSUFFICIENT"
    if inputs.pce_result == _PCE_CONSISTENT:
        return "SUPPORTED"
    if recommendation == INCONCLUSIVE:
        return "INCONCLUSIVE"
    return inputs.pce_result or "INCONCLUSIVE"


def local_confidence(
    inputs: AssessmentInputs,
    recommendation: str,
    *,
    data_mode: str = "REAL",
) -> float:
    cap = _cap(data_mode)
    if recommendation == INCONCLUSIVE or not inputs.has_required_evidence:
        return min(INSUFFICIENT_CONFIDENCE, cap)
    if recommendation == PROCEED:
        return round(min(0.82, cap), 4)
    if recommendation == HOLD:
        return round(min(0.70, cap), 4)
    return round(min(0.62, cap), 4)


def assess(inputs: AssessmentInputs, *, data_mode: str = "REAL") -> AssessmentResult:
    recommendation, concerns = recommend(inputs)
    status = evidence_status_for(inputs, recommendation)
    return AssessmentResult(
        recommendation=recommendation,
        pce_result=inputs.pce_result,
        evidence_status=status,
        independent_concerns=list(concerns),
        evidence_confidence=local_confidence(inputs, recommendation, data_mode=data_mode),
        funds_released=False,
        payment_executed=False,
        automatic_sanction=False,
        pfms_integrated=False,
    )
