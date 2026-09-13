"""Shared fixtures for ML Training & Inference V1 tests."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.db import get_session_factory
from app.models.project import Project

TITLES = (
    "Construction of water tanks",
    "Construction of roads, approach roads, link roads and pathways",
    "Construction of community halls",
    "Street lights",
    "Construction of rooms and halls in school and colleges",
)


def insert_real_work(
    session: Session,
    *,
    suffix: str,
    amount: int,
    category: str = "Normal/Others",
    constituency: str = "KURNOOL",
    state: str = "Andhra Pradesh",
    work: str = TITLES[0],
    rec: date = date(2023, 6, 1),
    status: str = "Unsanctioned",
    house: str = "Lok Sabha",
) -> Project:
    row = Project(
        internal_project_id=f"internal:ml-test:{suffix}",
        internal_id_kind="internal_surrogate_hash",
        internal_id_scheme="sarvsakshi_internal_work_v1",
        is_synthetic=False,
        lifecycle_stage="FUTURE",
        state=state,
        constituency=constituency,
        category=category,
        work_description=work,
        allocation_amount=amount,
        recommended_date=rec,
        status=status,
        house=house,
    )
    session.add(row)
    session.flush()
    return row


def seed_real_training_rows(session: Session | None = None, *, n: int = 48) -> list[Project]:
    own = session is None
    session = session or get_session_factory()()
    rows: list[Project] = []
    try:
        for i in range(n):
            rows.append(
                insert_real_work(
                    session,
                    suffix=f"{i:03d}",
                    amount=200_000 + (i % 12) * 15_000,
                    work=TITLES[i % len(TITLES)],
                    rec=date(2022 + (i // 16), 1 + (i % 12), 1 + (i % 27)),
                    constituency="KURNOOL" if i % 3 else "GUNTUR",
                )
            )
        # Extreme allocation held in the latest temporal slice so IF can score it.
        rows.append(
            insert_real_work(
                session,
                suffix="extreme",
                amount=25_000_000,
                work=TITLES[0],
                rec=date(2024, 12, 15),
                constituency="KURNOOL",
            )
        )
        session.commit()
        return rows
    finally:
        if own:
            session.close()
