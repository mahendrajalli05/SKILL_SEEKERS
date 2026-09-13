from __future__ import annotations

from datetime import date

from app.engines.cost.constants import (
    MIN_PEER_COUNT,
    SCOPE_CONSTITUENCY_CATEGORY,
    SCOPE_CONSTITUENCY_CATEGORY_WORK_TYPE,
    SCOPE_STATE_BROADER_WORK_TYPE,
    SCOPE_STATE_CATEGORY_WORK_TYPE,
)
from app.engines.cost.peers import InMemoryPeerSource, select_peers
from app.engines.cost.types import PeerRecord
from app.engines.cost.work_type import derive_work_type

TANKS = "NA - Construction of water tanks"
ROADS = "NA - Construction of roads, approach roads, link roads and pathways"
SCHOOL = "NA - Construction of New Building"


def _peer(
    project_id: int,
    *,
    constituency: str = "KURNOOL",
    category: str = "Normal/Others",
    state: str = "Andhra Pradesh",
    work_description: str = TANKS,
    amount: int = 500_000,
    is_synthetic: bool = True,
) -> PeerRecord:
    return PeerRecord(
        project_id=project_id,
        internal_project_id=f"internal:synthetic:cost:{project_id}",
        constituency=constituency,
        category=category,
        state=state,
        work_description=work_description,
        derived_work_type=derive_work_type(work_description),
        allocation_amount=amount,
        recommended_date=date(2023, 6, 1),
        is_synthetic=is_synthetic,
    )


def test_sufficient_constituency_category_work_type() -> None:
    subject = _peer(1, amount=500_000)
    others = [_peer(i, amount=400_000 + i * 1_000) for i in range(2, 10)]
    selection = select_peers(subject, InMemoryPeerSource([subject, *others]))
    assert selection.scope is not None
    assert selection.scope.id == SCOPE_CONSTITUENCY_CATEGORY_WORK_TYPE
    assert selection.peer_count == 8
    assert selection.scope.geography == "KURNOOL"


def test_constituency_broader_category_fallback() -> None:
    subject = _peer(1, work_description=SCHOOL, amount=500_000)
    same_category = [
        _peer(10 + i, work_description=ROADS if i % 2 == 0 else TANKS, amount=400_000)
        for i in range(8)
    ]
    selection = select_peers(subject, InMemoryPeerSource([subject, *same_category]))
    assert selection.scope is not None
    assert selection.scope.id == SCOPE_CONSTITUENCY_CATEGORY
    assert selection.peer_count == 8
    assert SCOPE_CONSTITUENCY_CATEGORY_WORK_TYPE in selection.attempted_scopes
    assert selection.best_attempt_peer_count == 8


def test_no_peers_at_all() -> None:
    subject = _peer(1, constituency="UNIQUE-PC", work_description="NA - Unique title abc")
    selection = select_peers(subject, InMemoryPeerSource([subject]))
    assert selection.scope is None
    assert selection.peer_count == 0
    assert selection.best_attempt_peer_count == 0


def test_insufficient_peers_report_best_attempt_count() -> None:
    subject = _peer(
        1,
        constituency="UNIQUE-PC",
        work_description="NA - Completely unique observed title xyz",
    )
    others = [
        _peer(2, constituency="UNIQUE-PC", work_description=ROADS),
        _peer(3, constituency="UNIQUE-PC", work_description=TANKS),
        _peer(4, constituency="UNIQUE-PC", work_description=SCHOOL),
    ]
    selection = select_peers(subject, InMemoryPeerSource([subject, *others]))
    assert selection.scope is None
    assert selection.peer_count == 0
    assert selection.best_attempt_peer_count == 3


def test_insufficient_constituency_peers_fallback_to_ap_state() -> None:
    subject = _peer(
        1,
        constituency="ELURU",
        category="Repair and Renovation",
        work_description=SCHOOL,
        amount=500_000,
    )
    local = [
        _peer(2, constituency="ELURU", category="Repair and Renovation", work_description=ROADS),
        _peer(3, constituency="ELURU", category="Repair and Renovation", work_description=TANKS),
    ]
    statewide = [
        _peer(
            10 + i,
            constituency="KURNOOL",
            category="Repair and Renovation",
            work_description=SCHOOL,
            amount=450_000,
        )
        for i in range(8)
    ]
    selection = select_peers(subject, InMemoryPeerSource([subject, *local, *statewide]))
    assert selection.scope is not None
    assert selection.scope.id == SCOPE_STATE_CATEGORY_WORK_TYPE
    assert selection.peer_count == 8
    assert SCOPE_CONSTITUENCY_CATEGORY_WORK_TYPE in selection.attempted_scopes
    assert SCOPE_CONSTITUENCY_CATEGORY in selection.attempted_scopes


def test_state_fallback_uses_broader_work_type_when_category_too_sparse() -> None:
    subject = _peer(
        1,
        constituency="ELURU",
        category="Repair and Renovation",
        work_description=SCHOOL,
    )
    local = [
        _peer(2, constituency="ELURU", category="Repair and Renovation", work_description=ROADS),
        _peer(3, constituency="ELURU", category="Repair and Renovation", work_description=TANKS),
    ]
    broader = [
        _peer(
            20 + i,
            constituency="GUNTUR",
            category="Normal/Others",
            work_description=SCHOOL,
        )
        for i in range(8)
    ]
    selection = select_peers(subject, InMemoryPeerSource([subject, *local, *broader]))
    assert selection.scope is not None
    assert selection.scope.id == SCOPE_STATE_BROADER_WORK_TYPE
    assert selection.peer_count == 8
    assert SCOPE_STATE_CATEGORY_WORK_TYPE in selection.attempted_scopes


def test_no_usable_peers() -> None:
    subject = _peer(
        1,
        constituency="UNIQUE-PC",
        work_description="NA - Completely unique observed title xyz",
    )
    others = [
        _peer(2, constituency="UNIQUE-PC", work_description=ROADS),
        _peer(3, constituency="UNIQUE-PC", work_description=TANKS),
        _peer(4, constituency="KURNOOL", work_description=ROADS),
    ]
    selection = select_peers(subject, InMemoryPeerSource([subject, *others]))
    assert selection.scope is None
    assert selection.peer_count == 0


def test_non_ap_does_not_use_other_states_as_fallback() -> None:
    subject = _peer(
        1,
        constituency="GURGAON",
        state="Haryana",
        work_description=TANKS,
    )
    local = [_peer(2, constituency="GURGAON", state="Haryana", work_description=ROADS)]
    plenty_elsewhere = [
        _peer(10 + i, constituency="KURNOOL", state="Andhra Pradesh", work_description=TANKS)
        for i in range(20)
    ]
    same_mp_other_pc = [
        _peer(50 + i, constituency="FARIDABAD", state="Haryana", work_description=TANKS)
        for i in range(20)
    ]
    selection = select_peers(
        subject,
        InMemoryPeerSource([subject, *local, *plenty_elsewhere, *same_mp_other_pc]),
    )
    assert selection.scope is None
    assert SCOPE_STATE_CATEGORY_WORK_TYPE not in selection.attempted_scopes


def test_zero_amount_peers_are_excluded() -> None:
    subject = _peer(1, amount=500_000)
    zeros = [_peer(i, amount=0) for i in range(2, 10)]
    valid = [_peer(20 + i, amount=400_000) for i in range(5)]
    selection = select_peers(subject, InMemoryPeerSource([subject, *zeros, *valid]))
    assert selection.peer_count == 5
    assert all(peer.allocation_amount and peer.allocation_amount > 0 for peer in selection.peers)


def test_synthetic_and_real_rows_are_not_mixed() -> None:
    subject = _peer(1, is_synthetic=True)
    synthetic = [_peer(i, is_synthetic=True, amount=400_000) for i in range(2, 8)]
    real = [_peer(100 + i, is_synthetic=False, amount=400_000) for i in range(20)]
    selection = select_peers(subject, InMemoryPeerSource([subject, *synthetic, *real]))
    assert selection.peer_count == 6
    assert all(peer.is_synthetic for peer in selection.peers)


def test_homonymous_geographic_constituency_does_not_cross_state() -> None:
    subject = _peer(
        1,
        constituency="KURNOOL",
        state="Andhra Pradesh",
        work_description=TANKS,
    )
    local = [
        _peer(
            i,
            constituency="KURNOOL",
            state="Andhra Pradesh",
            work_description=TANKS,
            amount=400_000,
        )
        for i in range(2, 8)
    ]
    other_state = [
        _peer(
            50 + i,
            constituency="KURNOOL",
            state="Haryana",
            work_description=TANKS,
            amount=400_000,
        )
        for i in range(20)
    ]
    selection = select_peers(subject, InMemoryPeerSource([subject, *local, *other_state]))
    assert selection.peer_count == 6
    assert all(peer.state == "Andhra Pradesh" for peer in selection.peers)


def test_rajya_sabha_is_excluded_from_constituency_geography() -> None:
    subject = _peer(
        1,
        constituency="Sitting Rajya Sabha",
        state="Andhra Pradesh",
        work_description=TANKS,
        amount=500_000,
    )
    local = [
        _peer(
            i,
            constituency="Sitting Rajya Sabha",
            state="Andhra Pradesh",
            work_description=TANKS,
            amount=400_000,
        )
        for i in range(2, 8)
    ]
    other_state = [
        _peer(
            50 + i,
            constituency="Sitting Rajya Sabha",
            state="Haryana",
            work_description=TANKS,
            amount=400_000,
        )
        for i in range(20)
    ]
    statewide = [
        _peer(
            80 + i,
            constituency="KURNOOL",
            state="Andhra Pradesh",
            work_description=TANKS,
            amount=410_000,
        )
        for i in range(5)
    ]
    selection = select_peers(
        subject,
        InMemoryPeerSource([subject, *local, *other_state, *statewide]),
    )
    assert selection.constituency_usable is False
    assert SCOPE_CONSTITUENCY_CATEGORY_WORK_TYPE not in selection.attempted_scopes
    assert SCOPE_CONSTITUENCY_CATEGORY not in selection.attempted_scopes
    assert selection.scope is not None
    assert selection.scope.id == SCOPE_STATE_CATEGORY_WORK_TYPE
    assert all(peer.state == "Andhra Pradesh" for peer in selection.peers)
    assert all(peer.constituency != "Haryana" for peer in selection.peers)
    assert "chamber" in (selection.constituency_exclusion_reason or "").casefold() or "house" in (
        selection.constituency_exclusion_reason or ""
    ).casefold()


def test_similar_road_titles_form_a_precise_group() -> None:
    alt_roads = (
        "NA - Construction of roads, link roads, pathways or any other road "
        "with or without drainage system"
    )
    subject = _peer(1, work_description=ROADS, amount=500_000)
    others = [_peer(10 + i, work_description=alt_roads, amount=400_000) for i in range(8)]
    unrelated = [_peer(30 + i, work_description=TANKS, amount=400_000) for i in range(8)]
    selection = select_peers(subject, InMemoryPeerSource([subject, *others, *unrelated]))
    assert selection.scope is not None
    assert selection.scope.id == SCOPE_CONSTITUENCY_CATEGORY_WORK_TYPE
    assert selection.peer_count == 8
    assert all("road" in peer.derived_work_type for peer in selection.peers)


def test_peer_record_does_not_use_mp_name() -> None:
    assert "mp_name" not in PeerRecord.__dataclass_fields__


def test_selection_is_deterministic() -> None:
    subject = _peer(1)
    others = [_peer(i, amount=400_000 + i) for i in range(2, 12)]
    source = InMemoryPeerSource([subject, *others])
    first = select_peers(subject, source, min_peer_count=MIN_PEER_COUNT)
    second = select_peers(subject, source, min_peer_count=MIN_PEER_COUNT)
    assert first.scope == second.scope
    assert [p.project_id for p in first.peers] == [p.project_id for p in second.peers]
