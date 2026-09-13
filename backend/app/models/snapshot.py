from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class DatasetSnapshot(Base, TimestampMixin):
    """Provenance for one ingested extract. No government values are invented here."""

    __tablename__ = "dataset_snapshot"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    extracted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    download_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    publisher: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    original_filename: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source_filename: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    internal_id_scheme: Mapped[str | None] = mapped_column(String(64), nullable=True)
    cleaned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    record_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    projects = relationship("Project", back_populates="snapshot")
