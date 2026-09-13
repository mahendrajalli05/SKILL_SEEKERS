"""Plan → Claim → Evidence framing for citizen reports.

Does not change Plan–Claim–Evidence V1 comparison logic.
Does not mark a claim false automatically.
"""

from __future__ import annotations

from app.engines.citizen.constants import (
    COMPLETION_CLAIM_TOKENS,
    INCOMPLETE_TOKENS,
    ISSUE_INCOMPLETE_WORK,
    PCE_CLAIM_NOT_FALSE_NOTE,
    PCE_CONCERN,
    PCE_CONSISTENT,
    PCE_CONTRADICTION,
    PCE_INCONCLUSIVE,
)
from app.engines.citizen.types import PceFraming
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
        return "Work is complete."
    return None


def frame_against_claim(
    *,
    claim: AssembledClaim | None,
    observation_text: str | None,
    issue_category: str | None,
) -> PceFraming:
    claim_text = _claim_text(claim)
    citizen_text = (observation_text or "").strip() or None
    if claim_text is None or citizen_text is None:
        return PceFraming(
            claim=claim_text,
            citizen_evidence=citizen_text,
            result=PCE_INCONCLUSIVE,
            note=(
                "Citizen evidence is recorded as supporting evidence. "
                "There is not enough claim/observation pairing to compare. "
                + PCE_CLAIM_NOT_FALSE_NOTE
            ),
        )
    folded_claim = claim_text.casefold()
    folded_citizen = citizen_text.casefold()
    claim_complete = any(token in folded_claim for token in COMPLETION_CLAIM_TOKENS)
    citizen_incomplete = issue_category == ISSUE_INCOMPLETE_WORK or any(
        token in folded_citizen for token in INCOMPLETE_TOKENS
    )
    if claim_complete and citizen_incomplete:
        return PceFraming(
            claim=claim_text,
            citizen_evidence=citizen_text,
            result=PCE_CONTRADICTION,
            note=(
                f"CLAIM: {claim_text} Citizen evidence: {citizen_text} "
                f"Result: {PCE_CONTRADICTION} / {PCE_CONCERN}. "
                + PCE_CLAIM_NOT_FALSE_NOTE
            ),
        )
    return PceFraming(
        claim=claim_text,
        citizen_evidence=citizen_text,
        result=PCE_CONSISTENT if not citizen_incomplete else PCE_INCONCLUSIVE,
        note=(
            f"CLAIM: {claim_text} Citizen evidence: {citizen_text} "
            "Citizen reports remain supporting evidence. "
            + PCE_CLAIM_NOT_FALSE_NOTE
        ),
    )
