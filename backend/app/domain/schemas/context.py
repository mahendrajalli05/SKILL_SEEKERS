from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import DataMode


class ContextObservationRead(BaseModel):
    model_config = ConfigDict(extra="ignore")

    indicator: str
    status: str
    value: float | int | str | None = None
    unit: str | None = None
    geographic_level: str | None = None
    geo_key: str | None = None
    reference_year: int | None = None
    reference_date: str | None = None
    source_id: str | None = None
    source_name: str | None = None
    publisher: str | None = None
    source_url: str | None = None
    retrieval_date: str | None = None
    dataset_version: str | None = None
    transformation: str | None = None
    limitations: list[str] = Field(default_factory=list)
    data_mode: str
    confidence: float
    quality: str
    context_kind: str
    failure_code: str | None = None
    derived: bool = False
    comparison: dict | None = None
    notes: str = ""
    assessment_kind: str | None = None


class ContextUnavailableRead(BaseModel):
    indicator: str
    status: str
    failure_code: str | None = None
    source_id: str | None = None
    notes: str | None = None


class ProjectContextRead(BaseModel):
    project_id: int | None
    internal_project_id: str
    engine: str
    engine_version: str
    data_mode: str
    assessment_kind: str | None = None
    persisted: bool = False
    governance_note: str
    requested_geographic_level: str | None = None
    matched_geographic_level: str | None = None
    project_state: str | None = None
    project_constituency: str | None = None
    recommended_date: str | None = None
    allocation_amount: int | None = None
    observations: list[ContextObservationRead] = Field(default_factory=list)
    unavailable_indicators: list[ContextUnavailableRead] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    snapshot_retrieval_at: str | None = None
    processing_version: str
    cost_v1_1_unchanged: bool = True
    need_impact_formula_unchanged: bool = True
    risk_fusion_unchanged: bool = True
    fraud_probability: None = None
    automatic_sanction: bool = False


class ContextSourceRead(BaseModel):
    source_id: str
    source_name: str
    publisher: str
    source_type: str
    url: str | None = None
    retrieval_date: str | None = None
    dataset_version: str | None = None
    geographic_level: str
    unit: str | None = None
    update_frequency: str | None = None
    license_note: str | None = None
    transformation_notes: str | None = None
    limitations: list[str] = Field(default_factory=list)
    active: bool
    requires_credential: bool = False
    real_mode_allowed: bool = True
    unavailable_reason: str | None = None
    indicators: list[str] = Field(default_factory=list)


class ContextSourceListRead(BaseModel):
    registry_version: str = "context-sources-v1"
    items: list[ContextSourceRead]
    data_mode: DataMode | None = None
