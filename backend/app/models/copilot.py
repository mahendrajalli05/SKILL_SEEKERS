from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class CopilotTurn(Base, TimestampMixin):
    """Project-scoped Investigation Copilot turn. Not unrestricted personal memory."""

    __tablename__ = "copilot_turn"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), nullable=False)
    session_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    question: Mapped[str | None] = mapped_column(Text, nullable=True)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    mode: Mapped[str] = mapped_column(String(32), nullable=False, default="template")
    data_mode: Mapped[str | None] = mapped_column(String(32), nullable=True)
    intent: Mapped[str | None] = mapped_column(String(64), nullable=True)
    evidence_ids_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(String(64), nullable=True)
    evidence_set_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)

    project = relationship("Project", back_populates="copilot_turns")
