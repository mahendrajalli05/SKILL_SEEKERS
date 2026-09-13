"""Plan → Claim → Evidence framing for satellite findings.

Does not change Plan–Claim–Evidence V1 comparison logic.
Does not mark a claim false.
"""

from __future__ import annotations

from app.engines.pce.types import AssembledClaim
from app.engines.satellite.constants import (
    DEFAULT_SITE_CLAIM,
    PCE_CLAIM_NOT_FALSE_NOTE,
    SATELLITE_CONSISTENT,
    SATELLITE_INCONCLUSIVE,
    SATELLITE_UNAVAILABLE,
)
from app.engines.satellite.types import PlanClaimEvidenceFraming, SatelliteResult


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
        return "Work is claimed 100% complete."
    return None


def _satellite_sentence(result: SatelliteResult) -> str:
    if result.overall_result == SATELLITE_UNAVAILABLE:
        return "Satellite imagery is unavailable for the claimed site and date window."
    bits: list[str] = []
    if result.imagery_available:
        bits.append("Imagery available")
        if result.acquisition_date:
            bits.append(f"acquisition {result.acquisition_date}")
        if result.spatial_resolution_m is not None:
            bits.append(f"resolution {result.spatial_resolution_m} m")
    if result.coverage:
        bits.append(f"coverage {result.coverage}")
    if result.change_result:
        bits.append(f"change {result.change_result}")
    bits.append(result.finding)
    return ". ".join(bits)


def frame_against_claim(
    result: SatelliteResult,
    claim: AssembledClaim | None,
) -> PlanClaimEvidenceFraming:
    claim_text = _claim_text(claim) or DEFAULT_SITE_CLAIM
    satellite = _satellite_sentence(result)
    framing_result = result.overall_result
    if framing_result not in {
        SATELLITE_CONSISTENT,
        SATELLITE_UNAVAILABLE,
        SATELLITE_INCONCLUSIVE,
        "SATELLITE_INCONSISTENT",
    }:
        framing_result = SATELLITE_INCONCLUSIVE
    return PlanClaimEvidenceFraming(
        claim=claim_text,
        satellite=satellite,
        result=framing_result,
        note=(
            f"CLAIM: {claim_text} SATELLITE: {satellite} Result: {framing_result}. "
            + PCE_CLAIM_NOT_FALSE_NOTE
        ),
        claim_marked_false=False,
    )
