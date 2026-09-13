from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.enums import OfficerDecisionType

ALLOWED_DECISION_TYPES = frozenset(item.value for item in OfficerDecisionType)


class OfficerDecisionCreate(BaseModel):
    decision_type: OfficerDecisionType
    reason: str | None = None
    actor_role: str = "officer"

    @field_validator("decision_type", mode="before")
    @classmethod
    def reject_legal_fraud_actions(cls, value: object) -> object:
        text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
        if "fraud" in text:
            raise ValueError(
                "Legal fraud conclusions are not officer actions in this prototype. "
                "Use confirm_concern, dismiss, or need_more_info."
            )
        return value

    @field_validator("reason")
    @classmethod
    def reason_must_not_claim_fraud(cls, value: str | None) -> str | None:
        if value and "fraud" in value.casefold():
            raise ValueError(
                "Officer notes must not record a legal fraud conclusion. "
                "Record an investigation concern instead."
            )
        return value


class OfficerDecisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    decision_type: str
    reason: str | None = None
    actor_role: str | None = None
    created_at: datetime | None = None
    investigation_priority_snapshot: int | None = None
    evidence_confidence_snapshot: int | None = None
    recommended_action_snapshot: str | None = None
    scores_unchanged: bool = True
    note: str = (
        "Human officer decision. Underlying intelligence scores were not changed."
    )


class OfficerDecisionListResponse(BaseModel):
    project_id: int
    items: list[OfficerDecisionRead] = Field(default_factory=list)
    allowed_actions: list[str] = Field(
        default_factory=lambda: sorted(ALLOWED_DECISION_TYPES)
    )
    disallowed_actions: list[str] = Field(
        default_factory=lambda: ["fraud_confirmed", "legal_fraud_finding"]
    )
    note: str = (
        "Officer actions are stored as human decisions. They do not change "
        "Investigation Priority or Evidence Confidence. This is not a legal "
        "fraud determination."
    )
