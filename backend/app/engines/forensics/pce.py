"""Plan → Claim → Evidence framing for forensic findings.

Does not change Plan–Claim–Evidence V1 comparison logic.
Does not mark a claim false.
"""

from __future__ import annotations

from app.engines.forensics.constants import (
    CLAIM_PHOTO_COMPLETED,
    INCONCLUSIVE,
    PCE_CLAIM_NOT_FALSE_NOTE,
    PCE_REVIEW_REQUIRED,
    POTENTIAL_MANIPULATION,
    REVIEW_REQUIRED,
)
from app.engines.forensics.types import ForensicResult, PlanClaimEvidenceFraming
from app.engines.pce.types import AssembledClaim


def _claim_text(claim: AssembledClaim | None) -> str | None:
    if claim is None or not claim.recorded:
        return None
    parts = [
        claim.claimed_completion_state,
        claim.claimed_progress,
        claim.milestone_claimed,
    ]
    text = " ".join(str(item).strip() for item in parts if item).strip()
    if text:
        return text
    if claim.claimed_progress_percent is not None and float(claim.claimed_progress_percent) >= 100:
        return CLAIM_PHOTO_COMPLETED
    return None


def frame_against_claim(result: ForensicResult, claim: AssembledClaim | None) -> PlanClaimEvidenceFraming:
    claim_text = _claim_text(claim) or CLAIM_PHOTO_COMPLETED
    forensic_bits: list[str] = []
    if result.reuse_signal.result in {"EXACT_DUPLICATE", "POTENTIAL_IMAGE_REUSE"}:
        forensic_bits.append(
            "Potential image reuse detected."
            if result.reuse_signal.result == "POTENTIAL_IMAGE_REUSE"
            else "Exact duplicate image detected."
        )
    if result.manipulation_signal.result == POTENTIAL_MANIPULATION:
        forensic_bits.append("Potential manipulation signal.")
    if result.metadata_signal.result == "METADATA_ANOMALY":
        forensic_bits.append("Metadata anomaly signal.")
    if result.ai_generation_signal.result == "AI_GENERATION_ANALYSIS_UNAVAILABLE":
        forensic_bits.append("AI-generation analysis unavailable.")
    if not forensic_bits:
        forensic_bits.append("No strong forensic signal.")
    forensic = " ".join(forensic_bits)
    framing_result = PCE_REVIEW_REQUIRED if result.overall_assessment == REVIEW_REQUIRED else (
        INCONCLUSIVE if result.overall_assessment == INCONCLUSIVE else result.overall_assessment
    )
    return PlanClaimEvidenceFraming(
        claim=claim_text,
        forensic=forensic,
        result=framing_result,
        note=(
            f"CLAIM: {claim_text} FORENSIC: {forensic} Result: {framing_result}. "
            + PCE_CLAIM_NOT_FALSE_NOTE
        ),
        claim_marked_false=False,
    )
