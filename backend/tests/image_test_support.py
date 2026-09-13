from __future__ import annotations

from datetime import date

from app.db import get_session_factory
from app.models.project import Project

SYNTHETIC_LABEL = "SYNTHETIC: image evidence unit test (not a government project)"


def insert_project(session, **overrides: object) -> Project:
    values: dict[str, object] = {
        "internal_project_id": "internal:synthetic:image:subject",
        "internal_id_kind": "internal_surrogate_hash",
        "internal_id_scheme": "sarvsakshi_internal_work_v1",
        "source_dataset": "github_vonter_india-mplads-works_MPLADS.csv",
        "is_synthetic": False,
        "lifecycle_stage": "ONGOING",
        "state": "Andhra Pradesh",
        "constituency": "KURNOOL",
        "category": "Normal/Others",
        "work_description": "NA - Construction of community hall",
        "allocation_amount": 2_000_000,
        "recommended_date": date(2023, 6, 1),
        "status": "Ongoing",
    }
    values.update(overrides)
    row = Project(**values)
    session.add(row)
    session.flush()
    return row


def project_id(client, **overrides: object) -> int:
    session = get_session_factory()()
    try:
        row = insert_project(session, **overrides)
        session.commit()
        return row.id
    finally:
        session.close()
