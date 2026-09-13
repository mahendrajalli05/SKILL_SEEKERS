"""Need & Impact V1 typed payloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from app.domain.enums import DataMode
from app.engines.need.constants import GOVERNANCE_NOTE, INCONCLUSIVE, WEIGHT_NOTE


def _mode_value(value: DataMode | str) -> str:
    return value.value if isinstance(value, DataMode) else str(value)


@dataclass(frozen=True)
class SyntheticNeedImpactEnrichment:
    """TEST/SYNTHETIC prototype values. Never a government statistic."""

    internal_project_id: str
    label: str = "TEST/SYNTHETIC"
    population_need_index: float | None = None
    infrastructure_gap_index: float | None = None
    underserved_index: float | None = None
    beneficiary_count: int | None = None
    community_coverage_index: float | None = None
    disaster_flag: bool | None = None
    urgency_index: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "internal_project_id": self.internal_project_id,
            "label": self.label,
            "population_need_index": self.population_need_index,
            "infrastructure_gap_index": self.infrastructure_gap_index,
            "underserved_index": self.underserved_index,
            "beneficiary_count": self.beneficiary_count,
            "community_coverage_index": self.community_coverage_index,
            "disaster_flag": self.disaster_flag,
            "urgency_index": self.urgency_index,
            "synthetic": True,
            "note": "TEST/SYNTHETIC prototype enrichment. Not a government fact.",
        }


@dataclass
class SignalComponent:
    key: str
    label: str
    available: bool
    score: float | None
    weight: float
    source: str
    data_mode: str
    synthetic: bool = False
    unavailable_reason: str | None = None
    explanation: str = ""
    used_in_score: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "available": self.available,
            "score": self.score,
            "weight": self.weight,
            "source": self.source,
            "data_mode": self.data_mode,
            "synthetic": self.synthetic,
            "unavailable_reason": self.unavailable_reason,
            "explanation": self.explanation,
            "used_in_score": self.used_in_score,
        }


@dataclass
class ConstituencyContext:
    constituency: str
    usable_as_geography: bool
    constituency_work_count: int | None
    category_work_count: int | None
    locality_work_count: int | None
    locality_field: str | None
    reason: str
    used_as_need_score: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "constituency": self.constituency,
            "usable_as_geography": self.usable_as_geography,
            "constituency_work_count": self.constituency_work_count,
            "category_work_count": self.category_work_count,
            "locality_work_count": self.locality_work_count,
            "locality_field": self.locality_field,
            "reason": self.reason,
            "used_as_need_score": self.used_as_need_score,
            "note": (
                "Historical counts are contextual only and are not used as Need Score."
            ),
        }


@dataclass
class DimensionScore:
    name: str
    score: float | None
    available: bool
    confidence: float
    finding: str
    explanation: str
    components: list[SignalComponent] = field(default_factory=list)
    unavailable_inputs: list[str] = field(default_factory=list)
    top_reasons: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "score": self.score,
            "available": self.available,
            "confidence": self.confidence,
            "finding": self.finding,
            "explanation": self.explanation,
            "components": [item.as_dict() for item in self.components],
            "unavailable_inputs": list(self.unavailable_inputs),
            "top_reasons": list(self.top_reasons),
        }


@dataclass
class NeedImpactInputs:
    project_id: int
    internal_project_id: str
    state: str
    constituency: str
    constituency_usable: bool
    category: str
    work_description: str
    allocation_amount: int | None
    status: str
    recommended_date: date | None
    lifecycle_stage: str
    mp_name: str
    ida: str
    data_mode: DataMode
    village: str = ""
    block: str = ""
    city: str = ""
    enrichment: SyntheticNeedImpactEnrichment | None = None


@dataclass
class NeedImpactResult:
    project_id: int
    internal_project_id: str
    data_mode: DataMode
    constituency: str
    category: str
    work_description: str
    requested_amount: int | None
    lifecycle_stage: str
    status: str
    need: DimensionScore
    impact: DimensionScore
    urgency: DimensionScore
    priority_score: float | None
    priority_class: str
    evidence_confidence: float
    top_reasons: list[str]
    unavailable_inputs: list[str]
    contextual_evidence: list[str]
    explanation: str
    finding: str
    weights: dict[str, float]
    weight_note: str = WEIGHT_NOTE
    governance_note: str = GOVERNANCE_NOTE
    limitations: list[str] = field(default_factory=list)
    constituency_context: ConstituencyContext | None = None
    enrichment_used: bool = False
    enrichment_label: str | None = None
    automatic_sanction: bool = False
    evidence_ids: list[str] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)
    engine_version: str = ""
    engine_name: str = "need"

    def as_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "internal_project_id": self.internal_project_id,
            "data_mode": _mode_value(self.data_mode),
            "constituency": self.constituency,
            "category": self.category,
            "work_description": self.work_description,
            "requested_amount": self.requested_amount,
            "lifecycle_stage": self.lifecycle_stage,
            "status": self.status,
            "need_score": self.need.score,
            "impact_score": self.impact.score,
            "urgency_score": self.urgency.score,
            "priority_score": self.priority_score,
            "priority_class": self.priority_class,
            "evidence_confidence": self.evidence_confidence,
            "need": self.need.as_dict(),
            "impact": self.impact.as_dict(),
            "urgency": self.urgency.as_dict(),
            "top_reasons": list(self.top_reasons),
            "unavailable_inputs": list(self.unavailable_inputs),
            "contextual_evidence": list(self.contextual_evidence),
            "explanation": self.explanation,
            "finding": self.finding,
            "weights": dict(self.weights),
            "weight_note": self.weight_note,
            "governance_note": self.governance_note,
            "limitations": list(self.limitations),
            "constituency_context": (
                self.constituency_context.as_dict() if self.constituency_context else None
            ),
            "enrichment_used": self.enrichment_used,
            "enrichment_label": self.enrichment_label,
            "automatic_sanction": self.automatic_sanction,
            "sanction_decision": None,
            "evidence_ids": list(self.evidence_ids),
            "provenance": dict(self.provenance),
            "engine_version": self.engine_version,
            "engine_name": self.engine_name,
            "priority_recommendation_only": True,
            "planning_simulation": False,
        }


@dataclass
class RankedProject:
    rank: int | None
    project_id: int
    internal_project_id: str
    constituency: str
    category: str
    requested_amount: int | None
    priority_score: float | None
    priority_class: str
    evidence_confidence: float
    rationale: str
    why_ranked_above: str | None
    why_ranked_below: str | None
    within_hypothetical_budget: bool | None
    budget_note: str | None
    need_score: float | None
    impact_score: float | None
    data_mode: str
    finding: str
    top_reasons: list[str] = field(default_factory=list)
    unavailable_inputs: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "project_id": self.project_id,
            "internal_project_id": self.internal_project_id,
            "constituency": self.constituency,
            "category": self.category,
            "requested_amount": self.requested_amount,
            "priority_score": self.priority_score,
            "priority_class": self.priority_class,
            "evidence_confidence": self.evidence_confidence,
            "rationale": self.rationale,
            "why_ranked_above": self.why_ranked_above,
            "why_ranked_below": self.why_ranked_below,
            "within_hypothetical_budget": self.within_hypothetical_budget,
            "budget_note": self.budget_note,
            "need_score": self.need_score,
            "impact_score": self.impact_score,
            "data_mode": self.data_mode,
            "finding": self.finding,
            "top_reasons": list(self.top_reasons),
            "unavailable_inputs": list(self.unavailable_inputs),
            "automatic_sanction": False,
        }


@dataclass
class RankResult:
    items: list[RankedProject]
    unranked: list[RankedProject]
    available_budget: int | None
    available_budget_crore: float | None
    remaining_budget: int | None
    data_mode: str
    weight_note: str = WEIGHT_NOTE
    governance_note: str = GOVERNANCE_NOTE
    planning_simulation: bool = True
    automatic_sanction: bool = False
    explanation: str = ""
    engine_version: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "items": [item.as_dict() for item in self.items],
            "unranked": [item.as_dict() for item in self.unranked],
            "available_budget": self.available_budget,
            "available_budget_crore": self.available_budget_crore,
            "remaining_budget": self.remaining_budget,
            "data_mode": self.data_mode,
            "weight_note": self.weight_note,
            "governance_note": self.governance_note,
            "planning_simulation": self.planning_simulation,
            "automatic_sanction": self.automatic_sanction,
            "sanction_decision": None,
            "explanation": self.explanation,
            "engine_version": self.engine_version,
            "priority_recommendation_only": True,
        }
