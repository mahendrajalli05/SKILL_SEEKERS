from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.enums import (
    DataMode,
    EvidenceDisposition,
    EvidenceEngine,
    EvidenceFactKind,
    EvidenceSeverity,
    EvidenceStatus,
    SignalType,
    SourceType,
)


class EvidenceFact(BaseModel):
    """One observation or derived value attached to an evidence object."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    key: str
    value: Any = None
    source: str
    kind: EvidenceFactKind = EvidenceFactKind.OBSERVATION
    statement: str | None = None

    @field_validator("key")
    @classmethod
    def key_must_be_non_empty(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("Evidence fact key is required.")
        return text

    @field_validator("source")
    @classmethod
    def source_must_be_non_empty(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("Evidence fact source/provenance is required.")
        return text


class EvidenceProvenance(BaseModel):
    """Source trail for an evidence object. Must not be dropped."""

    data_mode: DataMode
    source_type: SourceType
    source_ids: list[str] = Field(min_length=1)
    internal_project_id: str
    notes: str
    source_dataset: str | None = None
    source_url: str | None = None
    extracted_at: str | None = None
    download_date: str | None = None
    publisher: str | None = None
    file_sha256: str | None = None
    source_filename: str | None = None
    source_sha256: str | None = None
    snapshot_id: int | None = None
    internal_id_scheme: str | None = None
    source_first_row_number: int | None = None
    enrichment_used: bool = False
    enrichment_path: str | None = None
    enrichment_sha256: str | None = None

    @field_validator("internal_project_id", "notes")
    @classmethod
    def required_text(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("Provenance internal_project_id and notes are required.")
        return text

    @field_validator("source_ids")
    @classmethod
    def ids_must_be_non_empty_strings(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if str(item).strip()]
        if not cleaned:
            raise ValueError("Provenance source_ids must contain at least one identifier.")
        return cleaned


class EvidenceObject(BaseModel):
    """Canonical auditable finding envelope for all SARVSAKSHI engines.

    Distinguishes observation, derived finding, score, confidence, and
    source/provenance. Never a legal fraud conclusion.
    """

    model_config = ConfigDict(from_attributes=True)

    evidence_id: str
    project_id: int
    signal_type: SignalType
    finding: str
    severity: EvidenceSeverity = EvidenceSeverity.INFO
    score: float | int | None = Field(default=None, ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    source_type: SourceType
    source_ids: list[str] = Field(min_length=1)
    evidence_facts: list[EvidenceFact] = Field(default_factory=list)
    explanation: str
    engine_name: EvidenceEngine | str
    engine_version: str
    created_at: datetime | None = None
    data_mode: DataMode
    provenance: EvidenceProvenance
    disposition: EvidenceDisposition
    status: EvidenceStatus = EvidenceStatus.INCONCLUSIVE
    comparables: list[Any] = Field(default_factory=list)
    rule_ids: list[str] = Field(default_factory=list)
    guideline_refs: list[str] = Field(default_factory=list)

    @field_validator("evidence_id", "finding", "explanation", "engine_version")
    @classmethod
    def required_non_empty(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("Required evidence text fields must be non-empty.")
        return text

    @field_validator("source_ids")
    @classmethod
    def source_ids_required(cls, value: list[str]) -> list[str]:
        cleaned = [str(item).strip() for item in value if str(item).strip()]
        if not cleaned:
            raise ValueError("source_ids must preserve at least one source reference.")
        return cleaned

    @field_validator("engine_name", mode="before")
    @classmethod
    def coerce_engine_name(cls, value: object) -> str:
        if isinstance(value, EvidenceEngine):
            return value.value
        text = str(value).strip()
        if not text:
            raise ValueError("engine_name is required.")
        return text

    @model_validator(mode="after")
    def provenance_must_match_envelope(self) -> EvidenceObject:
        if self.provenance.data_mode != self.data_mode:
            raise ValueError("Provenance data_mode must match the evidence object data_mode.")
        if self.provenance.source_type != self.source_type:
            raise ValueError("Provenance source_type must match the evidence object source_type.")
        if self.data_mode == DataMode.REAL and self.source_type == SourceType.SYNTHETIC_TEST_RECORD:
            raise ValueError("REAL evidence must never be marked SYNTHETIC.")
        return self


class ProjectEvidenceResponse(BaseModel):
    """Evidence for one project. Investigation Priority is not assigned here."""

    project_id: int
    internal_project_id: str | None = None
    items: list[EvidenceObject] = Field(default_factory=list)
    note: str = (
        "Evidence objects only. Investigation Priority and fused Evidence "
        "Confidence are not assigned by this endpoint."
    )
