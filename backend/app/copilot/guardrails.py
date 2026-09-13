"""Guardrails for Investigation Copilot V1.

Never fabricate facts, legal fraud findings, unsupported rules, or hidden
data-mode switching.
"""

from __future__ import annotations

import re

from app.copilot.constants import (
    FORBIDDEN_RECOMMENDATIONS,
    FRAUD_CLAIM_PATTERN,
    LEGAL_CONCLUSION_PATTERN,
    PATH_LEAK_PATTERN,
    SANCTION_PATTERN,
    SECRET_LEAK_PATTERN,
)
from app.copilot.types import CopilotDraft, CopilotRecommendation, CopilotSections
from app.evidence.constants import FRAUD_CLAIM_PATTERN as EVIDENCE_FRAUD_PATTERN

_FRAUD = re.compile(FRAUD_CLAIM_PATTERN, re.IGNORECASE)
_EVIDENCE_FRAUD = re.compile(EVIDENCE_FRAUD_PATTERN, re.IGNORECASE)
_LEGAL = re.compile(LEGAL_CONCLUSION_PATTERN, re.IGNORECASE)
_SANCTION = re.compile(SANCTION_PATTERN, re.IGNORECASE)
_PATH = re.compile(PATH_LEAK_PATTERN)
_SECRET = re.compile(SECRET_LEAK_PATTERN, re.IGNORECASE)


_POSITIVE_FRAUD = re.compile(
    r"\b(?:this (?:project |work )?is fraud|fraud has been established|committed fraud|prove[sd]? fraud)\b",
    re.IGNORECASE,
)


def contains_fraud_claim(text: str) -> bool:
    blob = text or ""
    if _POSITIVE_FRAUD.search(blob):
        return True
    if not (_FRAUD.search(blob) or _EVIDENCE_FRAUD.search(blob)):
        return False
    lowered = blob.lower()
    if (
        "does not determine legal fraud" in lowered
        or "not a legal finding" in lowered
        or "not a fraud probability" in lowered
        or "cannot determine fraud" in lowered
    ):
        return False
    return True


def contains_forbidden_recommendation(text: str) -> bool:
    blob = (text or "").casefold()
    if _SANCTION.search(blob):
        return True
    return any(term in blob for term in FORBIDDEN_RECOMMENDATIONS)


def strip_sensitive(text: str) -> str:
    cleaned = _PATH.sub("[redacted]", text or "")
    cleaned = _SECRET.sub("[redacted]", cleaned)
    return cleaned


def draft_violates_guardrails(draft: CopilotDraft) -> str | None:
    blob = draft.sections.render()
    if contains_fraud_claim(blob):
        return "fraud_language"
    if _LEGAL.search(blob):
        return "legal_conclusion"
    if contains_forbidden_recommendation(blob):
        return "forbidden_recommendation"
    if _PATH.search(blob) or _SECRET.search(blob):
        return "sensitive_leak"
    if draft.recommended_action not in CopilotRecommendation:
        return "invalid_recommendation"
    return None


def legal_refusal_sections() -> CopilotSections:
    return CopilotSections(
        answer=(
            "SARVSAKSHI does not determine legal fraud. Investigation Priority "
            "and Evidence Confidence are review rankings only. Authorized officers decide."
        ),
        why="The Copilot is not a legal decision system and must not declare fraud.",
        evidence="No legal finding is produced from stored evidence.",
        missing="A legal determination is outside the scope of this assistant.",
        recommended_action=CopilotRecommendation.NEED_MORE_INFORMATION.value,
    )
