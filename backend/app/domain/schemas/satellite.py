from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.domain.enums import DataMode
from app.engines.satellite.constants import GOVERNANCE_NOTE, SATELLITE_UNAVAILABLE


def _reject_fraud(value: object) -> object:
    if isinstance(value, str) and "fraud" in value.casefold():
        raise ValueError("Satellite evidence must not claim fraud.")
    return value


class SatelliteCheckRequest(BaseModel):
    data_mode: str | None = None
    provider: str | None = None
    test_scenario: str | None = None
    date_start: str | None = None
    date_end: str | None = None
    aoi_radius_meters: float | None = Field(default=None, gt=0)


class SatellitePceFramingRead(BaseModel):
    claim: str | None = None
    satellite: str
    result: str
    note: str
    claim_marked_false: bool = False


class SatelliteRead(BaseModel):
    project_id: int
    internal_project_id: str
    data_mode: DataMode | str
    overall_result: str
    provider: str
    imagery_available: bool
    acquisition_date: str | None = None
    spatial_resolution_m: float | None = None
    coverage: str | None = None
    change_result: str | None = None
    evidence_confidence: float
    confidence_label: str = "LOW"
    project_location: dict[str, Any] = Field(default_factory=dict)
    availability: dict[str, Any] = Field(default_factory=dict)
    location_analysis: dict[str, Any] | None = None
    temporal_analysis: dict[str, Any] | None = None
    change_analysis: dict[str, Any] | None = None
    resolution_analysis: dict[str, Any] | None = None
    image_gps_signals: list[dict[str, Any]] = Field(default_factory=list)
    scenes: list[dict[str, Any]] = Field(default_factory=list)
    work_scale: str | None = None
    limitations: list[str] = Field(default_factory=list)
    explanation: str
    finding: str = SATELLITE_UNAVAILABLE
    plan_claim_evidence: SatellitePceFramingRead | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    note: str = GOVERNANCE_NOTE
    engine_version: str
    labelled_synthetic: bool = False
    official_imagery: bool = False
    map_available: bool = False

    @field_validator("explanation", "note", "overall_result", "finding")
    @classmethod
    def no_fraud_text(cls, value: str) -> str:
        _reject_fraud(value)
        return value
