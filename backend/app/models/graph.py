from sqlalchemy import Float, ForeignKey, Integer, String

from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class GraphEdge(Base, TimestampMixin):
    """Project-to-project SIMILAR_TO edges from Relationship Graph V1.

    Entity links (MP, constituency, category, IDA, state) are derived
    from observed ``project`` columns and are not stored here.
    """

    __tablename__ = "graph_edge"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    from_project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), nullable=False)
    to_project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), nullable=False)
    edge_type: Mapped[str] = mapped_column(String(64), nullable=False)
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)
