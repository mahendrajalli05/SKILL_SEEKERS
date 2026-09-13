"""SARVSAKSHI lifecycle workflow persistence.

Planning states are application workflow only, not official MPLADS status.
Does not overwrite project.lifecycle_stage or intelligence scores.
"""

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class LifecycleWorkflow(Base, TimestampMixin):
    """Latest SARVSAKSHI planning/admin state per project.

    ``lifecycle_state`` here is a copy of source-derived FUTURE/ONGOING/COMPLETED/UNKNOWN
    at last write. It is not an official MPLADS status and does not replace
    ``project.lifecycle_stage``.
    """

    __tablename__ = "lifecycle_workflow"
    __table_args__ = (UniqueConstraint("project_id", name="uq_lifecycle_workflow_project"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), nullable=False)
    planning_state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_action: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    data_mode: Mapped[str | None] = mapped_column(String(32), nullable=True)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    project = relationship("Project", back_populates="lifecycle_workflow")


class LifecycleDecision(Base, TimestampMixin):
    """Append-only planning/admin decisions. Does not change scores."""

    __tablename__ = "lifecycle_decision"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    resulting_state: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    data_mode: Mapped[str | None] = mapped_column(String(32), nullable=True)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    project = relationship("Project", back_populates="lifecycle_decisions")
