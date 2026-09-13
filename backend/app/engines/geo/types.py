"""Geospatial Consistency V1 typed payloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain.enums import DataMode
from app.engines.geo.constants import (
    DEFAULT_THRESHOLD_METERS,
    INCONCLUSIVE,
    SATELLITE_VERIFICATION_NOT_AVAILABLE,
)


@dataclass
class ProjectLocation:
    project_id: int
    latitude: float | None
    longitude: float | None
    source: str
    data_mode: DataMode
    confidence: float
    timestamp: str | None
    provenance: dict[str, Any]
    available: bool
    unavailable_reason: str | None = None
    synthetic: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "source": self.source,
            "data_mode": self.data_mode.value,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "provenance": self.provenance,
            "available": self.available,
            "unavailable_reason": self.unavailable_reason,
            "synthetic": self.synthetic,
            "label": "SYNTHETIC" if self.synthetic else None,
        }


@dataclass
class ImageLocation:
    image_id: int
    latitude: float | None
    longitude: float | None
    source: str
    extraction_method: str
    confidence: float
    data_mode: DataMode
    gps_status: str
    gps_available: bool
    unavailable_reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "image_id": self.image_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "source": self.source,
            "extraction_method": self.extraction_method,
            "confidence": self.confidence,
            "data_mode": self.data_mode.value,
            "gps_status": self.gps_status,
            "gps_available": self.gps_available,
            "unavailable_reason": self.unavailable_reason,
        }


@dataclass
class ImageConsistency:
    image_id: int
    location: ImageLocation
    result: str
    distance_meters: float | None
    distance_km: float | None
    threshold_meters: float
    finding: str
    explanation: str
    confidence: float
    score: float | None
    evidence_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "image_id": self.image_id,
            "location": self.location.as_dict(),
            "result": self.result,
            "distance_meters": self.distance_meters,
            "distance_km": self.distance_km,
            "threshold_meters": self.threshold_meters,
            "finding": self.finding,
            "explanation": self.explanation,
            "confidence": self.confidence,
            "score": self.score,
            "evidence_id": self.evidence_id,
        }


@dataclass
class GeospatialSummary:
    image_count: int = 0
    gps_available_count: int = 0
    gps_unavailable_count: int = 0
    consistent_count: int = 0
    mismatch_count: int = 0
    inconclusive_count: int = 0
    mixed_results: bool = False
    distances_meters: list[float] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "image_count": self.image_count,
            "gps_available_count": self.gps_available_count,
            "gps_unavailable_count": self.gps_unavailable_count,
            "consistent_count": self.consistent_count,
            "mismatch_count": self.mismatch_count,
            "inconclusive_count": self.inconclusive_count,
            "mixed_results": self.mixed_results,
            "distances_meters": self.distances_meters,
        }


@dataclass
class SatelliteCapability:
    capability: str = SATELLITE_VERIFICATION_NOT_AVAILABLE
    result: str = SATELLITE_VERIFICATION_NOT_AVAILABLE
    available: bool = False
    imagery: None = None
    explanation: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "capability": self.capability,
            "result": self.result,
            "available": self.available,
            "imagery": self.imagery,
            "explanation": self.explanation,
            "score": None,
        }


@dataclass
class PlanClaimEvidenceFraming:
    claim: str | None
    evidence: str
    result: str
    note: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "claim": self.claim,
            "evidence": self.evidence,
            "result": self.result,
            "note": self.note,
        }


@dataclass
class GeospatialResult:
    project_id: int
    internal_project_id: str
    data_mode: DataMode
    project_location: ProjectLocation
    image_locations: list[ImageLocation]
    images: list[ImageConsistency]
    summary: GeospatialSummary
    overall_result: str
    threshold_meters: float = DEFAULT_THRESHOLD_METERS
    evidence_confidence: float = 0.0
    location_consistency: str = INCONCLUSIVE
    satellite: SatelliteCapability = field(default_factory=SatelliteCapability)
    plan_claim_evidence: PlanClaimEvidenceFraming | None = None
    evidence_ids: list[str] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)
    explanation: str = ""
    limitations: list[str] = field(default_factory=list)
    note: str = ""
    engine_version: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "internal_project_id": self.internal_project_id,
            "data_mode": self.data_mode.value,
            "project_location": self.project_location.as_dict(),
            "image_locations": [item.as_dict() for item in self.image_locations],
            "images": [item.as_dict() for item in self.images],
            "summary": self.summary.as_dict(),
            "overall_result": self.overall_result,
            "location_consistency": self.location_consistency,
            "threshold_meters": self.threshold_meters,
            "evidence_confidence": self.evidence_confidence,
            "satellite": self.satellite.as_dict(),
            "plan_claim_evidence": (
                self.plan_claim_evidence.as_dict() if self.plan_claim_evidence else None
            ),
            "evidence_ids": self.evidence_ids,
            "provenance": self.provenance,
            "explanation": self.explanation,
            "limitations": self.limitations,
            "note": self.note,
            "engine_version": self.engine_version,
        }
