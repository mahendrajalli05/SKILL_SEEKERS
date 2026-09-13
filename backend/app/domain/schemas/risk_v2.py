from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.enums import (
    DataMode,
    FusionExplanationType,
    InvestigationPriorityBand,
    RecommendedAction,
)
from app.engines.fusion_v2.constants import ENGINE_VERSION, GOVERNANCE_NOTE, WEIGHT_NOTE
from app.engines.fusion_v2.types import FusionV2Result, V2EvidenceState


class RiskV2ItemRead(BaseModel):
    evidence_id: str
    signal_type: str
    engine_name: str
    raw_evidence_score: int | None = None
    mapped_score: int | None = None
    confidence: float
    disposition: str
    data_mode: str
    source_ids: list[str] = Field(default_factory=list)
    finding: str | None = None


class RiskV2GroupRead(BaseModel):
    signal: str
    group_id: str
    display_name: str
    weight: float
    state: V2EvidenceState
    polarity: str
    raw_evidence_score: int | None = None
    confidence: float | None = None
    confidence_adjusted_score: float | None = None
    correlation_factor: float = 1.0
    correlation_reason: str | None = None
    dependency_correlation_adjustment: float = 1.0
    effective_contribution: float = 0.0
    evidence_ids: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    items: list[RiskV2ItemRead] = Field(default_factory=list)
    finding: str | None = None
    support: str | None = None
    unavailable_reason: str | None = None
    data_mode: str | None = None
    flagged: bool = False
    peer_quality: int | None = None
    independent: bool = True


class RiskV2ConflictRead(BaseModel):
    left_group: str
    right_group: str
    left_polarity: str
    right_polarity: str
    summary: str


class ProjectRiskV2Response(BaseModel):
    """Risk Fusion V2 Investigation Priority. Not a fraud probability."""

    model_config = ConfigDict(from_attributes=True)

    project_id: int
    internal_project_id: str | None = None
    investigation_priority: int = Field(ge=0, le=100)
    investigation_priority_0_100: float = Field(ge=0, le=100)
    raw_risk: float = Field(ge=0, le=100)
    evidence_confidence: int = Field(ge=0, le=100)
    risk_class: InvestigationPriorityBand
    explanation_type: FusionExplanationType
    explanation_types: list[str] = Field(default_factory=list)
    recommended_action: RecommendedAction
    data_mode: DataMode
    contributing_evidence_groups: list[RiskV2GroupRead] = Field(default_factory=list)
    independent_evidence_groups: list[RiskV2GroupRead] = Field(default_factory=list)
    discounted_correlated_evidence: list[RiskV2GroupRead] = Field(default_factory=list)
    unavailable_evidence: list[RiskV2GroupRead] = Field(default_factory=list)
    not_assessable_evidence: list[RiskV2GroupRead] = Field(default_factory=list)
    conflicting_evidence: list[RiskV2ConflictRead] = Field(default_factory=list)
    evidence_contribution_breakdown: list[RiskV2GroupRead] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    ignored_duplicate_evidence_ids: list[str] = Field(default_factory=list)
    explanation: str
    recommendation: str
    available_weight: float
    unavailable_weight: float
    evidence_coverage: float
    synthetic_disclosure: str | None = None
    evidence_fingerprint: str
    engine_version: str = ENGINE_VERSION
    weight_note: str = WEIGHT_NOTE
    note: str = GOVERNANCE_NOTE

    @field_validator("investigation_priority", "evidence_confidence")
    @classmethod
    def bounded(cls, value: int) -> int:
        if value < 0 or value > 100:
            raise ValueError("Scores must be between 0 and 100.")
        return value

    @classmethod
    def from_result(cls, result: FusionV2Result) -> ProjectRiskV2Response:
        breakdown = [RiskV2GroupRead.model_validate(item.as_payload()) for item in result.all_groups]
        return cls(
            project_id=result.project_id,
            internal_project_id=result.internal_project_id,
            investigation_priority=result.investigation_priority,
            investigation_priority_0_100=result.investigation_priority_0_100,
            raw_risk=result.raw_risk,
            evidence_confidence=result.evidence_confidence,
            risk_class=result.risk_class,
            explanation_type=result.explanation_type,
            explanation_types=list(result.explanation_types),
            recommended_action=result.recommended_action,
            data_mode=result.data_mode,
            contributing_evidence_groups=[
                RiskV2GroupRead.model_validate(item.as_payload())
                for item in result.contributing_evidence_groups
            ],
            independent_evidence_groups=[
                RiskV2GroupRead.model_validate(item.as_payload())
                for item in result.independent_evidence_groups
            ],
            discounted_correlated_evidence=[
                RiskV2GroupRead.model_validate(item.as_payload())
                for item in result.discounted_correlated_evidence
            ],
            unavailable_evidence=[
                RiskV2GroupRead.model_validate(item.as_payload())
                for item in result.unavailable_evidence
            ],
            not_assessable_evidence=[
                RiskV2GroupRead.model_validate(item.as_payload())
                for item in result.not_assessable_evidence
            ],
            conflicting_evidence=[
                RiskV2ConflictRead.model_validate(item.as_payload())
                for item in result.conflicting_evidence
            ],
            evidence_contribution_breakdown=breakdown,
            evidence_ids=list(result.evidence_ids),
            ignored_duplicate_evidence_ids=list(result.ignored_duplicate_evidence_ids),
            explanation=result.explanation,
            recommendation=result.recommendation,
            available_weight=result.available_weight,
            unavailable_weight=result.unavailable_weight,
            evidence_coverage=result.evidence_coverage,
            synthetic_disclosure=result.synthetic_disclosure,
            evidence_fingerprint=result.evidence_fingerprint,
            engine_version=result.engine_version,
            weight_note=result.weight_note,
            note=result.governance_note,
        )


def response_as_dict_v2(result: FusionV2Result) -> dict[str, Any]:
    return ProjectRiskV2Response.from_result(result).model_dump(mode="json")
