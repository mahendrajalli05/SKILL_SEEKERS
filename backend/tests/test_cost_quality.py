from __future__ import annotations

from datetime import date

from app.engines.cost.constants import (
    FORBIDDEN_MODEL_INPUT_COLUMNS,
    SCOPE_CONSTITUENCY_CATEGORY,
    SCOPE_CONSTITUENCY_CATEGORY_WORK_TYPE,
)
from app.engines.cost.peers import InMemoryPeerSource, select_peers
from app.engines.cost.quality import compute_peer_quality
from app.engines.cost.types import PeerRecord
from app.engines.cost.work_type import derive_work_type

TANKS = "NA - Construction of water tanks"
ROADS = "NA - Construction of roads, approach roads, link roads and pathways"
SCHOOL = "NA - Construction of New Building"
ALT_ROADS = (
    "NA - Construction of roads, link roads, pathways or any other road "
    "with or without drainage system"
)


def _peer(
    project_id: int,
    *,
    work_description: str = TANKS,
    amount: int = 500_000,
    constituency: str = "KURNOOL",
) -> PeerRecord:
    return PeerRecord(
        project_id=project_id,
        internal_project_id=f"internal:synthetic:cost:{project_id}",
        constituency=constituency,
        category="Normal/Others",
        state="Andhra Pradesh",
        work_description=work_description,
        derived_work_type=derive_work_type(work_description),
        allocation_amount=amount,
        recommended_date=date(2023, 6, 1),
        is_synthetic=True,
    )


def test_precise_group_has_higher_quality_than_broad_category_mix() -> None:
    subject = _peer(1, work_description=ROADS)
    similar = [_peer(10 + i, work_description=ALT_ROADS) for i in range(8)]
    mixed = [
        _peer(20 + i, work_description=TANKS if i % 2 == 0 else SCHOOL)
        for i in range(8)
    ]
    precise = select_peers(subject, InMemoryPeerSource([subject, *similar]))
    broad = select_peers(subject, InMemoryPeerSource([subject, *mixed]))
    assert precise.scope is not None
    assert precise.scope.id == SCOPE_CONSTITUENCY_CATEGORY_WORK_TYPE
    assert broad.scope is not None
    assert broad.scope.id == SCOPE_CONSTITUENCY_CATEGORY
    precise_quality = compute_peer_quality(subject, precise.peers, precise.scope)
    broad_quality = compute_peer_quality(subject, broad.peers, broad.scope)
    assert precise_quality.score > broad_quality.score
    assert broad_quality.score <= 55
    assert "Jaccard" in precise_quality.rationale


def test_large_loose_group_quality_is_capped() -> None:
    subject = _peer(1, work_description=SCHOOL)
    mixed = [
        _peer(10 + i, work_description=TANKS if i % 3 else ROADS)
        for i in range(40)
    ]
    selection = select_peers(subject, InMemoryPeerSource([subject, *mixed]))
    quality = compute_peer_quality(subject, selection.peers, selection.scope)
    assert selection.peer_count == 40
    assert quality.score <= 55
    assert quality.median_work_type_similarity < 0.5


def test_result_fields_do_not_include_synthetic_labels() -> None:
    from app.engines.cost.types import CostIntelligenceResult

    fields = set(CostIntelligenceResult.__dataclass_fields__)
    assert fields.isdisjoint(FORBIDDEN_MODEL_INPUT_COLUMNS)
    assert "mp_name" not in fields
