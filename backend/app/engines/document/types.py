"""Document & Blueprint Intelligence V1 typed payloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain.enums import DataMode


@dataclass
class ExtractedField:
    name: str
    value: Any = None
    unit: str | None = None
    confidence: float | None = None
    extraction_method: str = "unavailable"
    source_location: str | None = None
    available: bool = False
    unavailable_reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "confidence": self.confidence,
            "extraction_method": self.extraction_method,
            "source_location": self.source_location,
            "available": self.available,
            "unavailable_reason": self.unavailable_reason,
        }


@dataclass
class QuantityItem:
    item: str | None = None
    quantity: float | None = None
    unit: str | None = None
    confidence: float | None = None
    source_location: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "item": self.item,
            "quantity": self.quantity,
            "unit": self.unit,
            "confidence": self.confidence,
            "source_location": self.source_location,
        }


@dataclass
class MilestoneItem:
    milestone: str | None = None
    amount: float | None = None
    target_date: str | None = None
    confidence: float | None = None
    source_location: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "milestone": self.milestone,
            "amount": self.amount,
            "target_date": self.target_date,
            "confidence": self.confidence,
            "source_location": self.source_location,
        }


@dataclass
class NormalizedStructure:
    scope_description: str | None = None
    quantities: list[QuantityItem] = field(default_factory=list)
    dimensions: dict[str, ExtractedField] = field(default_factory=dict)
    finance: dict[str, ExtractedField] = field(default_factory=dict)
    milestones: list[MilestoneItem] = field(default_factory=list)
    dates: dict[str, ExtractedField] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "scope": {"description": self.scope_description},
            "quantities": [item.as_dict() for item in self.quantities],
            "dimensions": {key: value.as_dict() for key, value in self.dimensions.items()},
            "finance": {key: value.as_dict() for key, value in self.finance.items()},
            "milestones": [item.as_dict() for item in self.milestones],
            "dates": {key: value.as_dict() for key, value in self.dates.items()},
        }


@dataclass
class SourceValue:
    field: str
    value: Any
    unit: str | None
    source: str
    confidence: float | None
    timestamp: str | None
    document_id: int | None
    data_mode: DataMode | str

    def as_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "value": self.value,
            "unit": self.unit,
            "source": self.source,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "document_id": self.document_id,
            "data_mode": self.data_mode.value if isinstance(self.data_mode, DataMode) else self.data_mode,
        }


@dataclass
class PlanConflict:
    field: str
    result: str
    sources: list[SourceValue]
    explanation: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "result": self.result,
            "sources": [item.as_dict() for item in self.sources],
            "explanation": self.explanation,
        }


@dataclass
class ExtractionResult:
    document_id: int
    project_id: int
    status: str
    extraction_method: str
    fields: list[ExtractedField]
    structure: NormalizedStructure
    raw_text_available: bool
    page_count: int | None
    text_sha256: str | None
    integrity_status: str
    similar_document_ids: list[int] = field(default_factory=list)
    duplicate_of_id: int | None = None
    evidence_id: str | None = None
    data_mode: DataMode = DataMode.REAL
    notes: list[str] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)

    def field_map(self) -> dict[str, ExtractedField]:
        return {item.name: item for item in self.fields}

    def as_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "project_id": self.project_id,
            "status": self.status,
            "extraction_method": self.extraction_method,
            "fields": [item.as_dict() for item in self.fields],
            "structure": self.structure.as_dict(),
            "raw_text_available": self.raw_text_available,
            "page_count": self.page_count,
            "text_sha256": self.text_sha256,
            "integrity_status": self.integrity_status,
            "similar_document_ids": self.similar_document_ids,
            "duplicate_of_id": self.duplicate_of_id,
            "evidence_id": self.evidence_id,
            "data_mode": self.data_mode.value,
            "notes": self.notes,
            "provenance": self.provenance,
        }
