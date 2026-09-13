from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ImplementingAgency(Base, TimestampMixin):
    __tablename__ = "implementing_agency"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    raw_name: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)

    projects = relationship("Project", back_populates="agency")
