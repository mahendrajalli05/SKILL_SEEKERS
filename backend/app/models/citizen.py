from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class CitizenReport(Base, TimestampMixin):
    """P1 Jan-Sakshi storage. No citizen routes or UI in this slice."""

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

    project = relationship("Project", back_populates="citizen_reports")
