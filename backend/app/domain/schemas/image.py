from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.domain.enums import DataMode
from app.engines.image.constants import GOVERNANCE_NOTE


def _reject_fraud(value: object) -> object:
    if isinstance(value, str) and "fraud" in value.casefold():
        raise ValueError("Image Evidence must not claim fraud.")
    return value


class ImageMetadataFieldRead(BaseModel):
    field: str
    value: Any = None
    source: str
    extraction_method: str
    confidence: float
    available: bool = True
    unavailable_reason: str | None = None


class ImageMatchRead(BaseModel):
    image_id: int
    matched_image_id: int
    matched_project_id: int | None = None
    hash_name: str
    distance: int
    hash_similarity: float | None = None
    explanation: str
    confidence: float
    data_mode: str | None = None

    @field_validator("explanation")
    @classmethod
    def no_fraud(cls, value: str) -> str:
        _reject_fraud(value)
        return value


class ImageAuthenticityRead(BaseModel):
    capability: str = "NOT_IMPLEMENTED"
    result: str = "INCONCLUSIVE"
    explanation: str = ""
    score: float | None = None


class ImageRead(BaseModel):
    image_id: int
    project_id: int
    filename: str | None = None
    mime_type: str | None = None
    file_size: int | None = None
    uploaded_at: str | None = None
    content_sha256: str | None = None
    ahash: str | None = None
    dhash: str | None = None
    phash: str | None = None
    integrity_status: str | None = None
    duplicate_of_id: int | None = None
    analysis_status: str | None = None
    attached_to_evidence: bool = False
    data_mode: DataMode | str | None = None
    source: str | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)
    thumbnail_data_url: str | None = None
    exact_duplicate: bool = False
    potential_reuse: bool = False
    exact_matches: list[ImageMatchRead] = Field(default_factory=list)
    reuse_matches: list[ImageMatchRead] = Field(default_factory=list)
    metadata_status: str | None = None
    metadata_fields: list[ImageMetadataFieldRead] = Field(default_factory=list)
    gps_available: bool = False
    gps_message: str | None = None
    capture_timestamp: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    quality: dict[str, Any] = Field(default_factory=dict)
    authenticity: ImageAuthenticityRead = Field(default_factory=ImageAuthenticityRead)
    evidence_ids: list[str] = Field(default_factory=list)
    evidence_confidence: float | None = None
    engine_version: str
    note: str = GOVERNANCE_NOTE
    limitations: list[str] = Field(default_factory=list)

    @field_validator("filename", "note")
    @classmethod
    def no_fraud_text(cls, value: str | None) -> str | None:
        _reject_fraud(value)
        return value


class ImageSummaryRead(BaseModel):
    images_submitted: int = 0
    exact_duplicates: int = 0
    potential_reuse: int = 0
    gps_available: int = 0
    gps_unavailable: int = 0
    metadata_available: int = 0
    metadata_unavailable: int = 0
    quality_warnings: int = 0
    advanced_authenticity_analysis: str = "INCONCLUSIVE"
    authenticity_capability: str = "NOT_IMPLEMENTED"
    evidence_confidence: float = 0.0
    note: str = GOVERNANCE_NOTE


class ImageListResponse(BaseModel):
    project_id: int
    internal_project_id: str | None = None
    summary: ImageSummaryRead
    items: list[ImageRead] = Field(default_factory=list)
    note: str = GOVERNANCE_NOTE


class ImageAttachResult(BaseModel):
    image_id: int
    project_id: int
    attached_to_evidence: bool = True
    evidence_ids: list[str] = Field(default_factory=list)
    note: str = GOVERNANCE_NOTE
