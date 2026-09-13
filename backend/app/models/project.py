from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Project(Base, TimestampMixin):
    """Master work record mapped from the cleaned MPLADS extract.

    ``internal_project_id`` is a SARVSAKSHI surrogate, not an official work ID.
    District, vendor, GPS, expenditure, sanction date, and completion date are
    absent from the source and are not stored here.
    """

    __tablename__ = "project"
    __table_args__ = (
        Index("ix_project_internal_project_id", "internal_project_id", unique=True),
        Index("ix_project_state", "state"),
        Index("ix_project_constituency", "constituency"),
        Index("ix_project_category", "category"),
        Index("ix_project_status", "status"),
        Index("ix_project_mp_name", "mp_name"),
        Index("ix_project_recommended_date", "recommended_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    internal_project_id: Mapped[str] = mapped_column(String(128), nullable=False)
    internal_id_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    internal_id_scheme: Mapped[str] = mapped_column(String(64), nullable=False)

    source_dataset: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source_first_row_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_duplicate_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    source_mp_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_work: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_category: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_state: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_constituency: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_ida: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_city: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_ward: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_block: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_village: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_recommended_date: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_allocation_amount: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_ida_approval: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_status: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_house: Mapped[str | None] = mapped_column(Text, nullable=True)

    mp_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    work_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(256), nullable=True)
    state: Mapped[str | None] = mapped_column(String(128), nullable=True)
    constituency: Mapped[str | None] = mapped_column(String(256), nullable=True)
    ida: Mapped[str | None] = mapped_column(String(512), nullable=True)
    city: Mapped[str | None] = mapped_column(String(512), nullable=True)
    ward: Mapped[str | None] = mapped_column(String(512), nullable=True)
    block: Mapped[str | None] = mapped_column(String(512), nullable=True)
    village: Mapped[str | None] = mapped_column(String(512), nullable=True)
    recommended_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    allocation_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ida_approval: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str | None] = mapped_column(String(128), nullable=True)
    house: Mapped[str | None] = mapped_column(String(64), nullable=True)
    lifecycle_stage: Mapped[str] = mapped_column(String(32), nullable=False, default="UNKNOWN")

    agency_id: Mapped[int | None] = mapped_column(ForeignKey("implementing_agency.id"), nullable=True)
    snapshot_id: Mapped[int | None] = mapped_column(ForeignKey("dataset_snapshot.id"), nullable=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    synthetic_label: Mapped[str | None] = mapped_column(String(256), nullable=True)

    snapshot = relationship("DatasetSnapshot", back_populates="projects")
    agency = relationship("ImplementingAgency", back_populates="projects")
    documents = relationship("Document", back_populates="project")
    photos = relationship("Photo", back_populates="project")
    claims = relationship("Claim", back_populates="project")
    plans = relationship("Plan", back_populates="project")
    milestones = relationship("Milestone", back_populates="project")
    evidence_objects = relationship("EvidenceObjectRow", back_populates="project")
    fusion_score = relationship("FusionScore", back_populates="project", uselist=False)
    fusion_scores_v2 = relationship("FusionScoreV2", back_populates="project")
    fusion_score_v2_history = relationship("FusionScoreV2History", back_populates="project")
    decisions = relationship("OfficerDecision", back_populates="project")
    copilot_turns = relationship("CopilotTurn", back_populates="project")
    citizen_reports = relationship("CitizenReport", back_populates="project")
    lifecycle_workflow = relationship(
        "LifecycleWorkflow", back_populates="project", uselist=False
    )
    lifecycle_decisions = relationship("LifecycleDecision", back_populates="project")
