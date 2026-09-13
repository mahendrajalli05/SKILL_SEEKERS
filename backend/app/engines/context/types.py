"""Types for Real Contextual Data Enrichment V1."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from app.domain.enums import DataMode
from app.engines.context.constants import ENGINE_NAME, ENGINE_VERSION, GOVERNANCE_NOTE


@dataclass
class SourceRecord:
    source_id: str
    source_name: str
    publisher: str
    source_type: str
    url: str | None
    retrieval_date: str | None
    dataset_version: str | None
    geographic_level: str
    unit: str | None
    update_frequency: str | None
    license_note: str | None
    transformation_notes: str | None
    limitations: list[str]
    active: bool
    requires_credential: bool = False
    credential_env: str | None = None
    snapshot_relative_path: str | None = None
    real_mode_allowed: bool = True
    unavailable_reason: str | None = None
    indicators: list[str] = field(default_factory=list)
    alternate_url: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ContextObservation:
    indicator: str
    status: str
    value: float | int | str | None
    unit: str | None
    geographic_level: str | None
    geo_key: str | None
    reference_year: int | None
    reference_date: str | None
    source_id: str | None
    source_name: str | None
    publisher: str | None
    source_url: str | None
    retrieval_date: str | None
    dataset_version: str | None
    transformation: str | None
    limitations: list[str]
    data_mode: DataMode
    confidence: float
    quality: str
    context_kind: str
    failure_code: str | None = None
    derived: bool = False
    comparison: dict[str, Any] | None = None
    notes: str = ""
    assessment_kind: str | None = None

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["data_mode"] = self.data_mode.value
        return payload


@dataclass
class ContextResult:
    project_id: int | None
    internal_project_id: str
    engine: str = ENGINE_NAME
    engine_version: str = ENGINE_VERSION
    data_mode: DataMode = DataMode.REAL
    assessment_kind: str | None = None
    persisted: bool = False
    governance_note: str = GOVERNANCE_NOTE
    requested_geographic_level: str | None = None
    matched_geographic_level: str | None = None
    project_state: str | None = None
    project_constituency: str | None = None
    recommended_date: str | None = None
    allocation_amount: int | None = None
    observations: list[ContextObservation] = field(default_factory=list)
    unavailable_indicators: list[dict[str, Any]] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    snapshot_retrieval_at: str | None = None
    processing_version: str = ENGINE_VERSION
    cost_v1_1_unchanged: bool = True
    need_impact_formula_unchanged: bool = True
    risk_fusion_unchanged: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "internal_project_id": self.internal_project_id,
            "engine": self.engine,
            "engine_version": self.engine_version,
            "data_mode": self.data_mode.value,
            "assessment_kind": self.assessment_kind,
            "persisted": self.persisted,
            "governance_note": self.governance_note,
            "requested_geographic_level": self.requested_geographic_level,
            "matched_geographic_level": self.matched_geographic_level,
            "project_state": self.project_state,
            "project_constituency": self.project_constituency,
            "recommended_date": self.recommended_date,
            "allocation_amount": self.allocation_amount,
            "observations": [item.as_dict() for item in self.observations],
            "unavailable_indicators": list(self.unavailable_indicators),
            "evidence_ids": list(self.evidence_ids),
            "limitations": list(self.limitations),
            "snapshot_retrieval_at": self.snapshot_retrieval_at,
            "processing_version": self.processing_version,
            "cost_v1_1_unchanged": self.cost_v1_1_unchanged,
            "need_impact_formula_unchanged": self.need_impact_formula_unchanged,
            "risk_fusion_unchanged": self.risk_fusion_unchanged,
            "fraud_probability": None,
            "automatic_sanction": False,
        }
