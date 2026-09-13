from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class FusionScore(Base, TimestampMixin):
    """Latest fused result. Never stores a legal fraud probability."""

    __tablename__ = "fusion_score"
    __table_args__ = (UniqueConstraint("project_id", name="uq_fusion_score_project"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), nullable=False)
    investigation_priority: Mapped[int | None] = mapped_column(Integer, nullable=True)
    evidence_confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    config_version: Mapped[str] = mapped_column(String(64), nullable=False)
    why_flagged: Mapped[str | None] = mapped_column(Text, nullable=True)
    why_not_flagged: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_mode: Mapped[str | None] = mapped_column(String(32), nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(String(32), nullable=True)
    explanation_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    project = relationship("Project", back_populates="fusion_score")
