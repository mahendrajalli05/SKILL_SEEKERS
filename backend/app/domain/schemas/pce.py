from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.enums import DataMode
from app.engines.pce.constants import GOVERNANCE_NOTE
from app.engines.pce.types import (
    AssembledClaim,
    AssembledEvidenceItem,
    AssembledPlan,
    FieldComparison,
    VerificationResult,
)


def _reject_fraud(value: object) -> object:
    if value is None:
        return value
    if isinstance(value, str) and "fraud" in value.casefold():
        raise ValueError(
            "Plan–Claim–Evidence must not claim fraud. Record a consistency finding instead."
        )
    return value


class PlanFieldRead(BaseModel):
    name: str
    value: Any = None
    available: bool
    data_mode: DataMode | str
    synthetic: bool = False
    source: str
    unavailable_reason: str | None = None


class PlanWrite(BaseModel):
    sanctioned_scope: str | None = None
    budget_estimate: float | None = None
    blueprint_document_id: int | None = None
    dimensions_value: float | None = None
    dimensions_unit: str | None = None
    milestone_label: str | None = None
    milestone_amount: float | None = None
    planned_start_date: str | None = None
    planned_completion_date: str | None = None
    source: str | None = "officer_recorded"
    data_mode: DataMode | str | None = None

    @field_validator("sanctioned_scope", "source", "milestone_label")
    @classmethod
    def no_fraud(cls, value: str | None) -> str | None:
        _reject_fraud(value)
        return value


class PlanRead(BaseModel):
    project_id: int
    internal_project_id: str
    data_mode: DataMode | str
    sanctioned_scope: str | None = None
    budget_estimate: float | None = None
    budget_from_extract: bool = False
    blueprint_document_id: int | None = None
    dimensions_value: float | None = None
    dimensions_unit: str | None = None
    milestone_label: str | None = None
    milestone_amount: float | None = None
    planned_start_date: str | None = None
    planned_completion_date: str | None = None
    source: str
    recorded: bool = False
    fields: list[PlanFieldRead] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    note: str = (
        "Plan fields that are not present in the public extract remain unavailable "
        "in REAL mode. SYNTHETIC enrichment is labelled when HYBRID mode is used."
    )

    @classmethod
    def from_assembled(cls, plan: AssembledPlan) -> "PlanRead":
        return cls(
            project_id=plan.project_id,
            internal_project_id=plan.internal_project_id,
            data_mode=plan.data_mode,
            sanctioned_scope=plan.sanctioned_scope,
            budget_estimate=plan.budget_estimate,
            budget_from_extract=plan.budget_from_extract,
            blueprint_document_id=plan.blueprint_document_id,
            dimensions_value=plan.dimensions_value,
            dimensions_unit=plan.dimensions_unit,
            milestone_label=plan.milestone_label,
            milestone_amount=plan.milestone_amount,
            planned_start_date=plan.planned_start_date,
            planned_completion_date=plan.planned_completion_date,
            source=plan.source,
            recorded=plan.recorded,
            fields=[PlanFieldRead.model_validate(item.__dict__) for item in plan.fields],
            provenance=plan.provenance,
        )


class ClaimWrite(BaseModel):
    claimed_progress: str | None = None
    claimed_progress_percent: float | None = Field(default=None, ge=0, le=100)
    claimed_expenditure: float | None = None
    claimed_completion_state: str | None = None
    claimed_quantity: float | None = None
    claimed_quantity_unit: str | None = None
    milestone_claimed: str | None = None
    claim_date: str | None = None
    claimant_source: str | None = None
    supporting_document_ids: list[int] = Field(default_factory=list)
    data_mode: DataMode | str | None = None

    @field_validator("claimed_progress", "claimed_completion_state", "claimant_source")
    @classmethod
    def no_fraud(cls, value: str | None) -> str | None:
        _reject_fraud(value)
        return value


class ClaimRead(BaseModel):
    project_id: int
    claim_id: int | None = None
    data_mode: DataMode | str
    claimed_progress: str | None = None
    claimed_progress_percent: float | None = None
    claimed_expenditure: float | None = None
    claimed_completion_state: str | None = None
    claimed_quantity: float | None = None
    claimed_quantity_unit: str | None = None
    milestone_claimed: str | None = None
    claim_date: str | None = None
    claimant_source: str | None = None
    supporting_document_ids: list[int] = Field(default_factory=list)
    recorded: bool = False
    provenance: dict[str, Any] = Field(default_factory=dict)
    note: str = "Claims are statements being evaluated, not automatically true facts."

    @classmethod
    def from_assembled(cls, claim: AssembledClaim) -> "ClaimRead":
        return cls(
            project_id=claim.project_id,
            claim_id=claim.claim_id,
            data_mode=claim.data_mode,
            claimed_progress=claim.claimed_progress,
            claimed_progress_percent=claim.claimed_progress_percent,
            claimed_expenditure=claim.claimed_expenditure,
            claimed_completion_state=claim.claimed_completion_state,
            claimed_quantity=claim.claimed_quantity,
            claimed_quantity_unit=claim.claimed_quantity_unit,
            milestone_claimed=claim.milestone_claimed,
            claim_date=claim.claim_date,
            claimant_source=claim.claimant_source,
            supporting_document_ids=claim.supporting_document_ids,
            recorded=claim.recorded,
            provenance=claim.provenance,
        )


class ClaimListResponse(BaseModel):
    project_id: int
    items: list[ClaimRead] = Field(default_factory=list)
    note: str = "Claims are statements being evaluated, not automatically true facts."


class EvidenceAttachmentWrite(BaseModel):
    document_type: str = "supporting_document"
    filename: str | None = None
    source: str | None = "officer_upload"
    data_mode: DataMode | str | None = None
    timestamp: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    hash: str | None = None
    observed_quantity: float | None = None
    observed_quantity_unit: str | None = None
    observed_expenditure: float | None = None
    notes: str | None = None

    @field_validator("filename", "source", "notes")
    @classmethod
    def no_fraud(cls, value: str | None) -> str | None:
        _reject_fraud(value)
        return value


class EvidenceAttachmentRead(BaseModel):
    evidence_kind: str
    document_id: int | None = None
    photo_id: int | None = None
    evidence_id: str | None = None
    filename: str | None = None
    source: str | None = None
    data_mode: DataMode | str
    timestamp: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    content_hash: str | None = None
    observed_quantity: float | None = None
    observed_quantity_unit: str | None = None
    observed_expenditure: float | None = None
    notes: str | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)
    note: str = (
        "Evidence attachment recording only. Image authenticity and satellite "
        "measurements are not assessed in V1."
    )

    @classmethod
    def from_assembled(cls, item: AssembledEvidenceItem) -> "EvidenceAttachmentRead":
        return cls(
            evidence_kind=item.evidence_kind,
            document_id=item.document_id,
            photo_id=item.photo_id,
            evidence_id=item.evidence_id,
            filename=item.filename,
            source=item.source,
            data_mode=item.data_mode,
            timestamp=item.timestamp,
            latitude=item.latitude,
            longitude=item.longitude,
            content_hash=item.content_hash,
            observed_quantity=item.observed_quantity,
            observed_quantity_unit=item.observed_quantity_unit,
            observed_expenditure=item.observed_expenditure,
            notes=item.notes,
            provenance=item.provenance,
        )


class ComparisonRead(BaseModel):
    comparison_id: str
    pair: str
    field: str
    status: str
    left_value: Any = None
    right_value: Any = None
    explanation: str
    missing_information: list[str] = Field(default_factory=list)


class VerificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    project_id: int
    internal_project_id: str
    overall_result: str
    data_mode: DataMode | str
    plan_findings: list[str] = Field(default_factory=list)
    claim_findings: list[str] = Field(default_factory=list)
    evidence_findings: list[str] = Field(default_factory=list)
    mismatches: list[ComparisonRead] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    comparisons: list[ComparisonRead] = Field(default_factory=list)
    evidence_confidence: float
    explanation: str
    provenance: dict[str, Any] = Field(default_factory=dict)
    evidence_ids: list[str] = Field(default_factory=list)
    note: str = GOVERNANCE_NOTE

    @classmethod
    def from_result(cls, result: VerificationResult) -> "VerificationRead":
        def as_read(item: FieldComparison) -> ComparisonRead:
            return ComparisonRead(
                comparison_id=item.comparison_id,
                pair=item.pair,
                field=item.field,
                status=item.status.value,
                left_value=item.left_value,
                right_value=item.right_value,
                explanation=item.explanation,
                missing_information=item.missing_information,
            )

        return cls(
            project_id=result.project_id,
            internal_project_id=result.internal_project_id,
            overall_result=result.overall_result.value,
            data_mode=result.data_mode,
            plan_findings=result.plan_findings,
            claim_findings=result.claim_findings,
            evidence_findings=result.evidence_findings,
            mismatches=[as_read(item) for item in result.mismatches],
            missing_information=result.missing_information,
            comparisons=[as_read(item) for item in result.comparisons],
            evidence_confidence=result.evidence_confidence,
            explanation=result.explanation,
            provenance=result.provenance,
            evidence_ids=result.evidence_ids,
            note=result.note or GOVERNANCE_NOTE,
        )
