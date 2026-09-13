"""Map SQLite projects and HYBRID schedules into TimePeerRecord rows."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.engines.cost.work_type import derive_work_type
from app.engines.time.constants import DEFAULT_HYBRID_AS_OF_DATE, REAL_OBSERVATION_DATE
from app.engines.time.enrichment import HybridSchedule
from app.engines.time.types import TimeMode, TimePeerRecord
from app.models.project import Project
from app.models.snapshot import DatasetSnapshot


def observation_date_from_session(session: Session) -> date:
    snap = session.scalars(select(DatasetSnapshot).order_by(DatasetSnapshot.id.asc())).first()
    if snap is not None:
        text = (snap.download_date or "").strip()
        parsed = None
        if text:
            from app.engines.time.dates import parse_iso_date

            parsed = parse_iso_date(text)
        if parsed is not None:
            return parsed
        if snap.extracted_at is not None:
            return snap.extracted_at.date()
    return REAL_OBSERVATION_DATE


def project_to_time_record(
    row: Project,
    *,
    time_mode: TimeMode,
    schedule: HybridSchedule | None = None,
    observation_date: date | None = None,
) -> TimePeerRecord:
    obs = observation_date or REAL_OBSERVATION_DATE
    if time_mode == TimeMode.HYBRID_TEST:
        return TimePeerRecord(
            project_id=row.id,
            internal_project_id=row.internal_project_id,
            constituency=(row.constituency or "").strip(),
            category=(row.category or "").strip(),
            state=(row.state or "").strip(),
            work_description=(row.work_description or "").strip(),
            derived_work_type=derive_work_type(row.work_description),
            status=(row.status or "").strip(),
            lifecycle_stage=(row.lifecycle_stage or "").strip(),
            recommended_date=row.recommended_date,
            time_mode=TimeMode.HYBRID_TEST,
            planned_start_date=schedule.planned_start_date if schedule else None,
            planned_completion_date=schedule.planned_completion_date if schedule else None,
            actual_start_date=schedule.actual_start_date if schedule else None,
            actual_completion_date=schedule.actual_completion_date if schedule else None,
            physical_progress_percent=(
                schedule.physical_progress_percent if schedule else None
            ),
            as_of_date=(
                schedule.as_of_date if schedule else DEFAULT_HYBRID_AS_OF_DATE
            ),
            observation_date=obs,
        )
    return TimePeerRecord(
        project_id=row.id,
        internal_project_id=row.internal_project_id,
        constituency=(row.constituency or "").strip(),
        category=(row.category or "").strip(),
        state=(row.state or "").strip(),
        work_description=(row.work_description or "").strip(),
        derived_work_type=derive_work_type(row.work_description),
        status=(row.status or "").strip(),
        lifecycle_stage=(row.lifecycle_stage or "").strip(),
        recommended_date=row.recommended_date,
        time_mode=TimeMode.REAL,
        observation_date=obs,
    )


class SqlTimePeerSource:
    """Constituency/state candidates from ``project``, optionally joined to HYBRID schedules."""

    def __init__(
        self,
        session: Session,
        *,
        time_mode: TimeMode,
        schedules: dict[str, HybridSchedule] | None = None,
        observation_date: date | None = None,
    ) -> None:
        self._session = session
        self._time_mode = time_mode
        self._schedules = schedules or {}
        self._observation_date = observation_date or observation_date_from_session(session)

    def _to_record(self, row: Project) -> TimePeerRecord | None:
        if self._time_mode == TimeMode.HYBRID_TEST:
            schedule = self._schedules.get(row.internal_project_id)
            if schedule is None:
                return None
            return project_to_time_record(
                row,
                time_mode=TimeMode.HYBRID_TEST,
                schedule=schedule,
                observation_date=self._observation_date,
            )
        return project_to_time_record(
            row,
            time_mode=TimeMode.REAL,
            observation_date=self._observation_date,
        )

    def _map(self, rows: Sequence[Project]) -> list[TimePeerRecord]:
        mapped: list[TimePeerRecord] = []
        for row in rows:
            record = self._to_record(row)
            if record is not None:
                mapped.append(record)
        return mapped

    def by_constituency(
        self,
        constituency: str,
        state: str | None = None,
    ) -> Sequence[TimePeerRecord]:
        key = (constituency or "").strip()
        if not key:
            return []
        stmt = select(Project).where(Project.constituency == key)
        state_key = (state or "").strip()
        if state_key:
            stmt = stmt.where(Project.state == state_key)
        rows = self._session.scalars(stmt).all()
        if self._time_mode == TimeMode.HYBRID_TEST:
            rows = [row for row in rows if row.internal_project_id in self._schedules]
        return self._map(rows)

    def by_state(self, state: str) -> Sequence[TimePeerRecord]:
        key = (state or "").strip()
        if not key:
            return []
        stmt = select(Project).where(Project.state == key)
        rows = self._session.scalars(stmt).all()
        if self._time_mode == TimeMode.HYBRID_TEST:
            rows = [row for row in rows if row.internal_project_id in self._schedules]
        return self._map(rows)
