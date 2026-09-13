"""Controlled fixtures for Lifecycle Orchestration V1 tests."""

from __future__ import annotations

from datetime import date

from app.domain.enums import LifecycleStage
from app.models.project import Project

SYNTHETIC_LABEL = "SYNTHETIC: lifecycle-orchestration unit test (not a government project)"


def insert_project(session, **overrides: object) -> Project:
    values: dict[str, object] = {
        "internal_project_id": "internal:lifecycle:subject",
        "internal_id_kind": "internal_surrogate_hash",
        "internal_id_scheme": "sarvsakshi_internal_work_v1",
        "source_dataset": "github_vonter_india-mplads-works_MPLADS.csv",
        "is_synthetic": False,
        "lifecycle_stage": LifecycleStage.FUTURE.value,
        "state": "Andhra Pradesh",
        "constituency": "KURNOOL",
        "category": "Normal/Others",
        "work_description": "NA - Construction of community hall",
        "allocation_amount": 500_000,
        "recommended_date": date(2023, 6, 1),
        "status": "Unsanctioned",
        "mp_name": "Example MP",
        "ida": "District Collector_IDA",
    }
    values.update(overrides)
    row = Project(**values)
    session.add(row)
    session.flush()
    return row
