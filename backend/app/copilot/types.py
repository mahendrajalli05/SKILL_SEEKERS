"""Investigation Copilot V1 types."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.domain.enums import DataMode


class CopilotIntent(str, Enum):
    WHY_FLAGGED = "WHY_FLAGGED"
    WHY_NOT_FLAGGED = "WHY_NOT_FLAGGED"
    STRONGEST_EVIDENCE = "STRONGEST_EVIDENCE"
    MISSING_INFORMATION = "MISSING_INFORMATION"
    TIME_INCONCLUSIVE = "TIME_INCONCLUSIVE"
    COMPARABLES = "COMPARABLES"
    PCE_SUMMARY = "PCE_SUMMARY"
    INSPECT_NEXT = "INSPECT_NEXT"
    COMPLIANCE = "COMPLIANCE"
    CITIZEN = "CITIZEN"
    SATELLITE = "SATELLITE"
    GEOSPATIAL = "GEOSPATIAL"
    SIGNALS = "SIGNALS"
    MILESTONE = "MILESTONE"
    GRAPH = "GRAPH"
    DOCUMENTS = "DOCUMENTS"
    IMAGES = "IMAGES"
    FORENSICS = "FORENSICS"
    NEED_IMPACT = "NEED_IMPACT"
    RISK_V2_CONTRIBUTION = "RISK_V2_CONTRIBUTION"
    RISK_V2_CORRELATED = "RISK_V2_CORRELATED"
    RISK_V2_CONFLICTING = "RISK_V2_CONFLICTING"
    RISK_V2_SCORE_CHANGE = "RISK_V2_SCORE_CHANGE"
    LIFECYCLE_WHERE = "LIFECYCLE_WHERE"
    LIFECYCLE_REMAINING = "LIFECYCLE_REMAINING"
    LIFECYCLE_LAST_MILESTONE = "LIFECYCLE_LAST_MILESTONE"
    PROJECT_OVERVIEW = "PROJECT_OVERVIEW"
    ML_EVIDENCE = "ML_EVIDENCE"
    ML_FRAUD_CLARIFICATION = "ML_FRAUD_CLARIFICATION"
    EXTERNAL_CONTEXT = "EXTERNAL_CONTEXT"
    FORBIDDEN_LEGAL = "FORBIDDEN_LEGAL"
    GENERAL = "GENERAL"


class CopilotProviderName(str, Enum):
    DETERMINISTIC = "deterministic"
    LOCAL = "local"
    EXTERNAL = "external"
    DISABLED = "disabled"


class CopilotRecommendation(str, Enum):
    MONITOR = "MONITOR"
    REVIEW = "REVIEW"
    INSPECT = "INSPECT"
    NEED_MORE_INFORMATION = "NEED MORE INFORMATION"


@dataclass
class SourceRef:
    id: str
    kind: str
    label: str

    def as_dict(self) -> dict[str, str]:
        return {"id": self.id, "kind": self.kind, "label": self.label}


@dataclass
class EvidenceSlice:
    evidence_id: str
    engine: str
    signal_type: str
    finding: str
    explanation: str
    disposition: str
    status: str
    score: float | int | None
    confidence: float
    data_mode: str
    facts_observed: list[dict[str, Any]]
    facts_derived: list[dict[str, Any]]
    comparables: list[Any]
    rule_ids: list[str]
    guideline_refs: list[str]


@dataclass
class RiskSlice:
    investigation_priority: int | None
    investigation_priority_0_100: float | None
    evidence_confidence: int | None
    explanation_type: str | None
    explanation: str | None
    recommended_action: str | None
    contributing: list[dict[str, Any]]
    unavailable: list[dict[str, Any]]
    evidence_ids: list[str]
    data_mode: str | None
    stored: bool


@dataclass
class RiskV2Slice:
    investigation_priority: int | None
    evidence_confidence: int | None
    risk_class: str | None
    explanation_type: str | None
    explanation: str | None
    recommended_action: str | None
    contributing: list[dict[str, Any]]
    independent: list[dict[str, Any]]
    discounted: list[dict[str, Any]]
    unavailable: list[dict[str, Any]]
    conflicting: list[dict[str, Any]]
    breakdown: list[dict[str, Any]]
    evidence_ids: list[str]
    data_mode: str | None
    synthetic_disclosure: str | None
    stored: bool


@dataclass
class LifecycleSlice:
    lifecycle_state: str | None
    source_status: str | None
    current_stage: str | None
    planning_state: str | None
    completed_stages: list[str]
    pending_stages: list[str]
    timeline: list[dict[str, Any]]
    recommendation: str | None
    last_milestone_decision: str | None
    missing: list[str]
    data_mode: str | None
    explanation: str | None


@dataclass
class InvestigationBundle:
    project_id: int
    internal_project_id: str
    scheme_id: str | None
    data_mode: DataMode
    is_synthetic: bool
    hybrid_enrichment: bool
    work_description: str | None
    constituency: str | None
    category: str | None
    status: str | None
    allocation_amount: int | None
    recommended_date: str | None
    mp_name: str | None
    state: str | None
    unavailable_fields: list[dict[str, str]]
    evidence: list[EvidenceSlice]
    risk: RiskSlice | None
    pce: dict[str, Any] | None
    documents: list[dict[str, Any]]
    images: dict[str, Any] | None
    citizen_reports: list[dict[str, Any]]
    citizen_summary: dict[str, Any] | None
    milestones: dict[str, Any] | None
    semantic_hits: list[dict[str, Any]] = field(default_factory=list)
    risk_v2: RiskV2Slice | None = None
    lifecycle: LifecycleSlice | None = None


@dataclass
class CopilotSections:
    answer: str
    why: str
    evidence: str
    missing: str
    recommended_action: str

    def render(self) -> str:
        return (
            f"ANSWER:\n{self.answer.strip()}\n\n"
            f"WHY:\n{self.why.strip()}\n\n"
            f"EVIDENCE:\n{self.evidence.strip()}\n\n"
            f"MISSING INFORMATION:\n{self.missing.strip()}\n\n"
            f"RECOMMENDED ACTION:\n{self.recommended_action.strip()}"
        )


@dataclass
class CopilotDraft:
    sections: CopilotSections
    evidence_ids: list[str]
    source_refs: list[SourceRef]
    limitations: list[str]
    recommended_action: CopilotRecommendation
    observed_facts: list[str]
    derived_findings: list[str]
    unavailable: list[str]
    insufficient_evidence: bool
    provider: CopilotProviderName
    used_llm: bool = False


@dataclass
class CopilotTurnRecord:
    session_id: str
    question: str
    answer: str
    intent: str
    data_mode: str
    evidence_ids: list[str]
    recommended_action: str | None
    provider: str
    created_at: str | None = None
