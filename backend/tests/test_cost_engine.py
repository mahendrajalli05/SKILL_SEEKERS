from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_session_factory
from app.engines.cost.constants import (
    ENGINE_VERSION,
    FORBIDDEN_MODEL_INPUT_COLUMNS,
    SCOPE_CONSTITUENCY_CATEGORY_WORK_TYPE,
    SCOPE_STATE_CATEGORY_WORK_TYPE,
)
from app.engines.cost.peers import InMemoryPeerSource
from app.engines.cost.service import assess_cost, assess_project_cost
from app.engines.cost.types import CostAssessmentOutcome, PeerRecord
from app.engines.cost.work_type import derive_work_type
from app.models.evidence import EvidenceObjectRow
from app.models.fusion import FusionScore
from app.models.project import Project

SYNTHETIC_LABEL = "SYNTHETIC: cost-intelligence unit test (not a government project)"
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
    amount: int | None = 500_000,
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


def _cluster(subject_id: int, subject_amount: int, *, n_peers: int = 8) -> list[PeerRecord]:
    subject = _peer(subject_id, amount=subject_amount)
    peers = [_peer(10 + i, amount=480_000 + i * 5_000) for i in range(n_peers)]
    return [subject, *peers]


def test_peer_record_excludes_synthetic_label_columns() -> None:
    fields = set(PeerRecord.__dataclass_fields__)
    assert fields.isdisjoint(FORBIDDEN_MODEL_INPUT_COLUMNS)
    assert "mp_name" not in fields


def test_normal_cost_project_is_not_flagged() -> None:
    rows = _cluster(1, 500_000)
    result = assess_cost(rows[0], InMemoryPeerSource(rows))
    assert result.outcome == CostAssessmentOutcome.WITHIN_PEER_RANGE
    assert result.flagged is False
    assert result.cost_anomaly_score is not None
    assert result.cost_anomaly_score < 60
    assert result.peer_scope == SCOPE_CONSTITUENCY_CATEGORY_WORK_TYPE
    assert result.why_not_flagged is not None
    assert result.why_flagged is None
    assert result.expected_range_low is not None
    assert result.expected_range_high is not None
    assert result.evidence_confidence > 0
    assert "Not flagged as an Allocation Cost Anomaly" in result.explanation
    assert result.peer_quality > 0
    assert result.signal_kind == "allocation_cost_anomaly"
    assert "fraud" not in result.explanation.casefold()


def test_high_cost_project_is_flagged() -> None:
    rows = _cluster(1, 2_000_000)
    result = assess_cost(rows[0], InMemoryPeerSource(rows))
    assert result.outcome == CostAssessmentOutcome.COST_ANOMALY
    assert result.flagged is True
    assert result.cost_anomaly_score is not None
    assert result.cost_anomaly_score >= 60
    assert result.deviation_percentage is not None
    assert result.deviation_percentage > 0
    assert result.why_flagged is not None
    assert "Cost Anomaly" in result.why_flagged
    assert "above the median" in result.why_flagged
    assert "fraud" not in result.why_flagged.casefold()


def test_low_cost_project_is_flagged() -> None:
    rows = _cluster(1, 1)
    result = assess_cost(rows[0], InMemoryPeerSource(rows))
    assert result.flagged is True
    assert result.outcome == CostAssessmentOutcome.COST_ANOMALY
    assert result.deviation_percentage is not None
    assert result.deviation_percentage < 0
    assert "below the median" in (result.why_flagged or "")


def test_zero_and_missing_amount_are_invalid() -> None:
    peers = [_peer(i, amount=400_000) for i in range(2, 12)]
    zero = assess_cost(_peer(1, amount=0), InMemoryPeerSource([_peer(1, amount=0), *peers]))
    missing = assess_cost(
        _peer(1, amount=None),
        InMemoryPeerSource([_peer(1, amount=None), *peers]),
    )
    for result in (zero, missing):
        assert result.outcome == CostAssessmentOutcome.INVALID_AMOUNT
        assert result.cost_anomaly_score is None
        assert result.flagged is False
        assert result.evidence_confidence == 0
        assert "was not assessed" in result.explanation


def test_insufficient_peers_do_not_produce_anomaly_score() -> None:
    subject = _peer(
        1,
        constituency="UNIQUE-PC",
        work_description="NA - Completely unique observed title xyz",
    )
    others = [
        _peer(2, constituency="UNIQUE-PC", work_description=ROADS),
        _peer(3, constituency="UNIQUE-PC", work_description=TANKS),
    ]
    result = assess_cost(subject, InMemoryPeerSource([subject, *others]))
    assert result.outcome == CostAssessmentOutcome.INSUFFICIENT_EVIDENCE
    assert result.cost_anomaly_score is None
    assert result.flagged is False
    assert result.peer_scope is None
    assert result.evidence_confidence <= 20
    assert result.best_attempt_peer_count >= 0
    assert "Insufficient evidence" in result.explanation


def test_constituency_fallback_to_andhra_pradesh_state() -> None:
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
            amount=450_000 + i * 1_000,
        )
        for i in range(8)
    ]
    result = assess_cost(subject, InMemoryPeerSource([subject, *local, *statewide]))
    assert result.peer_scope == SCOPE_STATE_CATEGORY_WORK_TYPE
    assert result.peer_count == 8
    assert result.cost_anomaly_score is not None
    assert "Andhra Pradesh state" in (result.peer_scope_label or "")


def test_output_is_deterministic() -> None:
    rows = _cluster(1, 750_000)
    first = assess_cost(rows[0], InMemoryPeerSource(rows))
    second = assess_cost(rows[0], InMemoryPeerSource(rows))
    assert first.cost_anomaly_score == second.cost_anomaly_score
    assert first.deviation_percentage == second.deviation_percentage
    assert first.baseline == second.baseline
    assert first.peer_project_ids == second.peer_project_ids
    assert first.explanation == second.explanation
    assert [item.project_id for item in first.comparable_projects] == [
        item.project_id for item in second.comparable_projects
    ]


def test_comparables_are_from_selected_peer_scope() -> None:
    rows = _cluster(1, 500_000, n_peers=12)
    result = assess_cost(rows[0], InMemoryPeerSource(rows))
    assert result.peer_count == 12
    assert len(result.comparable_projects) == 10
    comparable_ids = {item.project_id for item in result.comparable_projects}
    assert 1 not in comparable_ids
    assert comparable_ids.issubset(set(result.peer_project_ids))


def _insert_synthetic(session: Session, **overrides: object) -> Project:
    values: dict[str, object] = {
        "internal_project_id": "internal:synthetic:cost:db:1",
        "internal_id_kind": "internal_surrogate_hash",
        "internal_id_scheme": "sarvsakshi_internal_work_v1",
        "is_synthetic": True,
        "synthetic_label": SYNTHETIC_LABEL,
        "lifecycle_stage": "FUTURE",
        "state": "Andhra Pradesh",
        "constituency": "KURNOOL",
        "category": "Normal/Others",
        "work_description": TANKS,
        "allocation_amount": 500_000,
        "recommended_date": date(2023, 6, 1),
        "status": "Unsanctioned",
    }
    values.update(overrides)
    row = Project(**values)
    session.add(row)
    session.flush()
    return row


def test_persists_cost_evidence_object_not_fusion(client) -> None:
    session = get_session_factory()()
    try:
        subject = _insert_synthetic(session, internal_project_id="internal:synthetic:cost:db:subject")
        for i in range(8):
            _insert_synthetic(
                session,
                internal_project_id=f"internal:synthetic:cost:db:peer:{i}",
                allocation_amount=480_000 + i * 2_000,
            )
        session.commit()
        project_id = subject.id
        result = assess_project_cost(session, project_id, persist=True)
        assert result.peer_scope == SCOPE_CONSTITUENCY_CATEGORY_WORK_TYPE
        stored = session.scalars(
            select(EvidenceObjectRow).where(EvidenceObjectRow.project_id == project_id)
        ).all()
        assert len(stored) == 1
        assert stored[0].engine == "cost"
        assert stored[0].engine_version == ENGINE_VERSION
        assert stored[0].evidence_type == "allocation_cost_anomaly"
        keys = {fact.key for fact in stored[0].facts}
        assert {
            "peer_scope",
            "peer_count",
            "baseline",
            "actual_amount",
            "deviation_percentage",
            "cost_anomaly_score",
            "evidence_confidence",
            "peer_quality",
            "similarity_rationale",
            "expected_range",
            "peer_project_ids",
        }.issubset(keys)
        fusion_count = session.scalar(select(func.count()).select_from(FusionScore)) or 0
        assert fusion_count == 0
    finally:
        session.close()


def test_cost_intelligence_api(client) -> None:
    session = get_session_factory()()
    try:
        subject = _insert_synthetic(session, internal_project_id="internal:synthetic:cost:api:subject")
        for i in range(8):
            _insert_synthetic(
                session,
                internal_project_id=f"internal:synthetic:cost:api:peer:{i}",
                allocation_amount=500_000,
            )
        session.commit()
        project_id = subject.id
    finally:
        session.close()

    missing = client.get("/api/v1/projects/999999/cost-intelligence")
    assert missing.status_code == 404

    response = client.get(f"/api/v1/projects/{project_id}/cost-intelligence")
    assert response.status_code == 200
    body = response.json()
    assert body["engine"] == "cost"
    assert body["peer_scope"] == SCOPE_CONSTITUENCY_CATEGORY_WORK_TYPE
    assert body["peer_count"] == 8
    assert body["actual_amount"] == 500_000
    assert body["cost_anomaly_score"] == 0
    assert body["flagged"] is False
    assert body["evidence_confidence"] >= 0
    assert body["peer_quality"] > 0
    assert body["signal_kind"] == "allocation_cost_anomaly"
    assert body["expected_range_low"] is not None
    assert body["expected_range_high"] is not None
    assert "fraud" not in body["explanation"].casefold()
    assert "fraud" not in str(body).casefold()
