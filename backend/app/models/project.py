from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Project(Base, TimestampMixin):
    """Master work record. Every dump-derived column is nullable until profiling."""

    __tablename__ = "project"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    unique_work_number: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    work_name: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    work_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    work_category: Mapped[str | None] = mapped_column(String(256), nullable=True)
    state: Mapped[str | None] = mapped_column(String(128), nullable=True)
    implementing_district: Mapped[str | None] = mapped_column(String(128), nullable=True)
    constituency: Mapped[str | None] = mapped_column(String(256), nullable=True)
    house_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mp_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    agency_id: Mapped[int | None] = mapped_column(ForeignKey("implementing_agency.id"), nullable=True)
    agency_name_raw: Mapped[str | None] = mapped_column(String(512), nullable=True)
    village_or_place: Mapped[str | None] = mapped_column(String(256), nullable=True)

    amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    amount_role: Mapped[str | None] = mapped_column(String(32), nullable=True)
    amount_unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    recommended_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    sanctioned_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    utilised_amount: Mapped[float | None] = mapped_column(Float, nullable=True)

    recommendation_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    sanction_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_of_completion: Mapped[date | None] = mapped_column(Date, nullable=True)

    work_status: Mapped[str | None] = mapped_column(String(128), nullable=True)
    lifecycle_stage: Mapped[str] = mapped_column(String(32), nullable=False, default="UNKNOWN")
    image_uploaded: Mapped[str | None] = mapped_column(String(32), nullable=True)
    image_status: Mapped[str | None] = mapped_column(String(64), nullable=True)

    snapshot_id: Mapped[int | None] = mapped_column(ForeignKey("dataset_snapshot.id"), nullable=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    synthetic_label: Mapped[str | None] = mapped_column(String(256), nullable=True)

    snapshot = relationship("DatasetSnapshot", back_populates="projects")
    agency = relationship("ImplementingAgency", back_populates="projects")
    documents = relationship("Document", back_populates="project")
    photos = relationship("Photo", back_populates="project")
    claims = relationship("Claim", back_populates="project")
    evidence_objects = relationship("EvidenceObjectRow", back_populates="project")
    fusion_score = relationship("FusionScore", back_populates="project", uselist=False)
    decisions = relationship("OfficerDecision", back_populates="project")
    copilot_turns = relationship("CopilotTurn", back_populates="project")
    citizen_reports = relationship("CitizenReport", back_populates="project")
