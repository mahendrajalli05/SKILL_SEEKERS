"""Dataclasses for Compliance Engine V1."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any

from app.domain.enums import EvidenceSeverity, EvidenceStatus


class ComplianceMode(str, Enum):
    REAL = "REAL"
    HYBRID_TEST = "HYBRID_TEST"


class RuleResultStatus(str, Enum):
    TRIGGERED = "TRIGGERED"
    NOT_TRIGGERED = "NOT_TRIGGERED"
    NOT_ASSESSABLE = "NOT_ASSESSABLE"


class ComplianceStatus(str, Enum):
    RULES_TRIGGERED = "RULES_TRIGGERED"
    NO_RULES_TRIGGERED = "NO_RULES_TRIGGERED"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass(frozen=True)
class SourceReference:
    document: str
    para: str | None
    source_id: str
    url: str
    quote: str


@dataclass(frozen=True)
class ComplianceRule:
    rule_id: str
    category: str
    title: str
    description: str
    severity: str
    required_fields: tuple[str, ...]
    evaluation_logic: dict[str, Any]
    source_reference: SourceReference
    limitations: tuple[str, ...]
    not_assessable_template: str


@dataclass(frozen=True)
class RuleSet:
    engine: str
    engine_version: str
    guideline_document: str
    effective_from: str
    disclaimer: str
    sources: tuple[dict[str, str], ...]
    rules: tuple[ComplianceRule, ...]


@dataclass
class RuleResult:
    rule_id: str
    category: str
    title: str
    description: str
    status: RuleResultStatus
    severity: str
    explanation: str
    evidence: dict[str, Any]
    source_reference: dict[str, Any]
    missing_fields: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ComplianceContext:
    """Observed and optional HYBRID execution fields. Never holds held-out labels."""

    project_id: int
    internal_project_id: str
    mode: ComplianceMode
    mp_name: str
    work_description: str
    category: str
    state: str
    constituency: str
    ida: str
    city: str
    ward: str
    block: str
    village: str
    recommended_date: date | None
    allocation_amount: int | None
    ida_approval: str
    status: str
    house: str
    lifecycle_stage: str
    observation_date: date | None = None
    as_of_date: date | None = None
    sanction_date: date | None = None
    planned_start_date: date | None = None
    planned_completion_date: date | None = None
    actual_start_date: date | None = None
    actual_completion_date: date | None = None
    sanctioned_amount: int | None = None
    expenditure_amount: int | None = None
    physical_progress_percent: int | None = None
    first_payment_date: date | None = None
    amount_unit: str | None = None
    verified_work_district: str | None = None
    vendor_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    mp_sc_share_percent: float | None = None
    mp_st_share_percent: float | None = None
    mp_fy_sanctioned_total: int | None = None
    mp_entitlement_upto_year: int | None = None
    outside_constituency_fy_amount: int | None = None
    official_ineligible_work_match: bool | None = None
    statutory_clearance_evidence: bool | None = None
    user_agency_om_undertaking: bool | None = None
    plaque_evidence: bool | None = None
    mp_recommendation_geography_ok: bool | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    def field_value(self, name: str) -> Any:
        if name in self.extras:
            return self.extras[name]
        return getattr(self, name, None)


@dataclass
class ComplianceIntelligenceResult:
    project_id: int
    internal_project_id: str
    engine: str
    engine_version: str
    evidence_type: str
    dataset_type: str
    compliance_mode: ComplianceMode
    compliance_status: ComplianceStatus
    flagged: bool
    status: EvidenceStatus
    severity: EvidenceSeverity
    signal_kind: str
    triggered_rules: list[RuleResult] = field(default_factory=list)
    non_triggered_rules: list[RuleResult] = field(default_factory=list)
    not_assessable_rules: list[RuleResult] = field(default_factory=list)
    rule_results: list[RuleResult] = field(default_factory=list)
    explanation: str = ""
    observed_status: str = ""
    lifecycle_stage: str = ""
    category: str = ""
    constituency: str = ""
    recommended_date: date | None = None
    allocation_amount: int | None = None
    ida: str = ""
    house: str = ""
    triggered_rule_ids: list[str] = field(default_factory=list)
    not_assessable_rule_ids: list[str] = field(default_factory=list)
    guideline_refs: list[str] = field(default_factory=list)
