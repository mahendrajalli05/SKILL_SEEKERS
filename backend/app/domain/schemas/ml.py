from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MlPredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: str | None = None
    constituency: str | None = None
    category: str | None = None
    work_description: str | None = None
    allocation_amount: int | float | None = None
    recommendation_date: date | None = None
    status: str | None = None
    house: str | None = None
    planned_start_date: date | None = None
    planned_completion_date: date | None = None
    physical_progress_percent: int | None = Field(default=None, ge=0, le=100)
    data_mode: Literal["REAL", "HYBRID", "SYNTHETIC"] = "REAL"
    model_version: str | None = None

    @field_validator("allocation_amount")
    @classmethod
    def _amount(cls, value: int | float | None) -> int | None:
        if value is None:
            return None
        return int(value)


class FeatureAvailabilityRead(BaseModel):
    available: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    unseen: list[str] = Field(default_factory=list)
    unsupported: list[str] = Field(default_factory=list)
    coverage: float = 0.0


class FeatureContributionRead(BaseModel):
    feature: str
    value: Any = None
    contribution: float
    note: str


class MlSignalRead(BaseModel):
    model_name: str
    model_version: str | None = None
    model_type: str
    training_mode: str
    training_data_hash: str | None = None
    feature_schema_version: str | None = None
    created_at: str | None = None
    status: str
    ml_anomaly_score: int | None = None
    decision_label: str | None = None
    feature_availability: FeatureAvailabilityRead
    feature_values: dict[str, Any] = Field(default_factory=dict)
    contributions: list[FeatureContributionRead] = Field(default_factory=list)
    explanation: str
    limitations: list[str] = Field(default_factory=list)
    data_mode: str
    fraud_probability: None = None


class MlPredictResponse(BaseModel):
    data_mode: str
    model_versions: dict[str, str | None]
    predictions: dict[str, MlSignalRead | None]
    anomaly_signals: list[str] = Field(default_factory=list)
    explanation: str
    limitations: list[str] = Field(default_factory=list)
    feature_availability: FeatureAvailabilityRead | None = None
    fraud_probability: None = None
    automatic_sanction: bool = False
    automatic_payment: bool = False
    assessment_kind: str = "NEW_PROJECT_ASSESSMENT"
    evidence_kind: str = "NEW_PROJECT_ASSESSMENT"
    persisted: bool = False


class ProjectAssessRequest(MlPredictRequest):
    pass


class ProjectAssessResponse(BaseModel):
    assessment_kind: str
    is_new_project: bool
    project_id: int | None
    data_mode: str
    ml: dict[str, Any]
    cost_v1_1: dict[str, Any] | None
    time_v1: dict[str, Any] | None
    overlap_v1: dict[str, Any] | None
    compliance_v1: dict[str, Any] | None
    risk_fusion_v2: dict[str, Any]
    limitations: list[str]
    fraud_probability: None = None
    automatic_sanction: bool = False
    automatic_payment: bool = False
    pfms_integrated: bool = False
    evidence_kind: str = "NEW_PROJECT_ASSESSMENT"
    persisted: bool = False
    contextual_v1: dict[str, Any] | None = None


class MlEvidenceCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data_mode: Literal["REAL", "HYBRID", "SYNTHETIC"] = "REAL"
    model_version: str | None = None


class MlEvidenceCreateResponse(BaseModel):
    assessment_kind: str
    evidence_kind: str
    persisted: bool
    project_id: int
    internal_project_id: str
    evidence_id: str
    signal_type: str
    finding: str
    disposition: str
    ml_anomaly_score: int | None
    confidence: float
    data_mode: str
    model_name: str | None
    model_version: str | None
    feature_schema_version: str | None
    training_data_hash: str | None
    training_mode: str | None
    explanation: str
    limitations: list[str] = Field(default_factory=list)
    feature_availability: FeatureAvailabilityRead | dict[str, Any]
    fraud_probability: None = None
    evidence: dict[str, Any]
