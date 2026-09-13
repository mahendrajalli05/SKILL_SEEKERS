from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class ExternalSource(Base, TimestampMixin):
    """Registry copy. Source facts remain documented in data/external/sources/registry.json."""

    __tablename__ = "external_source"
    __table_args__ = (UniqueConstraint("source_id", name="uq_external_source_source_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False)
    source_name: Mapped[str] = mapped_column(String(512), nullable=False)
    publisher: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(128), nullable=False)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    retrieval_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    dataset_version: Mapped[str | None] = mapped_column(String(256), nullable=True)
    geographic_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    update_frequency: Mapped[str | None] = mapped_column(String(128), nullable=True)
    license_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    transformation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    limitations_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    requires_credential: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class ExternalContextSnapshot(Base, TimestampMixin):
    """Cached retrieval of one external source snapshot."""

    __tablename__ = "external_context_snapshot"
    __table_args__ = (UniqueConstraint("source_id", name="uq_external_context_snapshot_source_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False)
    retrieval_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_version: Mapped[str | None] = mapped_column(String(256), nullable=True)
    file_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class ExternalContextObservation(Base, TimestampMixin):
    """One contextual indicator for a project. Separate from project rows."""

    __tablename__ = "external_context_observation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("project.id"), nullable=True)
    internal_project_id: Mapped[str] = mapped_column(String(128), nullable=False)
    indicator: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    geographic_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    geo_key: Mapped[str | None] = mapped_column(String(256), nullable=True)
    source_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    retrieval_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reference_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    data_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[str | None] = mapped_column(String(32), nullable=True)
    quality: Mapped[str | None] = mapped_column(String(64), nullable=True)
    context_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    provenance_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    assessment_kind: Mapped[str | None] = mapped_column(String(64), nullable=True)
