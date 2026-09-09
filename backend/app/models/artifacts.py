from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Document(Base, TimestampMixin):
    __tablename__ = "document"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), nullable=False)
    kind: Mapped[str | None] = mapped_column(String(64), nullable=True)
    path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    uploaded_by_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    project = relationship("Project", back_populates="documents")
    plan_artifacts = relationship("PlanArtifact", back_populates="document")


class Photo(Base, TimestampMixin):
    __tablename__ = "photo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), nullable=False)
    path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    exif_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    exif_lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    exif_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    phash: Mapped[str | None] = mapped_column(String(128), nullable=True)

    project = relationship("Project", back_populates="photos")
    details = relationship("PhotoDetails", back_populates="photo", uselist=False)


class PhotoDetails(Base, TimestampMixin):
    __tablename__ = "photo_details"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    photo_id: Mapped[int] = mapped_column(ForeignKey("photo.id"), nullable=False)
    stage: Mapped[str | None] = mapped_column(String(64), nullable=True)
    work_type_seen: Mapped[str | None] = mapped_column(String(256), nullable=True)
    length_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    width_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    floors: Mapped[int | None] = mapped_column(Integer, nullable=True)
    roof: Mapped[str | None] = mapped_column(String(64), nullable=True)
    approx_area: Mapped[float | None] = mapped_column(Float, nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    photo = relationship("Photo", back_populates="details")


class Claim(Base, TimestampMixin):
    __tablename__ = "claim"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), nullable=False)
    milestone_label: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reported_progress: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount_used: Mapped[float | None] = mapped_column(Float, nullable=True)
    completion_statement: Mapped[str | None] = mapped_column(Text, nullable=True)

    project = relationship("Project", back_populates="claims")


class PlanArtifact(Base, TimestampMixin):
    __tablename__ = "plan_artifact"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("document.id"), nullable=False)
    claimed_area: Mapped[float | None] = mapped_column(Float, nullable=True)
    structure_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    extracted_fields_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    document = relationship("Document", back_populates="plan_artifacts")
