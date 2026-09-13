from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_session_factory
from app.engines.cost.work_type import derive_work_type
from app.engines.time.constants import (
    CAUSE_NOT_ESTABLISHED,
    ENGINE_VERSION,
    FORBIDDEN_MODEL_INPUT_COLUMNS,
    HYBRID_TEST_NOTE,
    SCOPE_CONSTITUENCY_CATEGORY_WORK_TYPE,
)
from app.engines.time.enrichment import HybridSchedule
from app.engines.time.peers import InMemoryTimePeerSource
from app.engines.time.service import assess_project_time, assess_time
from app.engines.time.types import TimeAssessmentOutcome, TimeMode, TimePeerRecord
from app.models.evidence import EvidenceObjectRow
from app.models.fusion import FusionScore
from app.models.project import Project

TANKS = "NA - Construction of water tanks"
ROADS = "NA - Construction of roads, approach roads, link roads and pathways"
AS_OF = date(2024, 6, 30)
SYNTHETIC_LABEL = "SYNTHETIC: time-intelligence unit test (not a government project)"


def _hybrid(
    project_id: int,
    *,
    constituency: str = "KURNOOL",
    category: str = "Normal/Others",
    work_description: str = TANKS,
    status: str = "Completed",
    planned_start: date = date(2024, 1, 1),
    planned_end: date = date(2024, 4, 10),
    actual_start: date | None = date(2024, 1, 1),
    actual_end: date | None = date(2024, 4, 10),
    progress: int | None = 100,
    as_of: date = AS_OF,
) -> TimePeerRecord:
    return TimePeerRecord(
        project_id=project_id,
        internal_project_id=f"internal:time:{project_id}",
        constituency=constituency,
        category=category,
        state="Andhra Pradesh",
        work_description=work_description,
        derived_work_type=derive_work_type(work_description),
        status=status,
        lifecycle_stage="COMPLETED" if actual_end else "ONGOING",
        recommended_date=date(2023, 6, 1),
        time_mode=TimeMode.HYBRID_TEST,
        planned_start_date=planned_start,
        planned_completion_date=planned_end,
        actual_start_date=actual_start,
        actual_completion_date=actual_end,
        physical_progress_percent=progress,
        as_of_date=as_of,
        observation_date=date(2026, 9, 9),
    )


def test_normal_completed_schedule_is_not_flagged() -> None:
    subject = _hybrid(1, actual_end=date(2024, 4, 10))
    peers = [_hybrid(10 + i, actual_end=date(2024, 4, 8 + (i % 3))) for i in range(8)]
    result = assess_time(subject, InMemoryTimePeerSource([subject, *peers]))
    assert result.outcome == TimeAssessmentOutcome.WITHIN_SCHEDULE
    assert result.flagged is False
    assert result.time_anomaly_score == 0
    assert result.planned_duration_days == 100
    assert result.actual_duration_days == 100
    assert result.why_not_flagged is not None
    assert "Not flagged as a Time Anomaly" in result.explanation
    assert HYBRID_TEST_NOTE in result.explanation
    assert result.dataset_type == "HYBRID"
    assert result.time_mode == TimeMode.HYBRID_TEST
    assert result.peer_scope == SCOPE_CONSTITUENCY_CATEGORY_WORK_TYPE
    assert "fraud" not in result.explanation.casefold()


def test_completed_delay_is_flagged() -> None:
    subject = _hybrid(1, actual_end=date(2024, 7, 19))
    peers = [_hybrid(10 + i, actual_end=date(2024, 4, 10)) for i in range(8)]
    result = assess_time(subject, InMemoryTimePeerSource([subject, *peers]))
    assert result.outcome == TimeAssessmentOutcome.TIME_ANOMALY
    assert result.flagged is True
    assert result.time_anomaly_score is not None
    assert result.time_anomaly_score >= 60
    assert result.slippage_days is not None
    assert result.slippage_days > 0
    assert result.why_flagged is not None
    assert CAUSE_NOT_ESTABLISHED in result.why_flagged
    assert result.cause_established is False
    assert result.signal_kind == "schedule_slippage"


def test_severe_delay_scores_higher_than_moderate() -> None:
    peers = [_hybrid(10 + i, actual_end=date(2024, 4, 10)) for i in range(8)]
    moderate = assess_time(
        _hybrid(1, actual_end=date(2024, 5, 10)),
        InMemoryTimePeerSource([_hybrid(1, actual_end=date(2024, 5, 10)), *peers]),
    )
    severe = assess_time(
        _hybrid(1, actual_end=date(2024, 10, 7)),
        InMemoryTimePeerSource([_hybrid(1, actual_end=date(2024, 10, 7)), *peers]),
    )
    assert moderate.time_anomaly_score is not None
    assert severe.time_anomaly_score is not None
    assert severe.time_anomaly_score >= moderate.time_anomaly_score
    assert severe.time_anomaly_score >= 60


def test_ongoing_progress_mismatch_is_flagged() -> None:
    start = AS_OF - timedelta(days=70)
    subject = _hybrid(
        1,
        status="Ongoing",
        planned_start=start,
        planned_end=start + timedelta(days=100),
        actual_start=start,
        actual_end=None,
        progress=20,
    )
    peers = [
        _hybrid(
            10 + i,
            status="Ongoing",
            planned_start=start,
            planned_end=start + timedelta(days=100),
            actual_start=start,
            actual_end=None,
            progress=65,
        )
        for i in range(8)
    ]
    result = assess_time(subject, InMemoryTimePeerSource([subject, *peers]))
    assert result.time_consumed_percent == 70.0
    assert result.physical_progress_percent == 20
    assert result.flagged is True
    assert result.time_anomaly_score is not None
    assert result.time_anomaly_score >= 60
    assert result.signal_kind == "schedule_progress_mismatch"
    assert CAUSE_NOT_ESTABLISHED in result.explanation
    assert "actual MPLADS execution history" in result.explanation


def test_negative_duration_is_invalid() -> None:
    subject = _hybrid(
        1,
        planned_start=date(2024, 4, 10),
        planned_end=date(2024, 1, 1),
        actual_start=date(2024, 1, 1),
        actual_end=date(2024, 4, 10),
    )
    result = assess_time(subject, InMemoryTimePeerSource([subject]))
    assert result.outcome == TimeAssessmentOutcome.INVALID_DATES
    assert result.time_anomaly_score is None
    assert result.evidence_confidence == 0
    assert result.flagged is False
    assert "negative" in result.explanation or "inconsistent" in result.explanation


def test_completion_before_start_is_invalid() -> None:
    subject = _hybrid(
        1,
        planned_start=date(2024, 1, 1),
        planned_end=date(2024, 4, 10),
        actual_start=date(2024, 4, 10),
        actual_end=date(2024, 1, 1),
    )
    result = assess_time(subject, InMemoryTimePeerSource([subject]))
    assert result.outcome == TimeAssessmentOutcome.INVALID_DATES
    assert result.time_anomaly_score is None
    assert "completion_before_start" in result.date_issues


def test_hybrid_without_schedule_is_insufficient() -> None:
    subject = _hybrid(
        1,
        planned_start=None,  # type: ignore[arg-type]
        planned_end=None,  # type: ignore[arg-type]
        actual_start=None,
        actual_end=None,
        progress=0,
    )
    # override Nones explicitly
    subject = TimePeerRecord(
        project_id=1,
        internal_project_id="internal:time:empty",
        constituency="KURNOOL",
        category="Normal/Others",
        state="Andhra Pradesh",
        work_description=TANKS,
        derived_work_type=derive_work_type(TANKS),
        status="Unsanctioned",
        lifecycle_stage="FUTURE",
        recommended_date=date(2023, 6, 1),
        time_mode=TimeMode.HYBRID_TEST,
        as_of_date=AS_OF,
        observation_date=date(2026, 9, 9),
    )
    result = assess_time(subject, InMemoryTimePeerSource([subject]))
    assert result.outcome == TimeAssessmentOutcome.INSUFFICIENT_EVIDENCE
    assert result.time_anomaly_score is None
    assert HYBRID_TEST_NOTE in result.explanation


def test_hybrid_scores_without_peers_from_own_plan() -> None:
    subject = _hybrid(1, actual_end=date(2024, 7, 19), constituency="UNIQUE-PC", work_description="NA - Unique xyz")
    result = assess_time(subject, InMemoryTimePeerSource([subject]))
    assert result.peer_scope is None
    assert result.peer_count == 0
    assert result.time_anomaly_score is not None
    assert result.time_anomaly_score >= 60
    assert result.evidence_confidence > 0
    assert result.evidence_confidence < 72


def test_output_is_deterministic() -> None:
    subject = _hybrid(1, actual_end=date(2024, 6, 1))
    peers = [_hybrid(10 + i) for i in range(8)]
    source = InMemoryTimePeerSource([subject, *peers])
    first = assess_time(subject, source)
    second = assess_time(subject, source)
    assert first.time_anomaly_score == second.time_anomaly_score
    assert first.explanation == second.explanation
    assert first.peer_project_ids == second.peer_project_ids


def test_peer_record_and_result_exclude_leakage_fields() -> None:
    fields = set(TimePeerRecord.__dataclass_fields__)
    assert fields.isdisjoint(FORBIDDEN_MODEL_INPUT_COLUMNS)
    subject = _hybrid(1)
    result = assess_time(subject, InMemoryTimePeerSource([subject]))
    blob = result.explanation.casefold()
    for token in ("scenario_type", "demo_stuck", "demo_case_id", "anomaly_notes", "overlap_group"):
        assert token not in blob


def test_mild_delay_is_detected_but_not_automatically_flagged() -> None:
    subject = _hybrid(1, actual_end=date(2024, 4, 20))
    peers = [_hybrid(10 + i) for i in range(8)]
    result = assess_time(subject, InMemoryTimePeerSource([subject, *peers]))
    assert result.slippage_days is not None
    assert result.slippage_days > 0
    assert result.delay_detected is True
    assert result.flagged is False
    assert CAUSE_NOT_ESTABLISHED in result.explanation
    assert result.time_anomaly_score is not None
    assert result.time_anomaly_score < 60


def _insert_project(session: Session, **overrides: object) -> Project:
    values: dict[str, object] = {
        "internal_project_id": "internal:synthetic:time:db:1",
        "internal_id_kind": "internal_surrogate_hash",
        "internal_id_scheme": "sarvsakshi_internal_work_v1",
        "is_synthetic": True,
        "synthetic_label": SYNTHETIC_LABEL,
        "lifecycle_stage": "ONGOING",
        "state": "Andhra Pradesh",
        "constituency": "KURNOOL",
        "category": "Normal/Others",
        "work_description": TANKS,
        "allocation_amount": 500_000,
        "recommended_date": date(2023, 6, 1),
        "status": "Ongoing",
    }
    values.update(overrides)
    row = Project(**values)
    session.add(row)
    session.flush()
    return row


def test_persists_time_evidence_not_fusion(client) -> None:
    session = get_session_factory()()
    try:
        subject = _insert_project(session, internal_project_id="internal:synthetic:time:db:subject")
        for i in range(8):
            _insert_project(session, internal_project_id=f"internal:synthetic:time:db:peer:{i}")
        session.commit()
        start = AS_OF - timedelta(days=70)
        schedules = {
            row.internal_project_id: HybridSchedule(
                internal_project_id=row.internal_project_id,
                planned_start_date=start,
                planned_completion_date=start + timedelta(days=100),
                actual_start_date=start,
                actual_completion_date=None,
                physical_progress_percent=20 if row.id == subject.id else 65,
                as_of_date=AS_OF,
            )
            for row in session.scalars(select(Project)).all()
        }
        result = assess_project_time(
            session,
            subject.id,
            mode=TimeMode.HYBRID_TEST,
            persist=True,
            schedules=schedules,
        )
        assert result.time_mode == TimeMode.HYBRID_TEST
        stored = session.scalars(
            select(EvidenceObjectRow).where(EvidenceObjectRow.project_id == subject.id)
        ).all()
        assert len(stored) == 1
        assert stored[0].engine == "time"
        assert stored[0].engine_version == ENGINE_VERSION
        keys = {fact.key for fact in stored[0].facts}
        assert {"time_anomaly_score", "evidence_confidence", "time_mode", "dataset_type"}.issubset(keys)
        fusion_count = session.scalar(select(func.count()).select_from(FusionScore)) or 0
        assert fusion_count == 0
    finally:
        session.close()


def test_time_intelligence_api_real_mode(client) -> None:
    session = get_session_factory()()
    try:
        subject = _insert_project(
            session,
            internal_project_id="internal:synthetic:time:api:subject",
            status="Unsanctioned",
            lifecycle_stage="FUTURE",
        )
        session.commit()
        project_id = subject.id
    finally:
        session.close()

    missing = client.get("/api/v1/projects/999999/time-intelligence")
    assert missing.status_code == 404

    response = client.get(f"/api/v1/projects/{project_id}/time-intelligence")
    assert response.status_code == 200
    body = response.json()
    assert body["engine"] == "time"
    assert body["time_mode"] == "REAL"
    assert body["dataset_type"] == "REAL"
    assert body["time_anomaly_score"] is None
    assert body["planned_duration_days"] is None
    assert "INCONCLUSIVE" in body["explanation"]
    assert "fraud" not in str(body).casefold()
