from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.domain.enums import DataMode
from app.engines.geo.constants import DEFAULT_THRESHOLD_METERS, GOVERNANCE_NOTE, SATELLITE_VERIFICATION_NOT_AVAILABLE


def _reject_fraud(value: object) -> object:
    if isinstance(value, str) and "fraud" in value.casefold():
        raise ValueError("Geospatial Consistency must not claim fraud.")
    return value


class ProjectLocationRead(BaseModel):
    project_id: int
    latitude: float | None = None
    longitude: float | None = None
    source: str
    data_mode: DataMode | str
    confidence: float
    timestamp: str | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)
    available: bool
    unavailable_reason: str | None = None
    synthetic: bool = False
    label: str | None = None


class ImageLocationRead(BaseModel):
    image_id: int
    latitude: float | None = None
    longitude: float | None = None
    source: str
    extraction_method: str
    confidence: float
    data_mode: DataMode | str
    gps_status: str
    gps_available: bool
    unavailable_reason: str | None = None


class ImageConsistencyRead(BaseModel):
    image_id: int
    location: ImageLocationRead
    result: str
    distance_meters: float | None = None
    distance_km: float | None = None
    threshold_meters: float
    finding: str
    explanation: str
    confidence: float
    score: float | None = None
    evidence_id: str | None = None

    @field_validator("finding", "explanation")
    @classmethod
    def no_fraud(cls, value: str) -> str:
        _reject_fraud(value)
        return value


class GeospatialSummaryRead(BaseModel):
    image_count: int = 0
    gps_available_count: int = 0
    gps_unavailable_count: int = 0
    consistent_count: int = 0
    mismatch_count: int = 0
    inconclusive_count: int = 0
    mixed_results: bool = False
    distances_meters: list[float] = Field(default_factory=list)


class SatelliteCapabilityRead(BaseModel):
    capability: str = SATELLITE_VERIFICATION_NOT_AVAILABLE
    result: str = SATELLITE_VERIFICATION_NOT_AVAILABLE
    available: bool = False
    imagery: None = None
    explanation: str = ""
    score: None = None


class PlanClaimEvidenceFramingRead(BaseModel):
    claim: str | None = None
    evidence: str
    result: str
    note: str


class GeospatialCheckRequest(BaseModel):
    data_mode: str | None = None
    threshold_meters: float | None = Field(default=None, gt=0)


class GeospatialRead(BaseModel):
    project_id: int
    internal_project_id: str
    data_mode: DataMode | str
    project_location: ProjectLocationRead
    image_locations: list[ImageLocationRead] = Field(default_factory=list)
    images: list[ImageConsistencyRead] = Field(default_factory=list)
    summary: GeospatialSummaryRead
    overall_result: str
    location_consistency: str
    threshold_meters: float = DEFAULT_THRESHOLD_METERS
    evidence_confidence: float
    satellite: SatelliteCapabilityRead
    plan_claim_evidence: PlanClaimEvidenceFramingRead | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    explanation: str
    limitations: list[str] = Field(default_factory=list)
    note: str = GOVERNANCE_NOTE
    engine_version: str

    @field_validator("explanation", "note", "overall_result", "location_consistency")
    @classmethod
    def no_fraud_text(cls, value: str) -> str:
        _reject_fraud(value)
        return value
