from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator, model_serializer

from app.domain.enums import DataMode
from app.engines.citizen.constants import GOVERNANCE_NOTE, PRIVACY_NOTE, THRESHOLD_NOTE


def _reject_forbidden(value: object) -> object:
    if isinstance(value, str):
        folded = value.casefold()
        for term in ("fraud", "fraudulent", "fraud probability"):
            if term in folded:
                raise ValueError("Jan-Sakshi must not claim fraud.")
    return value


class CitizenReportCreate(BaseModel):
    satisfaction_rating: int | None = None
    observation_text: str | None = None
    issue_category: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    capture_timestamp: str | None = None
    data_mode: str | None = None

    @field_validator("observation_text", "issue_category")
    @classmethod
    def no_forbidden(cls, value: str | None) -> str | None:
        _reject_forbidden(value)
        return value


class CitizenReportRead(BaseModel):
    citizen_report_id: int
    project_id: int
    scheme_id: str | None = None
    internal_project_id: str
    satisfaction_rating: int | None = None
    observation_text: str | None = None
    issue_category: str | None = None
    submitted_at: str | None = None
    image_id: int | None = None
    submission_status: str
    verification_result: str
    timestamp_status: str
    data_mode: DataMode | str
    provenance: dict[str, Any] = Field(default_factory=dict)
    location_verification: dict[str, Any] = Field(default_factory=dict)
    analysis: dict[str, Any] | None = None
    duplicate: dict[str, Any] | None = None
    watermark: dict[str, Any] | None = None
    plan_claim_evidence: dict[str, Any] | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    rejection_reason: str | None = None
    reasons: list[str] = Field(default_factory=list)
    synthetic: bool = False
    synthetic_badge: str | None = None
    image_hash: str | None = None
    image_metadata: dict[str, Any] | None = None
    thumbnail_data_url: str | None = None
    original_image_preserved: bool = True
    privacy: dict[str, Any] = Field(default_factory=dict)
    engine_version: str
    engine_name: str = "citizen"
    governance_note: str = GOVERNANCE_NOTE
    latitude: float | None = None
    longitude: float | None = None
    location_included: bool = False

    @field_validator("governance_note", "rejection_reason")
    @classmethod
    def no_forbidden(cls, value: str | None) -> str | None:
        _reject_forbidden(value)
        return value

    @model_serializer(mode="wrap")
    def omit_private_gps(self, handler):
        payload = handler(self)
        if not self.location_included:
            payload.pop("latitude", None)
            payload.pop("longitude", None)
        return payload


class CitizenReportListResponse(BaseModel):
    project_id: int
    internal_project_id: str
    data_mode: DataMode | str
    items: list[CitizenReportRead] = Field(default_factory=list)
    privacy_note: str = PRIVACY_NOTE
    threshold_note: str = THRESHOLD_NOTE
    governance_note: str = GOVERNANCE_NOTE
    engine_version: str
    engine_name: str = "citizen"


class CitizenSummaryRead(BaseModel):
    project_id: int
    internal_project_id: str
    scheme_id: str | None = None
    data_mode: DataMode | str
    total_submissions: int
    verified_location_submissions: int
    rejected_submissions: int
    inconclusive_submissions: int
    average_satisfaction: float | None = None
    satisfaction_distribution: dict[str, int] = Field(default_factory=dict)
    recurring_issue_categories: list[dict[str, Any]] = Field(default_factory=list)
    repeated_complaint_themes: list[str] = Field(default_factory=list)
    citizen_evidence_confidence: float
    sample_size_status: str
    aggregate_finding: str
    explanation: str
    provenance: dict[str, Any] = Field(default_factory=dict)
    synthetic_badge: str | None = None
    investigation_priority_unchanged: bool = True
    evidence_ids: list[str] = Field(default_factory=list)
    engine_version: str
    engine_name: str = "citizen"
    governance_note: str = GOVERNANCE_NOTE
    privacy_note: str = PRIVACY_NOTE
    limitations: list[str] = Field(default_factory=list)
    threshold_note: str = THRESHOLD_NOTE

    @field_validator("explanation", "aggregate_finding", "governance_note")
    @classmethod
    def no_forbidden(cls, value: str) -> str:
        _reject_forbidden(value)
        return value
