"""SQL peer source and project-to-record mapping for Cost Intelligence V1."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.engines.cost.types import PeerRecord
from app.engines.cost.work_type import derive_work_type
from app.models.project import Project


def project_to_peer_record(row: Project) -> PeerRecord:
    amount = row.allocation_amount
    return PeerRecord(
        project_id=row.id,
        internal_project_id=row.internal_project_id,
        constituency=(row.constituency or "").strip(),
        category=(row.category or "").strip(),
        state=(row.state or "").strip(),
        work_description=(row.work_description or "").strip(),
        derived_work_type=derive_work_type(row.work_description),
        allocation_amount=int(amount) if amount is not None else None,
        recommended_date=row.recommended_date,
        is_synthetic=bool(row.is_synthetic),
    )


class SqlPeerSource:
    """Loads constituency or state candidates from the cleaned ``project`` table."""

    def __init__(self, session: Session, *, subject_is_synthetic: bool) -> None:
        self._session = session
        self._subject_is_synthetic = subject_is_synthetic

    def _base_query(self):
        stmt = select(Project).where(Project.allocation_amount > 0)
        # Equality, not IS, so SQLite integer 0/1 booleans match.
        stmt = stmt.where(Project.is_synthetic == self._subject_is_synthetic)
        return stmt

    def by_constituency(
        self,
        constituency: str,
        state: str | None = None,
    ) -> Sequence[PeerRecord]:
        key = (constituency or "").strip()
        if not key:
            return []
        stmt = self._base_query().where(Project.constituency == key)
        state_key = (state or "").strip()
        if state_key:
            stmt = stmt.where(Project.state == state_key)
        rows = self._session.scalars(stmt).all()
        return [project_to_peer_record(row) for row in rows]

    def by_state(self, state: str) -> Sequence[PeerRecord]:
        key = (state or "").strip()
        if not key:
            return []
        stmt = self._base_query().where(Project.state == key)
        rows = self._session.scalars(stmt).all()
        return [project_to_peer_record(row) for row in rows]
