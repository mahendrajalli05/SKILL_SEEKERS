from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Plan(Base, TimestampMixin):
    """Officer-recorded or derived plan overlay for Plan–Claim–Evidence V1.

    Observed MPLADS extract fields remain on ``project``. Unavailable
    government values are not fabricated here.
    """

    __tablename__ = "plan"
    __table_args__ = (UniqueConstraint("project_id", name="uq_plan_project_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), nullable=False)
    sanctioned_scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    budget_estimate: Mapped[float | None] = mapped_column(Float, nullable=True)
    blueprint_document_id: Mapped[int | None] = mapped_column(
        ForeignKey("document.id"), nullable=True
    )
    dimensions_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    dimensions_unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    milestone_label: Mapped[str | None] = mapped_column(String(128), nullable=True)
    milestone_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    planned_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    planned_completion_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source: Mapped[str | None] = mapped_column(String(256), nullable=True)
    data_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="REAL")
    provenance_json: Mapped[str] = mapped_column(Text, nullable=False)

    project = relationship("Project", back_populates="plans")
    blueprint_document = relationship("Document")
