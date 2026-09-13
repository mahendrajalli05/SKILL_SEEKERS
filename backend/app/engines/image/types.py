"""Image Evidence & Authenticity V1 typed payloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain.enums import DataMode


@dataclass
class MetadataField:
    field: str
    value: Any
    source: str
    extraction_method: str
    confidence: float
    available: bool = True
    unavailable_reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "value": self.value,
            "source": self.source,
            "extraction_method": self.extraction_method,
            "confidence": self.confidence,
            "available": self.available,
            "unavailable_reason": self.unavailable_reason,
        }


@dataclass
class ReuseMatch:
    image_id: int
    matched_image_id: int
    matched_project_id: int | None
    hash_name: str
    distance: int
    similarity: float
    explanation: str
    confidence: float
    data_mode: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "image_id": self.image_id,
            "matched_image_id": self.matched_image_id,
            "matched_project_id": self.matched_project_id,
            "hash_name": self.hash_name,
            "distance": self.distance,
            "hash_similarity": self.similarity,
            "explanation": self.explanation,
            "confidence": self.confidence,
            "data_mode": self.data_mode,
        }


@dataclass
class AuthenticityCapability:
    capability: str
    result: str
    explanation: str
    score: None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "capability": self.capability,
            "result": self.result,
            "explanation": self.explanation,
            "score": self.score,
        }


@dataclass
class ImageAnalysis:
    image_id: int
    project_id: int
    content_sha256: str
    ahash: str | None
    dhash: str | None
    phash: str | None
    integrity_status: str
    duplicate_of_id: int | None
    exact_duplicate: bool
    potential_reuse: bool
    exact_matches: list[ReuseMatch] = field(default_factory=list)
    reuse_matches: list[ReuseMatch] = field(default_factory=list)
    metadata_fields: list[MetadataField] = field(default_factory=list)
    metadata_status: str = "METADATA_UNAVAILABLE"
    gps_available: bool = False
    gps_message: str | None = None
    capture_timestamp: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    quality: dict[str, Any] = field(default_factory=dict)
    authenticity: AuthenticityCapability = field(
        default_factory=lambda: AuthenticityCapability(
            capability="NOT_IMPLEMENTED",
            result="INCONCLUSIVE",
            explanation="",
        )
    )
    evidence_ids: list[str] = field(default_factory=list)
    data_mode: DataMode = DataMode.REAL
    notes: list[str] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "image_id": self.image_id,
            "project_id": self.project_id,
            "content_sha256": self.content_sha256,
            "ahash": self.ahash,
            "dhash": self.dhash,
            "phash": self.phash,
            "integrity_status": self.integrity_status,
            "duplicate_of_id": self.duplicate_of_id,
            "exact_duplicate": self.exact_duplicate,
            "potential_reuse": self.potential_reuse,
            "exact_matches": [item.as_dict() for item in self.exact_matches],
            "reuse_matches": [item.as_dict() for item in self.reuse_matches],
            "metadata_fields": [item.as_dict() for item in self.metadata_fields],
            "metadata_status": self.metadata_status,
            "gps_available": self.gps_available,
            "gps_message": self.gps_message,
            "capture_timestamp": self.capture_timestamp,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "quality": self.quality,
            "authenticity": self.authenticity.as_dict(),
            "evidence_ids": self.evidence_ids,
            "data_mode": self.data_mode.value,
            "notes": self.notes,
            "provenance": self.provenance,
        }
