from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import EvidenceSeverity, EvidenceStatus
from app.engines.compliance.constants import ENGINE_NAME, ENGINE_VERSION, EVIDENCE_TYPE
from app.engines.compliance.types import (
    ComplianceIntelligenceResult,
    ComplianceMode,
    ComplianceStatus,
    RuleResultStatus,
)


class ComplianceRuleResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rule_id: str
    category: str
    title: str
    description: str
    status: RuleResultStatus
    severity: str
    explanation: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    source_reference: dict[str, Any] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class ComplianceIntelligenceResponse(BaseModel):
    """Guideline-rule evaluation for one work. Investigation Priority is not assigned here."""

    project_id: int
    internal_project_id: str
    engine: str = ENGINE_NAME
    engine_version: str = ENGINE_VERSION
    evidence_type: str = EVIDENCE_TYPE
    dataset_type: str
    compliance_mode: ComplianceMode
    compliance_status: ComplianceStatus
    flagged: bool
    status: EvidenceStatus
    severity: EvidenceSeverity
    signal_kind: str
    triggered_rules: list[ComplianceRuleResultRead] = Field(default_factory=list)
    non_triggered_rules: list[ComplianceRuleResultRead] = Field(default_factory=list)
    not_assessable_rules: list[ComplianceRuleResultRead] = Field(default_factory=list)
    explanation: str
    observed_status: str = ""
    lifecycle_stage: str = ""
    category: str = ""
    constituency: str = ""
    recommended_date: date | None = None
    allocation_amount: int | None = None
    ida: str = ""
    house: str = ""
    triggered_rule_ids: list[str] = Field(default_factory=list)
    not_assessable_rule_ids: list[str] = Field(default_factory=list)
    guideline_refs: list[str] = Field(default_factory=list)

    @classmethod
    def from_result(cls, result: ComplianceIntelligenceResult) -> ComplianceIntelligenceResponse:
        return cls.model_validate(result, from_attributes=True)
