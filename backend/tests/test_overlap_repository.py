from __future__ import annotations

import uuid
from datetime import date, timedelta

from app.db import get_session_factory
from app.engines.overlap.constants import DATE_CANDIDATE_WINDOW_DAYS
from app.engines.overlap.repository import clear_overlap_record_cache, load_overlap_records
from app.engines.overlap.service import assess_project_overlap
from app.engines.overlap.types import OverlapAssessmentOutcome, OverlapMode
from app.models.project import Project


def _insert_project(session, **overrides: object) -> Project:
    uid = uuid.uuid4().hex[:12]
    values: dict[str, object] = {
        "internal_project_id": f"internal:synthetic:overlap:repo:{uid}",
        "internal_id_kind": "internal_surrogate_hash",
        "internal_id_scheme": "sarvsakshi_internal_work_v1",
        "source_dataset": "github_vonter_india-mplads-works_MPLADS.csv",
        "is_synthetic": True,
        "synthetic_label": "SYNTHETIC: overlap repository test",
        "lifecycle_stage": "FUTURE",
        "state": "Andhra Pradesh",
        "constituency": "KURNOOL",
        "category": "Normal/Others",
        "work_description": "NA - Construction of water tanks",
        "mp_name": "Test MP",
        "allocation_amount": 500_000,
        "recommended_date": date(2023, 6, 1),
        "status": "Unsanctioned",
        "ida": "Kurnool_IDA",
        "house": "Lok Sabha",
    }
    values.update(overrides)
    row = Project(**values)
    session.add(row)
    session.flush()
    return row


def test_load_overlap_records_filters_by_constituency() -> None:
    clear_overlap_record_cache()
    session = get_session_factory()()
    created_ids: list[int] = []
    try:
        p1 = _insert_project(
            session,
            constituency="KURNOOL",
        )
        p2 = _insert_project(
            session,
            constituency="GUNTUR",
        )
        session.commit()
        created_ids.extend([p1.id, p2.id])

        records_kurnool = load_overlap_records(
            session,
            mode=OverlapMode.REAL,
            subject_is_synthetic=True,
            constituency="KURNOOL",
        )
        ids = {r.project_id for r in records_kurnool}
        assert p1.id in ids
        assert p2.id not in ids
    finally:
        for pid in created_ids:
            row = session.get(Project, pid)
            if row:
                session.delete(row)
        session.commit()
        session.close()


def test_load_overlap_records_filters_by_date_window() -> None:
    clear_overlap_record_cache()
    session = get_session_factory()()
    created_ids: list[int] = []
    try:
        base_date = date(2023, 6, 1)
        p_near = _insert_project(
            session,
            constituency="TIRUPATI",
            recommended_date=base_date + timedelta(days=30),
        )
        p_far = _insert_project(
            session,
            constituency="TIRUPATI",
            recommended_date=base_date + timedelta(days=DATE_CANDIDATE_WINDOW_DAYS + 100),
        )
        session.commit()
        created_ids.extend([p_near.id, p_far.id])

        records = load_overlap_records(
            session,
            mode=OverlapMode.REAL,
            subject_is_synthetic=True,
            constituency="TIRUPATI",
            recommended_date=base_date,
        )
        ids = {r.project_id for r in records}
        assert p_near.id in ids
        assert p_far.id not in ids
    finally:
        for pid in created_ids:
            row = session.get(Project, pid)
            if row:
                session.delete(row)
        session.commit()
        session.close()


def test_assess_project_overlap_uses_scoped_corpus() -> None:
    clear_overlap_record_cache()
    session = get_session_factory()()
    created_ids: list[int] = []
    try:
        subject = _insert_project(
            session,
            constituency="VIJAYAWADA",
            work_description="Construction of CC road and drain",
            recommended_date=date(2023, 5, 10),
            allocation_amount=500_000,
        )
        match_peer = _insert_project(
            session,
            constituency="VIJAYAWADA",
            work_description="Construction of CC road and drain",
            recommended_date=date(2023, 5, 20),
            allocation_amount=500_000,
        )
        other_const_peer = _insert_project(
            session,
            constituency="VISAKHAPATNAM",
            work_description="Construction of CC road and drain",
            recommended_date=date(2023, 5, 20),
            allocation_amount=500_000,
        )
        session.commit()
        created_ids.extend([subject.id, match_peer.id, other_const_peer.id])

        result = assess_project_overlap(
            session,
            subject.id,
            mode=OverlapMode.REAL,
            persist=False,
        )
        assert result.project_id == subject.id
        assert result.outcome == OverlapAssessmentOutcome.POTENTIAL_DUPLICATE
        assert len(result.matches) >= 1
        linked_ids = {m.linked_project_id for m in result.matches}
        assert match_peer.id in linked_ids
        assert other_const_peer.id not in linked_ids
    finally:
        for pid in created_ids:
            row = session.get(Project, pid)
            if row:
                session.delete(row)
        session.commit()
        session.close()
