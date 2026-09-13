"""Plan–Claim–Evidence V1 typed payloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.domain.enums import DataMode


class ConsistencyStatus(str, Enum):
    CONSISTENT = "CONSISTENT"
    MISMATCH = "MISMATCH"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass(frozen=True)
class PlanField:
    name: str
    value: Any
    available: bool
    data_mode: DataMode
    synthetic: bool
    source: str
    unavailable_reason: str | None = None


@dataclass
class AssembledPlan:
    project_id: int
    internal_project_id: str
    data_mode: DataMode
    sanctioned_scope: str | None
    budget_estimate: float | None
    budget_from_extract: bool
    blueprint_document_id: int | None
    dimensions_value: float | None
    dimensions_unit: str | None
    milestone_label: str | None
    milestone_amount: float | None
    planned_start_date: str | None
    planned_completion_date: str | None
    source: str
    provenance: dict[str, Any]
    fields: list[PlanField] = field(default_factory=list)
    recorded: bool = False


@dataclass
class AssembledClaim:
    project_id: int
    claim_id: int | None
    data_mode: DataMode
    claimed_progress: str | None
    claimed_progress_percent: float | None
    claimed_expenditure: float | None
    claimed_completion_state: str | None
    claimed_quantity: float | None
    claimed_quantity_unit: str | None
    milestone_claimed: str | None
    claim_date: str | None
    claimant_source: str | None
    supporting_document_ids: list[int] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)
    recorded: bool = False


@dataclass
class AssembledEvidenceItem:
    evidence_kind: str
    document_id: int | None
    photo_id: int | None
    evidence_id: str | None
    filename: str | None
    source: str | None
    data_mode: DataMode
    timestamp: str | None
    latitude: float | None
    longitude: float | None
    content_hash: str | None
    observed_quantity: float | None
    observed_quantity_unit: str | None
    observed_expenditure: float | None
    notes: str | None
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass
class FieldComparison:
    comparison_id: str
    pair: str
    field: str
    status: ConsistencyStatus
    left_value: Any
    right_value: Any
    explanation: str
    missing_information: list[str] = field(default_factory=list)


@dataclass
class VerificationResult:
    project_id: int
    internal_project_id: str
    overall_result: ConsistencyStatus
    data_mode: DataMode
    plan_findings: list[str]
    claim_findings: list[str]
    evidence_findings: list[str]
    mismatches: list[FieldComparison]
    missing_information: list[str]
    comparisons: list[FieldComparison]
    evidence_confidence: float
    explanation: str
    provenance: dict[str, Any]
    evidence_ids: list[str] = field(default_factory=list)
    note: str = ""
