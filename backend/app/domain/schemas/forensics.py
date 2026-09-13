from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.domain.enums import DataMode
from app.engines.forensics.constants import GOVERNANCE_NOTE, PROTOTYPE_ASSESSMENT_LABEL


def _reject_forbidden(value: object) -> object:
    if not isinstance(value, str):
        return value
    folded = value.casefold()
    if "fraud" in folded or "definitely ai-generated" in folded or "definitely manipulated" in folded:
        raise ValueError("Image Forensics must not claim fraud or false certainty.")
    if re.search(r"\bthis (image|photo) is fake\b", folded) or re.search(r"\bfake image\b", folded):
        raise ValueError("Image Forensics must not claim fraud or false certainty.")
    return value


class ForensicSignalRead(BaseModel):
    name: str
    result: str
    confidence_label: str
    confidence: float
    available: bool = True
    findings: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)

    @field_validator("result", "findings", mode="before")
    @classmethod
    def no_forbidden(cls, value: object) -> object:
        if isinstance(value, list):
            for item in value:
                _reject_forbidden(item)
            return value
        return _reject_forbidden(value)


class ForensicIntegrityRead(BaseModel):
    status: str
    readable: bool
    content_sha256: str
    stored_sha256: str | None = None
    bytes_unmodified: bool = True
    mime_type: str | None = None
    file_size: int | None = None
    notes: list[str] = Field(default_factory=list)


class ForensicPceFramingRead(BaseModel):
    claim: str | None = None
    forensic: str
    result: str
    note: str
    claim_marked_false: bool = False

    @field_validator("forensic", "result", "note", "claim")
    @classmethod
    def no_forbidden_text(cls, value: str | None) -> str | None:
        _reject_forbidden(value)
        return value


class ImageForensicsRead(BaseModel):
    image_id: int
    project_id: int
    data_mode: DataMode | str
    integrity: ForensicIntegrityRead
    metadata_signal: ForensicSignalRead
    transformation: dict[str, Any] = Field(default_factory=dict)
    manipulation_signal: ForensicSignalRead
    ai_generation_signal: ForensicSignalRead
    reuse_signal: ForensicSignalRead
    quality_signal: ForensicSignalRead
    overall_assessment: str
    prototype_assessment_label: str = PROTOTYPE_ASSESSMENT_LABEL
    evidence_confidence: float
    confidence_label: str
    explanation: str
    limitations: list[str] = Field(default_factory=list)
    plan_claim_evidence: ForensicPceFramingRead | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    engine_version: str
    note: str = GOVERNANCE_NOTE
    external_transmission: bool = False
    bytes_unmodified: bool = True
    thumbnail_data_url: str | None = None
    finding: str
    source: str
    filename: str | None = None
    mime_type: str | None = None
    file_size: int | None = None
    ahash: str | None = None
    dhash: str | None = None
    phash: str | None = None
    content_sha256: str | None = None
    synthetic: bool = False
    synthetic_label: str | None = None
    ai_generation_analysis: str | None = None

    @field_validator("explanation", "note", "overall_assessment", "finding")
    @classmethod
    def no_forbidden_text(cls, value: str) -> str:
        _reject_forbidden(value)
        return value
