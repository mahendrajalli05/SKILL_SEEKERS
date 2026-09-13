from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class OfficerDecision(Base, TimestampMixin):
    __tablename__ = "officer_decision"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), nullable=False)
    decision_type: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor_role: Mapped[str | None] = mapped_column(String(64), nullable=True)

    project = relationship("Project", back_populates="decisions")
