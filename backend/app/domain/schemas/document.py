from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.domain.enums import DataMode
from app.engines.document.constants import GOVERNANCE_NOTE


def _reject_fraud(value: object) -> object:
    if isinstance(value, str) and "fraud" in value.casefold():
        raise ValueError("Document Intelligence must not claim fraud.")
    return value


class ExtractedFieldRead(BaseModel):
    name: str
    value: Any = None
    unit: str | None = None
    confidence: float | None = None
    extraction_method: str
    source_location: str | None = None
    available: bool = False
    unavailable_reason: str | None = None


class ExtractionRead(BaseModel):
    status: str
    extraction_method: str | None = None
    fields: list[ExtractedFieldRead] = Field(default_factory=list)
    structure: dict[str, Any] = Field(default_factory=dict)
    page_count: int | None = None
    raw_text_available: bool | None = None
    notes: list[str] = Field(default_factory=list)
    text_sha256: str | None = None
    similar_document_ids: list[int] = Field(default_factory=list)
    evidence_id: str | None = None


class DocumentRead(BaseModel):
    document_id: int
    project_id: int
    filename: str | None = None
    mime_type: str | None = None
    document_type: str | None = None
    pce_kind: str | None = None
    uploaded_at: str | None = None
    data_mode: DataMode | str | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)
    content_sha256: str | None = None
    file_size: int | None = None
    extraction_status: str | None = None
    integrity_status: str | None = None
    duplicate_of_id: int | None = None
    attached_to_plan: bool = False
    attached_to_evidence: bool = False
    observed_quantity: float | None = None
    observed_quantity_unit: str | None = None
    observed_expenditure: float | None = None
    extraction: ExtractionRead | None = None
    engine_version: str
    note: str = GOVERNANCE_NOTE

    @field_validator("filename")
    @classmethod
    def no_fraud(cls, value: str | None) -> str | None:
        _reject_fraud(value)
        return value


class DocumentListResponse(BaseModel):
    project_id: int
    items: list[DocumentRead] = Field(default_factory=list)
    conflicts: list[dict[str, Any]] = Field(default_factory=list)
    note: str = GOVERNANCE_NOTE


class AttachResult(BaseModel):
    document_id: int
    project_id: int
    attached_to_plan: bool = False
    attached_to_evidence: bool = False
    conflicts: list[dict[str, Any]] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    evidence_id: str | None = None
    observed_quantity: float | None = None
    observed_quantity_unit: str | None = None
    observed_expenditure: float | None = None
    note: str = GOVERNANCE_NOTE
