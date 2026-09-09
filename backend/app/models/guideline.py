from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class GuidelineRule(Base, TimestampMixin):
    """Deterministic compliance rules. Never an ML model."""

    __tablename__ = "guideline_rule"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    guideline_ref: Mapped[str | None] = mapped_column(String(256), nullable=True)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    condition_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    snippets = relationship("GuidelineSnippet", back_populates="rule")


class GuidelineSnippet(Base, TimestampMixin):
    __tablename__ = "guideline_snippet"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_id: Mapped[int | None] = mapped_column(ForeignKey("guideline_rule.id"), nullable=True)
    source_pdf: Mapped[str | None] = mapped_column(String(512), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    rule = relationship("GuidelineRule", back_populates="snippets")
