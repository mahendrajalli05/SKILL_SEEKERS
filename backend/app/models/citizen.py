from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class CitizenReport(Base, TimestampMixin):
    """Jan-Sakshi / Citizen Evidence V1 storage.

    No unnecessary personally identifying information is stored.
    """

    __tablename__ = "citizen_report"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    proximity_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    structured_option: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rating_existence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rating_matches_claim: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rating_public_use: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rating_official_photo: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    satisfaction_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    observation_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    issue_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    image_id: Mapped[int | None] = mapped_column(ForeignKey("photo.id"), nullable=True)
    submission_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    verification_result: Mapped[str | None] = mapped_column(String(32), nullable=True)
    timestamp_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    data_mode: Mapped[str | None] = mapped_column(String(32), nullable=True)
    provenance_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    duplicate_flag: Mapped[str | None] = mapped_column(String(64), nullable=True)
    watermark_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    evidence_ids_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    capture_timestamp: Mapped[str | None] = mapped_column(String(64), nullable=True)

    project = relationship("Project", back_populates="citizen_reports")
