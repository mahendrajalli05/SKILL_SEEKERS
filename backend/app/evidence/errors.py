"""Evidence Object validation errors."""

from __future__ import annotations


class EvidenceValidationError(ValueError):
    """Raised when an evidence object is incomplete, inconsistent, or forbidden."""
