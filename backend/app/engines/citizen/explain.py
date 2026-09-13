"""Jan-Sakshi explanations. Never claims a legal finding of wrongdoing."""

from __future__ import annotations

from app.engines.citizen.constants import GOVERNANCE_NOTE, THRESHOLD_NOTE


def submission_explanation(
    *,
    status: str,
    verification_result: str,
    reasons: list[str],
    duplicate_flagged: bool,
) -> str:
    parts = [
        f"Submission status is {status}. Location verification is {verification_result}.",
        *reasons,
    ]
    if duplicate_flagged:
        parts.append(
            "An identical image was previously submitted. This is flagged as "
            "POTENTIAL_DUPLICATE_CITIZEN_EVIDENCE for review and is not treated as a legal finding of wrongdoing."
        )
    parts.append(THRESHOLD_NOTE)
    parts.append(GOVERNANCE_NOTE)
    return " ".join(part.strip() for part in parts if part)
