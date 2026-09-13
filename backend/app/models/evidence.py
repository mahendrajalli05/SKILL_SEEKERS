from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class EvidenceObjectRow(Base, TimestampMixin):
    """Persisted Evidence Object. Canonical V1 columns plus legacy engine fields.

    ``id`` is the SQLite primary key used by ``evidence_fact.evidence_id``.
    ``evidence_id`` is the deterministic public identifier.
    """

    __tablename__ = "evidence_object"
    __table_args__ = (
        UniqueConstraint("evidence_id", name="uq_evidence_object_evidence_id"),
        Index("ix_evidence_object_project_id", "project_id"),
        Index("ix_evidence_object_engine", "engine"),
        Index("ix_evidence_object_data_mode", "data_mode"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    evidence_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), nullable=False)
    engine: Mapped[str] = mapped_column(String(32), nullable=False)
    engine_name: Mapped[str | None] = mapped_column(String(32), nullable=True)
    engine_version: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(128), nullable=False)
    signal_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="inconclusive")
    disposition: Mapped[str | None] = mapped_column(String(32), nullable=True)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, default="info")
    finding: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_ids_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_mode: Mapped[str | None] = mapped_column(String(32), nullable=True)
    provenance_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    comparables_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    rule_ids_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    guideline_refs_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    project = relationship("Project", back_populates="evidence_objects")
    facts = relationship(
        "EvidenceFactRow",
        back_populates="evidence",
        cascade="all, delete-orphan",
    )


class EvidenceFactRow(Base, TimestampMixin):
    __tablename__ = "evidence_fact"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    evidence_id: Mapped[int] = mapped_column(ForeignKey("evidence_object.id"), nullable=False)
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(256), nullable=False)
    fact_kind: Mapped[str] = mapped_column(String(32), nullable=False, default="OBSERVATION")
    statement: Mapped[str | None] = mapped_column(Text, nullable=True)

    evidence = relationship("EvidenceObjectRow", back_populates="facts")


class OverlapLink(Base, TimestampMixin):
    __tablename__ = "overlap_link"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    from_project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), nullable=False)
    to_project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    reasons: Mapped[str | None] = mapped_column(Text, nullable=True)
