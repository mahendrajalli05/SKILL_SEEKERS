"""Request/response schemas for project-scoped ML evidence.

Kept beside the ML schemas. Does not change Evidence Object V1 required fields.
"""

from app.domain.schemas.ml import MlEvidenceCreateRequest, MlEvidenceCreateResponse

__all__ = ["MlEvidenceCreateRequest", "MlEvidenceCreateResponse"]
