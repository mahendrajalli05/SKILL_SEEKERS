from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Milestone(Base, TimestampMixin):
    """Milestone Advisor V1 row. Not an official MPLADS milestone record."""

    __tablename__ = "milestone"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "milestone_number",
            "data_mode",
            name="uq_milestone_project_number_mode",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), nullable=False)
    milestone_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    milestone_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    planned_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    cumulative_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completion_claimed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    claimed_progress: Mapped[float | None] = mapped_column(Float, nullable=True)
    claimed_expenditure: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PLANNED")
    data_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="REAL")
    provenance_json: Mapped[str] = mapped_column(Text, nullable=False)
    claim_id: Mapped[int | None] = mapped_column(ForeignKey("claim.id"), nullable=True)
    document_ids_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_ids_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_ids_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(String(32), nullable=True)
    assessment_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    officer_action: Mapped[str | None] = mapped_column(String(64), nullable=True)
    officer_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    officer_actor_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    officer_acted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project = relationship("Project", back_populates="milestones")
    decisions = relationship("MilestoneDecision", back_populates="milestone")


class MilestoneDecision(Base, TimestampMixin):
    """Officer milestone action. Does not release funds or mutate scores."""

    __tablename__ = "milestone_decision"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    milestone_id: Mapped[int] = mapped_column(ForeignKey("milestone.id"), nullable=False)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    data_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="REAL")
    investigation_priority_snapshot: Mapped[int | None] = mapped_column(Integer, nullable=True)
    evidence_confidence_snapshot: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recommended_action_snapshot: Mapped[str | None] = mapped_column(String(32), nullable=True)
    scores_unchanged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    provenance_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    milestone = relationship("Milestone", back_populates="decisions")
    project = relationship("Project")
