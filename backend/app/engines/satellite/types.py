"""Satellite / Remote-Sensing Consistency V1 typed payloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from app.domain.enums import DataMode
from app.engines.geo.types import ImageLocation, ProjectLocation
from app.engines.satellite.constants import SATELLITE_UNAVAILABLE


@dataclass
class ImageryRequest:
    latitude: float | None
    longitude: float | None
    date_start: date | None
    date_end: date | None
    aoi_radius_m: float
    data_mode: DataMode
    test_scenario: str | None = None
    work_scale: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "date_start": self.date_start.isoformat() if self.date_start else None,
            "date_end": self.date_end.isoformat() if self.date_end else None,
            "aoi_radius_m": self.aoi_radius_m,
            "data_mode": self.data_mode.value,
            "test_scenario": self.test_scenario,
            "work_scale": self.work_scale,
        }


@dataclass
class ImageryScene:
    provider: str
    image_reference: str
    acquisition_date: str | None
    spatial_resolution_m: float | None
    cloud_cover_percent: float | None
    quality: str | None
    covers_site: bool | None
    scene_latitude: float | None = None
    scene_longitude: float | None = None
    official_imagery: bool = False
    labelled_synthetic: bool = False
    visible_site_change: bool | None = None
    notes: str = ""
    role: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "image_reference": self.image_reference,
            "acquisition_date": self.acquisition_date,
            "spatial_resolution_m": self.spatial_resolution_m,
            "cloud_cover_percent": self.cloud_cover_percent,
            "quality": self.quality,
            "covers_site": self.covers_site,
            "scene_latitude": self.scene_latitude,
            "scene_longitude": self.scene_longitude,
            "official_imagery": self.official_imagery,
            "labelled_synthetic": self.labelled_synthetic,
            "visible_site_change": self.visible_site_change,
            "notes": self.notes,
            "role": self.role,
        }


@dataclass
class ImageryAvailability:
    available: bool
    provider: str
    reason: str
    scenes: list[ImageryScene] = field(default_factory=list)
    labelled_synthetic: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "available": self.available,
            "provider": self.provider,
            "reason": self.reason,
            "scenes": [item.as_dict() for item in self.scenes],
            "labelled_synthetic": self.labelled_synthetic,
        }


@dataclass
class LocationAnalysis:
    result: str
    covers_claimed_site: bool | None
    finding: str
    explanation: str
    distance_to_scene_m: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "result": self.result,
            "covers_claimed_site": self.covers_claimed_site,
            "finding": self.finding,
            "explanation": self.explanation,
            "distance_to_scene_m": self.distance_to_scene_m,
        }


@dataclass
class TemporalAnalysis:
    result: str
    finding: str
    explanation: str
    planned_date: str | None = None
    claimed_completion_date: str | None = None
    milestone_date: str | None = None
    imagery_dates: list[str] = field(default_factory=list)
    window_matches_claim: bool | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "result": self.result,
            "finding": self.finding,
            "explanation": self.explanation,
            "planned_date": self.planned_date,
            "claimed_completion_date": self.claimed_completion_date,
            "milestone_date": self.milestone_date,
            "imagery_dates": self.imagery_dates,
            "window_matches_claim": self.window_matches_claim,
        }


@dataclass
class ChangeAnalysis:
    result: str
    finding: str
    explanation: str
    before_reference: str | None = None
    after_reference: str | None = None
    visible_site_change: bool | None = None
    assessed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "result": self.result,
            "finding": self.finding,
            "explanation": self.explanation,
            "before_reference": self.before_reference,
            "after_reference": self.after_reference,
            "visible_site_change": self.visible_site_change,
            "assessed": self.assessed,
        }


@dataclass
class ResolutionAnalysis:
    result: str
    work_scale: str
    spatial_resolution_m: float | None
    useful_gsd_limit_m: float
    sufficient: bool | None
    finding: str
    explanation: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "result": self.result,
            "work_scale": self.work_scale,
            "spatial_resolution_m": self.spatial_resolution_m,
            "useful_gsd_limit_m": self.useful_gsd_limit_m,
            "sufficient": self.sufficient,
            "finding": self.finding,
            "explanation": self.explanation,
        }


@dataclass
class ImageGpsSignal:
    image_id: int
    image_gps_available: bool
    project_location_available: bool
    satellite_covers_project: bool | None
    satellite_covers_image_gps: bool | None
    note: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "image_id": self.image_id,
            "image_gps_available": self.image_gps_available,
            "project_location_available": self.project_location_available,
            "satellite_covers_project": self.satellite_covers_project,
            "satellite_covers_image_gps": self.satellite_covers_image_gps,
            "note": self.note,
        }


@dataclass
class PlanClaimEvidenceFraming:
    claim: str | None
    satellite: str
    result: str
    note: str
    claim_marked_false: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "claim": self.claim,
            "satellite": self.satellite,
            "result": self.result,
            "note": self.note,
            "claim_marked_false": self.claim_marked_false,
        }


@dataclass
class SatelliteResult:
    project_id: int
    internal_project_id: str
    data_mode: DataMode
    overall_result: str = SATELLITE_UNAVAILABLE
    provider: str = "unavailable"
    imagery_available: bool = False
    acquisition_date: str | None = None
    spatial_resolution_m: float | None = None
    coverage: str | None = None
    change_result: str | None = None
    evidence_confidence: float = 0.0
    confidence_label: str = "LOW"
    project_location: dict[str, Any] = field(default_factory=dict)
    availability: dict[str, Any] = field(default_factory=dict)
    location_analysis: dict[str, Any] | None = None
    temporal_analysis: dict[str, Any] | None = None
    change_analysis: dict[str, Any] | None = None
    resolution_analysis: dict[str, Any] | None = None
    image_gps_signals: list[dict[str, Any]] = field(default_factory=list)
    scenes: list[dict[str, Any]] = field(default_factory=list)
    work_scale: str | None = None
    limitations: list[str] = field(default_factory=list)
    explanation: str = ""
    finding: str = SATELLITE_UNAVAILABLE
    plan_claim_evidence: PlanClaimEvidenceFraming | None = None
    evidence_ids: list[str] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)
    note: str = ""
    engine_version: str = ""
    labelled_synthetic: bool = False
    official_imagery: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "internal_project_id": self.internal_project_id,
            "data_mode": self.data_mode.value,
            "overall_result": self.overall_result,
            "provider": self.provider,
            "imagery_available": self.imagery_available,
            "acquisition_date": self.acquisition_date,
            "spatial_resolution_m": self.spatial_resolution_m,
            "coverage": self.coverage,
            "change_result": self.change_result,
            "evidence_confidence": self.evidence_confidence,
            "confidence_label": self.confidence_label,
            "project_location": self.project_location,
            "availability": self.availability,
            "location_analysis": self.location_analysis,
            "temporal_analysis": self.temporal_analysis,
            "change_analysis": self.change_analysis,
            "resolution_analysis": self.resolution_analysis,
            "image_gps_signals": self.image_gps_signals,
            "scenes": self.scenes,
            "work_scale": self.work_scale,
            "limitations": self.limitations,
            "explanation": self.explanation,
            "finding": self.finding,
            "plan_claim_evidence": (
                self.plan_claim_evidence.as_dict() if self.plan_claim_evidence else None
            ),
            "evidence_ids": self.evidence_ids,
            "provenance": self.provenance,
            "note": self.note,
            "engine_version": self.engine_version,
            "labelled_synthetic": self.labelled_synthetic,
            "official_imagery": self.official_imagery,
            "map_available": False,
        }
