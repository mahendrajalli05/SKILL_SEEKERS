"""Controlled project rows for Demo Cases tests. Evidence is attached through
the production Demo Evidence Fixtures V1 loader. Not a new government dataset.
"""

from __future__ import annotations

from datetime import date

from app.demo.constants import internal_project_id_for
from app.demo.evidence_fixtures import ensure_demo_case_evidence
from app.domain.enums import LifecycleStage
from app.models.project import Project

CASE_META = {
    "GHOST": {
        "lifecycle_stage": LifecycleStage.COMPLETED.value,
        "status": "Completed",
        "constituency": "VIZIANAGARAM",
        "category": "Other works",
        "work_description": "NA - Supply of artificial limbs / assistive devices",
        "allocation_amount": 500_000,
        "ida": "Vizianagaram",
    },
    "OVERBILL": {
        "lifecycle_stage": LifecycleStage.COMPLETED.value,
        "status": "Completed",
        "constituency": "ELURU",
        "category": "Repair and Renovation",
        "work_description": "NA - Repair and renovation of community building",
        "allocation_amount": 800_000,
        "ida": "Eluru",
    },
    "STUCK": {
        "lifecycle_stage": LifecycleStage.ONGOING.value,
        "status": "Ongoing",
        "constituency": "ANANTAPUR",
        "category": "Normal/Others",
        "work_description": "NA - Construction of additional classrooms",
        "allocation_amount": 1_200_000,
        "ida": "Anantapur",
    },
    "CLEAN": {
        "lifecycle_stage": LifecycleStage.FUTURE.value,
        "status": "Sanctioned",
        "constituency": "KADAPA",
        "category": "Normal/Others",
        "work_description": "NA - Construction of culverts",
        "allocation_amount": 400_000,
        "ida": "Kadapa",
    },
}


def insert_demo_project(session, case_id: str, **overrides: object) -> Project:
    meta = CASE_META[case_id]
    values: dict[str, object] = {
        "internal_project_id": internal_project_id_for(case_id),
        "internal_id_kind": "internal_surrogate_hash",
        "internal_id_scheme": "sarvsakshi_internal_work_v1",
        "source_dataset": "github_vonter_india-mplads-works_MPLADS.csv",
        "is_synthetic": False,
        "synthetic_label": None,
        "state": "Andhra Pradesh",
        "mp_name": "Example MP",
        "recommended_date": date(2023, 6, 1),
        "house": "Lok Sabha",
        **meta,
    }
    values.update(overrides)
    row = Project(**values)
    session.add(row)
    session.flush()
    return row


def insert_seeded_demo_case(session, case_id: str) -> Project:
    project = insert_demo_project(session, case_id)
    ensure_demo_case_evidence(session, project, case_id)
    session.flush()
    return project


def insert_all_demo_cases(session) -> dict[str, Project]:
    return {case_id: insert_seeded_demo_case(session, case_id) for case_id in CASE_META}
