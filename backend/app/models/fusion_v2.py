from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class FusionScoreV2(Base, TimestampMixin):
    """Latest Risk Fusion V2 result per project and data mode.

    Never stores a legal fraud probability. Does not replace fusion_score (V1.1).
    """

    __tablename__ = "fusion_score_v2"
    __table_args__ = (
        UniqueConstraint("project_id", "data_mode", name="uq_fusion_score_v2_project_mode"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), nullable=False)
    data_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    investigation_priority: Mapped[int | None] = mapped_column(Integer, nullable=True)
    evidence_confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_class: Mapped[str | None] = mapped_column(String(32), nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(String(64), nullable=True)
    explanation_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    config_version: Mapped[str] = mapped_column(String(64), nullable=False)
    engine_version: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    project = relationship("Project", back_populates="fusion_scores_v2")


class FusionScoreV2History(Base):
    """Append-only V2 snapshots. Prior rows are never mutated."""

    __tablename__ = "fusion_score_v2_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), nullable=False)
    data_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    investigation_priority: Mapped[int | None] = mapped_column(Integer, nullable=True)
    evidence_confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_class: Mapped[str | None] = mapped_column(String(32), nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(String(64), nullable=True)
    explanation_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    config_version: Mapped[str] = mapped_column(String(64), nullable=False)
    engine_version: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    project = relationship("Project", back_populates="fusion_score_v2_history")
