"""Shared Evidence Object layer (V1).

Canonical, auditable findings for Cost, Time, Overlap, Compliance, and
later engines. Does not run Risk Fusion or assign Investigation Priority.
"""

from app.domain.schemas.evidence import EvidenceFact, EvidenceObject, EvidenceProvenance
from app.evidence.errors import EvidenceValidationError
from app.evidence.ids import make_evidence_id
from app.evidence.repository import add_evidence_object, list_project_evidence, persist_evidence_object
from app.evidence.validate import validate_evidence

__all__ = [
    "EvidenceFact",
    "EvidenceObject",
    "EvidenceProvenance",
    "EvidenceValidationError",
    "add_evidence_object",
    "list_project_evidence",
    "make_evidence_id",
    "persist_evidence_object",
    "validate_evidence",
]
