from __future__ import annotations

from datetime import date

from app.db import get_session_factory
from app.models.project import Project

SYNTHETIC_LABEL = "TEST DATA — SYNTHETIC citizen fixture. Not a genuine public report."


def insert_project(session, **overrides: object) -> Project:
    values: dict[str, object] = {
        "internal_project_id": "internal:synthetic:citizen:subject",
        "internal_id_kind": "internal_surrogate_hash",
        "internal_id_scheme": "sarvsakshi_internal_work_v1",
        "source_dataset": "github_vonter_india-mplads-works_MPLADS.csv",
        "is_synthetic": False,
        "lifecycle_stage": "ONGOING",
        "state": "Andhra Pradesh",
        "constituency": "VIZIANAGARAM",
        "category": "Roads",
        "work_description": "Construction of rural road",
        "allocation_amount": 1_500_000,
        "recommended_date": date(2023, 6, 1),
        "status": "Ongoing",
    }
    values.update(overrides)
    row = Project(**values)
    session.add(row)
    session.flush()
    return row


def project_row(internal_project_id: str, **overrides: object) -> tuple[int, str]:
    session = get_session_factory()()
    try:
        row = insert_project(session, internal_project_id=internal_project_id, **overrides)
        session.commit()
        return row.id, row.internal_project_id
    finally:
        session.close()


def patch_project_gps(monkeypatch, internal_project_id: str, lat: float, lon: float) -> None:
    monkeypatch.setattr(
        "app.engines.geo.location.load_hybrid_coordinates",
        lambda path=None: {internal_project_id: (lat, lon)},
    )
