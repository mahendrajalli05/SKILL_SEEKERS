"""Grounding validation for Investigation Copilot V1.

Rejects fabricated citations, invented scores, and unsupported rule IDs.
Falls back to the deterministic answer when validation fails.
"""

from __future__ import annotations

import re

from app.copilot.context import allowed_identifiers
from app.copilot.types import CopilotDraft, InvestigationBundle

_EVIDENCE_ID = re.compile(r"\bev:[a-z0-9_:\-]+", re.IGNORECASE)
_SCHEME_ID = re.compile(r"\bSVK-[A-Z]{2,3}-\d{1,6}\b")
_INTERNAL_ID = re.compile(r"\binternal:[A-Za-z0-9:_-]+")
_RULE_ID = re.compile(r"\bMPLADS[-_][A-Z0-9._-]+\b", re.IGNORECASE)


def extract_cited_ids(text: str) -> set[str]:
    blob = text or ""
    found = set(_EVIDENCE_ID.findall(blob))
    found.update(_SCHEME_ID.findall(blob))
    found.update(_INTERNAL_ID.findall(blob))
    found.update(item.upper() if item.startswith("MPLADS") else item for item in _RULE_ID.findall(blob))
    found.update(_RULE_ID.findall(blob))
    return found


def grounding_errors(draft: CopilotDraft, bundle: InvestigationBundle) -> list[str]:
    allowed = allowed_identifiers(bundle)
    cited = extract_cited_ids(draft.sections.render())
    cited.update(draft.evidence_ids)
    errors: list[str] = []
    for item in cited:
        if item not in allowed:
            errors.append(f"ungrounded_id:{item}")
    for evidence_id in draft.evidence_ids:
        if evidence_id not in allowed:
            errors.append(f"fabricated_evidence:{evidence_id}")
    return errors


def is_grounded(draft: CopilotDraft, bundle: InvestigationBundle) -> bool:
    return not grounding_errors(draft, bundle)
