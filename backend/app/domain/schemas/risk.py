from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.enums import (
    DataMode,
    FusionExplanationType,
    InvestigationPriorityBand,
    RecommendedAction,
    RiskSignalState,
)
from app.engines.fusion.constants import ENGINE_VERSION, GOVERNANCE_NOTE, WEIGHT_NOTE
from app.engines.fusion.types import FusionResult


class RiskSignalRead(BaseModel):
    signal_id: str
    display_name: str
    weight: float
    state: RiskSignalState
    risk_score: int | None = None
    contribution: float = 0.0
    evidence_confidence: float | None = None
    evidence_id: str | None = None
    disposition: str | None = None
    finding: str | None = None
    support: str | None = None
    unavailable_reason: str | None = None
    data_mode: str | None = None
    flagged: bool = False
    peer_quality: int | None = None


class ProjectRiskResponse(BaseModel):
    """Fused Investigation Priority for one project. Not a fraud probability."""

    model_config = ConfigDict(from_attributes=True)

    project_id: int
    internal_project_id: str | None = None
    investigation_priority: int = Field(ge=0, le=100)
    investigation_priority_0_100: float = Field(ge=0, le=100)
    raw_risk: float = Field(ge=0, le=100)
    evidence_confidence: int = Field(ge=0, le=100)
    priority_band: InvestigationPriorityBand
    explanation_type: FusionExplanationType
    explanation_types: list[str] = Field(default_factory=list)
    recommended_action: RecommendedAction
    data_mode: DataMode
    contributing_signals: list[RiskSignalRead] = Field(default_factory=list)
    unavailable_signals: list[RiskSignalRead] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    ignored_duplicate_evidence_ids: list[str] = Field(default_factory=list)
    explanation: str
    recommendation: str
    available_weight: float
    available_signal_weight: float
    unavailable_signal_weight: float
    unused_weight: float
    reserved_unavailable_weight: float
    evidence_coverage: float
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
    def from_result(cls, result: FusionResult) -> ProjectRiskResponse:
        return cls(
            project_id=result.project_id,
            internal_project_id=result.internal_project_id,
            investigation_priority=result.investigation_priority,
            investigation_priority_0_100=result.investigation_priority_0_100,
            raw_risk=result.raw_risk,
            evidence_confidence=result.evidence_confidence,
            priority_band=result.priority_band,
            explanation_type=result.explanation_type,
            explanation_types=list(result.explanation_types),
            recommended_action=result.recommended_action,
            data_mode=result.data_mode,
            contributing_signals=[
                RiskSignalRead.model_validate(item.as_payload())
                for item in result.contributing_signals
            ],
            unavailable_signals=[
                RiskSignalRead.model_validate(item.as_payload())
                for item in result.unavailable_signals
            ],
            evidence_ids=list(result.evidence_ids),
            ignored_duplicate_evidence_ids=list(result.ignored_duplicate_evidence_ids),
            explanation=result.explanation,
            recommendation=result.recommendation,
            available_weight=result.available_weight,
            available_signal_weight=result.available_signal_weight,
            unavailable_signal_weight=result.unavailable_signal_weight,
            unused_weight=result.unused_weight,
            reserved_unavailable_weight=result.reserved_unavailable_weight,
            evidence_coverage=result.evidence_coverage,
            engine_version=result.engine_version,
            weight_note=result.weight_note,
            note=result.governance_note,
        )


def response_as_dict(result: FusionResult) -> dict[str, Any]:
    return ProjectRiskResponse.from_result(result).model_dump(mode="json")
