from __future__ import annotations

from datetime import date

from app.engines.cost.work_type import derive_work_type
from app.engines.time.constants import FORBIDDEN_MODEL_INPUT_COLUMNS, REAL_LIMITATION_NOTE
from app.engines.time.peers import InMemoryTimePeerSource
from app.engines.time.service import assess_time
from app.engines.time.types import TimeAssessmentOutcome, TimeMode, TimePeerRecord

TANKS = "NA - Construction of water tanks"


def _real(
    project_id: int,
    *,
    status: str = "Unsanctioned",
    recommended: date | None = date(2023, 6, 1),
    constituency: str = "KURNOOL",
    work_description: str = TANKS,
) -> TimePeerRecord:
    return TimePeerRecord(
        project_id=project_id,
        internal_project_id=f"internal:real:{project_id}",
        constituency=constituency,
        category="Normal/Others",
        state="Andhra Pradesh",
        work_description=work_description,
        derived_work_type=derive_work_type(work_description),
        status=status,
        lifecycle_stage="FUTURE" if status in {"Unsanctioned", "Sanctioned"} else "COMPLETED",
        recommended_date=recommended,
        time_mode=TimeMode.REAL,
        observation_date=date(2026, 9, 9),
    )


def test_real_mode_uses_recommendation_and_status_only() -> None:
    subject = _real(1, status="Completed")
    peers = [_real(10 + i, status="Completed") for i in range(8)]
    result = assess_time(subject, InMemoryTimePeerSource([subject, *peers]))
    assert result.time_mode == TimeMode.REAL
    assert result.dataset_type == "REAL"
    assert result.outcome == TimeAssessmentOutcome.INSUFFICIENT_EVIDENCE
    assert result.time_anomaly_score is None
    assert result.planned_duration_days is None
    assert result.actual_duration_days is None
    assert result.elapsed_duration_days is None
    assert result.slippage_days is None
    assert result.physical_progress_percent is None
    assert result.flagged is False
    assert result.recommendation_age_days is not None
    assert result.observed_status == "Completed"
    assert REAL_LIMITATION_NOTE in result.explanation
    assert "INCONCLUSIVE / INSUFFICIENT EVIDENCE" in result.explanation
    assert result.evidence_confidence > 0
    assert result.evidence_confidence <= 25
    assert "HYBRID/TEST" not in result.explanation
    assert "fraud" not in result.explanation.casefold()


def test_real_mode_missing_execution_dates_never_scored() -> None:
    subject = _real(1, status="Ongoing")
    result = assess_time(subject, InMemoryTimePeerSource([subject]))
    assert result.time_anomaly_score is None
    assert result.planned_start_date is None
    assert result.actual_completion_date is None
    assert result.signal_kind == "insufficient_execution_timing"


def test_real_mode_missing_recommended_date_has_zero_confidence() -> None:
    subject = _real(1, recommended=None)
    result = assess_time(subject, InMemoryTimePeerSource([subject]))
    assert result.recommendation_age_days is None
    assert result.evidence_confidence == 0
    assert result.time_anomaly_score is None


def test_real_peer_record_excludes_label_columns() -> None:
    fields = set(TimePeerRecord.__dataclass_fields__)
    assert fields.isdisjoint(FORBIDDEN_MODEL_INPUT_COLUMNS)
    for name in (
        "scenario_type",
        "demo_case_id",
        "mixed_signals",
        "anomaly_notes",
        "overlap_group_id",
        "coordinate_source",
    ):
        assert name not in fields
