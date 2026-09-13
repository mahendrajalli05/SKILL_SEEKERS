from __future__ import annotations

from datetime import date

from app.engines.cost.work_type import derive_work_type
from app.engines.time.constants import (
    SCOPE_CONSTITUENCY_CATEGORY,
    SCOPE_CONSTITUENCY_CATEGORY_WORK_TYPE,
    SCOPE_STATE_CATEGORY_WORK_TYPE,
)
from app.engines.time.peers import InMemoryTimePeerSource, select_peers
from app.engines.time.types import TimeMode, TimePeerRecord

TANKS = "NA - Construction of water tanks"
ROADS = "NA - Construction of roads, approach roads, link roads and pathways"
SCHOOL = "NA - Construction of New Building"
AS_OF = date(2024, 6, 30)


def _hybrid(
    project_id: int,
    *,
    constituency: str = "KURNOOL",
    category: str = "Normal/Others",
    state: str = "Andhra Pradesh",
    work_description: str = TANKS,
    status: str = "Completed",
    planned_start: date = date(2024, 1, 1),
    planned_end: date = date(2024, 4, 10),
    actual_start: date = date(2024, 1, 1),
    actual_end: date | None = date(2024, 4, 10),
    progress: int | None = 100,
) -> TimePeerRecord:
    lifecycle = "COMPLETED" if actual_end else "ONGOING"
    return TimePeerRecord(
        project_id=project_id,
        internal_project_id=f"internal:time:{project_id}",
        constituency=constituency,
        category=category,
        state=state,
        work_description=work_description,
        derived_work_type=derive_work_type(work_description),
        status=status,
        lifecycle_stage=lifecycle,
        recommended_date=date(2023, 6, 1),
        time_mode=TimeMode.HYBRID_TEST,
        planned_start_date=planned_start,
        planned_completion_date=planned_end,
        actual_start_date=actual_start,
        actual_completion_date=actual_end,
        physical_progress_percent=progress,
        as_of_date=AS_OF,
        observation_date=date(2026, 9, 9),
    )


def test_sufficient_constituency_category_work_type() -> None:
    subject = _hybrid(1)
    others = [_hybrid(i, actual_end=date(2024, 4, 10 + (i % 5))) for i in range(2, 10)]
    selection = select_peers(subject, InMemoryTimePeerSource([subject, *others]))
    assert selection.scope is not None
    assert selection.scope.id == SCOPE_CONSTITUENCY_CATEGORY_WORK_TYPE
    assert selection.peer_count == 8


def test_constituency_broader_category_fallback() -> None:
    subject = _hybrid(1, work_description=SCHOOL)
    same_category = [
        _hybrid(10 + i, work_description=ROADS if i % 2 == 0 else TANKS)
        for i in range(8)
    ]
    selection = select_peers(subject, InMemoryTimePeerSource([subject, *same_category]))
    assert selection.scope is not None
    assert selection.scope.id == SCOPE_CONSTITUENCY_CATEGORY
    assert SCOPE_CONSTITUENCY_CATEGORY_WORK_TYPE in selection.attempted_scopes


def test_state_fallback_when_local_peers_insufficient() -> None:
    subject = _hybrid(1, constituency="ELURU", work_description=SCHOOL, category="Repair and Renovation")
    local = [
        _hybrid(2, constituency="ELURU", category="Repair and Renovation", work_description=ROADS),
        _hybrid(3, constituency="ELURU", category="Repair and Renovation", work_description=TANKS),
    ]
    statewide = [
        _hybrid(
            10 + i,
            constituency="KURNOOL",
            category="Repair and Renovation",
            work_description=SCHOOL,
            actual_end=date(2024, 4, 12),
        )
        for i in range(8)
    ]
    selection = select_peers(subject, InMemoryTimePeerSource([subject, *local, *statewide]))
    assert selection.scope is not None
    assert selection.scope.id == SCOPE_STATE_CATEGORY_WORK_TYPE
    assert selection.peer_count == 8


def test_insufficient_peers_do_not_fabricate() -> None:
    subject = _hybrid(1, constituency="UNIQUE-PC", work_description="NA - Completely unique xyz")
    others = [
        _hybrid(2, constituency="UNIQUE-PC", work_description=ROADS),
        _hybrid(3, constituency="UNIQUE-PC", work_description=TANKS),
    ]
    selection = select_peers(subject, InMemoryTimePeerSource([subject, *others]))
    assert selection.scope is None
    assert selection.peer_count == 0
    assert selection.best_attempt_peer_count < 5


def test_open_and_closed_families_are_not_mixed() -> None:
    subject = _hybrid(1, actual_end=None, progress=20, status="Ongoing")
    closed = [_hybrid(10 + i, actual_end=date(2024, 4, 10)) for i in range(8)]
    selection = select_peers(subject, InMemoryTimePeerSource([subject, *closed]))
    assert selection.scope is None
    assert selection.peer_count == 0


def test_real_peers_require_same_status() -> None:
    def real(project_id: int, status: str) -> TimePeerRecord:
        return TimePeerRecord(
            project_id=project_id,
            internal_project_id=f"internal:real:{project_id}",
            constituency="KURNOOL",
            category="Normal/Others",
            state="Andhra Pradesh",
            work_description=TANKS,
            derived_work_type=derive_work_type(TANKS),
            status=status,
            lifecycle_stage="FUTURE",
            recommended_date=date(2023, 6, 1),
            time_mode=TimeMode.REAL,
            observation_date=date(2026, 9, 9),
        )

    subject = real(1, "Unsanctioned")
    peers = [real(10 + i, "Unsanctioned") for i in range(8)]
    wrong = [real(30 + i, "Completed") for i in range(8)]
    selection = select_peers(subject, InMemoryTimePeerSource([subject, *peers, *wrong]))
    assert selection.peer_count == 8
    assert all(peer.status == "Unsanctioned" for peer in selection.peers)


def test_non_geographic_constituency_skips_local_scope() -> None:
    subject = _hybrid(1, constituency="Sitting Rajya Sabha")
    local = [_hybrid(10 + i, constituency="Sitting Rajya Sabha") for i in range(8)]
    statewide = [_hybrid(20 + i, constituency="KURNOOL") for i in range(8)]
    selection = select_peers(subject, InMemoryTimePeerSource([subject, *local, *statewide]))
    assert selection.constituency_usable is False
    assert selection.scope is not None
    assert selection.scope.id == SCOPE_CONSTITUENCY_CATEGORY_WORK_TYPE or "state" in (selection.scope.id)
    # Sitting RS is excluded from constituency geography, so selected scope should be state.
    assert "state" in selection.scope.id
