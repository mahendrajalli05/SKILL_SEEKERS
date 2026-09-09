from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class EvidenceObjectRow(Base, TimestampMixin):
    __tablename__ = "evidence_object"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), nullable=False)
    engine: Mapped[str] = mapped_column(String(32), nullable=False)
    engine_version: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="inconclusive")
    severity: Mapped[str] = mapped_column(String(32), nullable=False, default="info")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    comparables_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    rule_ids_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    guideline_refs_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    project = relationship("Project", back_populates="evidence_objects")
    facts = relationship("EvidenceFactRow", back_populates="evidence")


class EvidenceFactRow(Base, TimestampMixin):
    __tablename__ = "evidence_fact"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    evidence_id: Mapped[int] = mapped_column(ForeignKey("evidence_object.id"), nullable=False)
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(256), nullable=False)

    evidence = relationship("EvidenceObjectRow", back_populates="facts")


class OverlapLink(Base, TimestampMixin):
    __tablename__ = "overlap_link"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    from_project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), nullable=False)
    to_project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    reasons: Mapped[str | None] = mapped_column(Text, nullable=True)
