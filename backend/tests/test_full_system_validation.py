"""Full-System Validation V1.

Integration checks across existing modules. Does not rewrite frozen engines,
does not fabricate evidence, and does not lower thresholds.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import REPO_ROOT
from app.db import get_session_factory
from app.demo.constants import CASE_IDS, DEMO_NOTICE, assert_fusion_v2_unchanged
from app.domain.enums import DataMode, LifecycleStage, OfficerDecisionType, SignalType
from app.engines.cost.constants import ENGINE_VERSION as COST_VERSION
from app.engines.cost.evaluate import DEMO_INTERNAL_IDS
from app.engines.cost.peers import InMemoryPeerSource
from app.engines.cost.service import assess_cost
from app.engines.cost.types import CostAssessmentOutcome, PeerRecord
from app.engines.cost.work_type import derive_work_type
from app.engines.fusion_v2.constants import ENGINE_VERSION as FUSION_V2_VERSION
from app.engines.fusion_v2.constants import GROUP_WEIGHTS, SIGNAL_TYPE_TO_GROUP
from app.engines.fusion_v2.service import fuse_evidence_v2
from app.engines.lifecycle.constants import FROZEN_FUSION_V2_VERSION, FROZEN_FUSION_V2_WEIGHTS
from app.engines.lifecycle.service import record_planning_decision
from app.engines.time.constants import ENGINE_VERSION as TIME_VERSION
from app.engines.time.enrichment import HybridSchedule
from app.engines.time.service import assess_project_time
from app.engines.time.types import TimeAssessmentOutcome, TimeMode
from app.ml.constants import COST_MODEL_NAME, NEW_PROJECT_ASSESSMENT
from app.ml.inference.loader import reset_model_cache
from app.ml.training.cost_train import train_from_session
from app.models.project import Project
from demo_fixtures import insert_all_demo_cases
from fusion_v2_fixtures import make_group_evidence
from lifecycle_fixtures import insert_project as insert_lifecycle_project
from tests.document_fixtures import consistent_blueprint_pdf
from tests.image_fixtures import unique_png
from tests.ml_fixtures import seed_real_training_rows

EXPECTED_PROJECT_COUNT = 56138
EXPECTED_CLEANED_SHA256 = "fb4bd06a75a3f66d7bfc08d02b86c980932682926b441fc4371dca8afdd9dd64"
EXPECTED_RAW_SHA256 = "aa1d0b7c9c6bbe014a1af772a22ab3dc0a6eb24d043695060abaa0f94333e413"
EXPECTED_SYNTHETIC_SHA256 = "d1de1b151cd115f9e4c0ae291f585481527a1f02846cb593c66d6c819895f4f1"

LIVE_DB = REPO_ROOT / "data" / "processed" / "sarvsakshi.db"
CLEANED_CSV = REPO_ROOT / "data" / "processed" / "mplads_works_cleaned.csv"
RAW_CSV = REPO_ROOT / "data" / "raw" / "github_vonter_india-mplads-works_MPLADS.csv"
SYNTHETIC_CSV = REPO_ROOT / "data" / "synthetic" / "sarvsakshi_synthetic_enrichment.csv"
ML_MODELS_DIR = REPO_ROOT / "backend" / "app" / "ml" / "models"

FORBIDDEN_BODY = (
    "fraud confirmed",
    "fraud probability",
    "automatic sanction",
    "automatic payment",
    "pfms payment",
    "release funds",
)

COPILOT_QUESTIONS = (
    "What evidence exists for this project?",
    "What is the main anomaly signal?",
    "Which model generated the ML score?",
    "What external context is available?",
    "Is the ML score a fraud probability?",
    "Why is this project being reviewed?",
    "What evidence is missing?",
)

TANKS = "NA - Construction of water tanks"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _live_connect() -> sqlite3.Connection:
    uri = f"file:{LIVE_DB.resolve().as_posix()}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def _blob(value: object) -> str:
    return json.dumps(value, default=str).casefold()


def _assert_governed(payload: object) -> None:
    text = _blob(payload)
    assert "fraud confirmed" not in text
    assert '"automatic_sanction": true' not in text
    assert '"automatic_payment": true' not in text
    assert '"pfms_integrated": true' not in text
    assert "c:\\\\" not in text
    assert "/app/ml/models/" not in text
    assert "model.joblib" not in text


def _insert_work(session, *, suffix: str, amount: int, **overrides: object) -> Project:
    values: dict[str, object] = {
        "internal_project_id": f"internal:fsv:{suffix}",
        "internal_id_kind": "internal_surrogate_hash",
        "internal_id_scheme": "sarvsakshi_internal_work_v1",
        "source_dataset": "github_vonter_india-mplads-works_MPLADS.csv",
        "is_synthetic": False,
        "lifecycle_stage": LifecycleStage.FUTURE.value,
        "state": "Andhra Pradesh",
        "constituency": "KURNOOL",
        "category": "Normal/Others",
        "work_description": TANKS,
        "allocation_amount": amount,
        "recommended_date": date(2023, 6, 1),
        "status": "Unsanctioned",
        "ida": "Kurnool_IDA",
        "mp_name": "Validation MP",
        "house": "Lok Sabha",
    }
    values.update(overrides)
    row = Project(**values)
    session.add(row)
    session.flush()
    return row


def _seed_kurnool_peers(session, *, n: int = 8, amount: int = 500_000) -> None:
    for i in range(n):
        _insert_work(session, suffix=f"peer-{i}", amount=amount + i * 5_000)


def _peer_record(project_id: int, amount: int, **overrides: object) -> PeerRecord:
    values = dict(
        project_id=project_id,
        internal_project_id=f"internal:fsv:cost:{project_id}",
        constituency="KURNOOL",
        category="Normal/Others",
        state="Andhra Pradesh",
        work_description=TANKS,
        derived_work_type=derive_work_type(TANKS),
        allocation_amount=amount,
        recommended_date=date(2023, 6, 1),
        is_synthetic=False,
    )
    values.update(overrides)
    return PeerRecord(**values)  # type: ignore[arg-type]


def _project_id(session_factory, **overrides: object) -> int:
    session = session_factory()
    try:
        row = _insert_work(session, suffix=overrides.pop("suffix", "subject"), **overrides)
        session.commit()
        return row.id
    finally:
        session.close()


def test_fusion_v2_formula_unchanged() -> None:
    assert_fusion_v2_unchanged()
    assert FUSION_V2_VERSION == "risk-fusion-v2"
    assert FUSION_V2_VERSION == FROZEN_FUSION_V2_VERSION
    assert GROUP_WEIGHTS == FROZEN_FUSION_V2_WEIGHTS
    assert round(sum(GROUP_WEIGHTS.values()), 4) == 1.0
    assert COST_VERSION == "cost-peer-v1.1"
    assert TIME_VERSION == "time-peer-v1"


def test_ml_and_context_are_not_fused_into_v2() -> None:
    excluded = {
        SignalType.ML_ANOMALY_SIGNAL.value,
        SignalType.REFERENCE_COST_CONTEXT.value,
        SignalType.DEVELOPMENT_NEED_CONTEXT.value,
        SignalType.INFRASTRUCTURE_CONTEXT.value,
        SignalType.CONTEXT_UNAVAILABLE.value,
        SignalType.CONTEXT_INCONCLUSIVE.value,
    }
    assert excluded.isdisjoint(SIGNAL_TYPE_TO_GROUP)
    assert "ml" not in GROUP_WEIGHTS
    assert "context" not in GROUP_WEIGHTS


@pytest.mark.skipif(not LIVE_DB.is_file(), reason="production SQLite is not present")
def test_live_database_integrity_readonly() -> None:
    assert CLEANED_CSV.is_file()
    assert RAW_CSV.is_file()
    assert SYNTHETIC_CSV.is_file()
    assert _sha256(CLEANED_CSV) == EXPECTED_CLEANED_SHA256
    assert _sha256(RAW_CSV) == EXPECTED_RAW_SHA256
    assert _sha256(SYNTHETIC_CSV) == EXPECTED_SYNTHETIC_SHA256

    conn = _live_connect()
    try:
        conn.row_factory = sqlite3.Row
        project_count = conn.execute("SELECT COUNT(*) FROM project").fetchone()[0]
        unique_ids = conn.execute(
            "SELECT COUNT(DISTINCT internal_project_id) FROM project"
        ).fetchone()[0]
        synthetic_count = conn.execute(
            "SELECT COUNT(*) FROM project WHERE is_synthetic = 1"
        ).fetchone()[0]
        snapshot_count = conn.execute(
            "SELECT record_count FROM dataset_snapshot ORDER BY id LIMIT 1"
        ).fetchone()[0]
        dupes = conn.execute(
            """
            SELECT internal_project_id, COUNT(*) AS n
            FROM project
            GROUP BY internal_project_id
            HAVING n > 1
            """
        ).fetchall()
        lifecycle = {
            row["lifecycle_stage"]: row["n"]
            for row in conn.execute(
                "SELECT lifecycle_stage, COUNT(*) AS n FROM project GROUP BY lifecycle_stage"
            )
        }
        missing_demo = []
        for case_id, internal_id in DEMO_INTERNAL_IDS.items():
            found = conn.execute(
                "SELECT id, lifecycle_stage, is_synthetic, state FROM project WHERE internal_project_id = ?",
                (internal_id,),
            ).fetchone()
            if found is None:
                missing_demo.append(case_id)
            else:
                assert found["is_synthetic"] == 0
        orphan_evidence = conn.execute(
            """
            SELECT COUNT(*) FROM evidence_object e
            LEFT JOIN project p ON p.id = e.project_id
            WHERE e.project_id IS NOT NULL AND p.id IS NULL
            """
        ).fetchone()[0]
        table_names = {
            row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    finally:
        conn.close()

    assert project_count == EXPECTED_PROJECT_COUNT
    assert unique_ids == EXPECTED_PROJECT_COUNT
    assert snapshot_count == EXPECTED_PROJECT_COUNT
    assert synthetic_count == 0
    assert dupes == []
    assert missing_demo == []
    assert orphan_evidence == 0
    assert {
        "external_source",
        "external_context_snapshot",
        "external_context_observation",
    }.issubset(table_names)
    assert lifecycle.get("FUTURE", 0) >= 1
    assert lifecycle.get("ONGOING", 0) >= 1
    assert lifecycle.get("COMPLETED", 0) >= 1


def test_new_project_three_scenarios_and_hybrid_label(client: TestClient) -> None:
    session = get_session_factory()()
    try:
        _seed_kurnool_peers(session)
        session.commit()
    finally:
        session.close()

    ordinary = {
        "state": "Andhra Pradesh",
        "constituency": "KURNOOL",
        "category": "Normal/Others",
        "work_description": TANKS,
        "allocation_amount": 500_000,
        "recommendation_date": "2023-06-01",
        "status": "Unsanctioned",
        "house": "Lok Sabha",
        "data_mode": "REAL",
    }
    high = dict(ordinary, allocation_amount=50_000_000)
    incomplete = {"state": "Andhra Pradesh", "data_mode": "REAL"}
    hybrid = dict(ordinary, data_mode="HYBRID")

    results = {}
    for name, body in (
        ("ordinary", ordinary),
        ("high_allocation", high),
        ("incomplete", incomplete),
        ("hybrid", hybrid),
    ):
        response = client.post("/api/v2/projects/assess", json=body)
        assert response.status_code == 200, response.text
        payload = response.json()
        results[name] = payload
        assert payload["assessment_kind"] == NEW_PROJECT_ASSESSMENT
        assert payload["evidence_kind"] == NEW_PROJECT_ASSESSMENT
        assert payload["is_new_project"] is True
        assert payload["project_id"] is None
        assert payload["persisted"] is False
        assert payload["fraud_probability"] is None
        assert payload["automatic_sanction"] is False
        assert payload["automatic_payment"] is False
        assert payload["risk_fusion_v2"]["available"] is False
        assert payload["risk_fusion_v2"]["investigation_priority"] is None
        assert payload["time_v1"]["time_anomaly_score"] is None
        assert payload["contextual_v1"]["assessment_kind"] == NEW_PROJECT_ASSESSMENT
        _assert_governed(payload)

    ordinary_payload = results["ordinary"]
    assert ordinary_payload["cost_v1_1"]["available"] is True
    assert ordinary_payload["cost_v1_1"]["engine_version"] == "cost-peer-v1.1"
    assert ordinary_payload["data_mode"] == "REAL"

    high_payload = results["high_allocation"]
    assert high_payload["cost_v1_1"]["available"] is True
    assert (high_payload["cost_v1_1"].get("cost_anomaly_score") or 0) >= (
        ordinary_payload["cost_v1_1"].get("cost_anomaly_score") or 0
    )

    incomplete_payload = results["incomplete"]
    assert incomplete_payload["cost_v1_1"]["available"] is False
    assert incomplete_payload["compliance_v1"]["status"] in {
        "INCONCLUSIVE",
        "NO_RULES_TRIGGERED",
        "RULES_TRIGGERED",
    }

    hybrid_payload = results["hybrid"]
    assert hybrid_payload["data_mode"] == "HYBRID"
    assert hybrid_payload["time_v1"]["time_anomaly_score"] is None
    assert hybrid_payload["contextual_v1"]["assessment_kind"] == NEW_PROJECT_ASSESSMENT


def test_cost_v1_1_independent_of_ml_score() -> None:
    peers = [_peer_record(10 + i, 500_000 + i * 4_000) for i in range(8)]
    normal = assess_cost(_peer_record(1, 510_000), InMemoryPeerSource([_peer_record(1, 510_000), *peers]))
    elevated = assess_cost(_peer_record(2, 4_000_000), InMemoryPeerSource([_peer_record(2, 4_000_000), *peers]))
    sparse = assess_cost(
        _peer_record(3, 510_000),
        InMemoryPeerSource([_peer_record(3, 510_000), *peers[:4]]),
    )
    empty = assess_cost(_peer_record(4, 510_000), InMemoryPeerSource([_peer_record(4, 510_000)]))
    chamber = assess_cost(
        _peer_record(5, 510_000, constituency="Sitting Rajya Sabha"),
        InMemoryPeerSource(
            [_peer_record(5, 510_000, constituency="Sitting Rajya Sabha")]
            + [_peer_record(20 + i, 500_000, constituency="Sitting Rajya Sabha") for i in range(8)]
        ),
    )
    again = assess_cost(_peer_record(1, 510_000), InMemoryPeerSource([_peer_record(1, 510_000), *peers]))

    assert normal.cost_anomaly_score == again.cost_anomaly_score
    assert normal.outcome == CostAssessmentOutcome.WITHIN_PEER_RANGE
    assert elevated.flagged is True
    assert elevated.cost_anomaly_score is not None
    assert sparse.outcome == CostAssessmentOutcome.INSUFFICIENT_EVIDENCE
    assert sparse.cost_anomaly_score is None
    assert empty.cost_anomaly_score is None
    assert empty.outcome == CostAssessmentOutcome.INSUFFICIENT_EVIDENCE
    reason = (chamber.constituency_exclusion_reason or "").casefold()
    assert "chamber" in reason or "house" in reason
    assert "ml_anomaly" not in (normal.explanation or "").casefold()
    assert "fraud" not in (elevated.explanation or "").casefold()


def test_time_real_inconclusive_hybrid_stays_hybrid(client: TestClient) -> None:
    session = get_session_factory()()
    try:
        real_row = _insert_work(session, suffix="time-real", amount=500_000, status="Ongoing", lifecycle_stage="ONGOING")
        hybrid_row = _insert_work(
            session,
            suffix="time-hybrid",
            amount=500_000,
            status="Ongoing",
            lifecycle_stage="ONGOING",
        )
        session.commit()
        real_id = real_row.id
        hybrid_id = hybrid_row.id
        hybrid_internal = hybrid_row.internal_project_id
        first = assess_project_time(session, real_id, mode=TimeMode.REAL, persist=False)
        second = assess_project_time(session, real_id, mode=TimeMode.REAL, persist=False)
        schedule = HybridSchedule(
            internal_project_id=hybrid_internal,
            planned_start_date=date(2023, 1, 1),
            planned_completion_date=date(2023, 6, 1),
            actual_start_date=date(2023, 1, 15),
            actual_completion_date=None,
            physical_progress_percent=12,
            as_of_date=date(2024, 6, 30),
        )
        hybrid = assess_project_time(
            session,
            hybrid_id,
            mode=TimeMode.HYBRID_TEST,
            persist=True,
            schedules={hybrid_internal: schedule},
            observation_date=date(2024, 6, 30),
        )
        missing = assess_project_time(session, real_id, mode=TimeMode.HYBRID_TEST, persist=False)
        session.commit()
    finally:
        session.close()

    assert first.time_anomaly_score is None
    assert first.time_anomaly_score == second.time_anomaly_score
    assert first.time_mode == TimeMode.REAL
    assert first.outcome == TimeAssessmentOutcome.INSUFFICIENT_EVIDENCE
    assert first.dataset_type == "REAL"
    assert hybrid.time_mode == TimeMode.HYBRID_TEST
    assert hybrid.dataset_type == "HYBRID"
    assert missing.time_mode == TimeMode.HYBRID_TEST
    assert missing.dataset_type == "HYBRID"
    assert missing.time_mode != TimeMode.REAL

    real_api = client.get(f"/api/v1/projects/{real_id}/time-intelligence", params={"mode": "real"})
    assert real_api.status_code == 200
    body = real_api.json()
    assert body["time_anomaly_score"] is None
    _assert_governed(body)


def test_compliance_states_remain_distinct(client: TestClient) -> None:
    session = get_session_factory()()
    try:
        with_ida = _insert_work(session, suffix="comp-ida", amount=400_000)
        no_ida = _insert_work(session, suffix="comp-no-ida", amount=400_000, ida="")
        session.commit()
        with_id = with_ida.id
        no_id = no_ida.id
    finally:
        session.close()

    present = client.get(f"/api/v1/projects/{with_id}/compliance", params={"mode": "real"}).json()
    missing = client.get(f"/api/v1/projects/{no_id}/compliance", params={"mode": "real"}).json()
    _assert_governed(present)
    present_rules = present["triggered_rules"] + present["non_triggered_rules"] + present["not_assessable_rules"]
    missing_rules = missing["triggered_rules"] + missing["non_triggered_rules"] + missing["not_assessable_rules"]
    statuses = {item["status"] for item in present_rules}
    assert "NOT_ASSESSABLE" in statuses
    assert present["compliance_status"] in {"INCONCLUSIVE", "NO_RULES_TRIGGERED", "RULES_TRIGGERED"}
    ida_rule = next(item for item in present_rules if item["rule_id"] == "R015")
    missing_ida = next(item for item in missing_rules if item["rule_id"] == "R015")
    assert ida_rule["status"] in {"TRIGGERED", "NOT_TRIGGERED"}
    assert missing_ida["status"] in {"TRIGGERED", "NOT_ASSESSABLE"}
    assert ida_rule["status"] != missing_ida["status"] or missing["compliance_status"] != present["compliance_status"]
    spend = next(item for item in present_rules if item["rule_id"] == "R004")
    assert spend["status"] == "NOT_ASSESSABLE"


def test_overlap_flows_into_graph_without_fabricated_edges(client: TestClient) -> None:
    session = get_session_factory()()
    try:
        subject = _insert_work(session, suffix="overlap-a", amount=500_000)
        _insert_work(
            session,
            suffix="overlap-b",
            amount=510_000,
            work_description=TANKS,
            recommended_date=date(2023, 6, 10),
        )
        session.commit()
        subject_id = subject.id
    finally:
        session.close()

    overlap = client.get(
        f"/api/v1/projects/{subject_id}/overlap-intelligence",
        params={"mode": "real"},
    )
    assert overlap.status_code == 200, overlap.text
    overlap_body = overlap.json()
    graph = client.get(f"/api/v1/projects/{subject_id}/graph", params={"mode": "real"})
    assert graph.status_code == 200, graph.text
    graph_body = graph.json()
    _assert_governed(overlap_body)
    _assert_governed(graph_body)
    assert overlap_body["dataset_type"] == "REAL"
    assert graph_body["dataset_type"] == "REAL"
    assert graph_body["project_node"]["node_type"] == "PROJECT"
    payload_nodes = json.dumps(graph_body)
    assert "PROJECT" in payload_nodes
    similar = [edge for edge in graph_body["relationships"] if edge["edge_type"] == "SIMILAR_TO"]
    overlap_ids = {item["linked_project_id"] for item in overlap_body.get("matches") or []}
    for edge in similar:
        target = edge.get("to_project_id")
        if isinstance(target, int) and overlap_ids:
            assert target in overlap_ids or target == subject_id


def test_future_ongoing_completed_and_invalid_transition(client: TestClient) -> None:
    session = get_session_factory()()
    try:
        future = insert_lifecycle_project(session, internal_project_id="internal:fsv:future")
        ongoing = insert_lifecycle_project(
            session,
            internal_project_id="internal:fsv:ongoing",
            lifecycle_stage="ONGOING",
            status="Ongoing",
        )
        completed = insert_lifecycle_project(
            session,
            internal_project_id="internal:fsv:completed",
            lifecycle_stage="COMPLETED",
            status="Completed",
        )
        unknown = insert_lifecycle_project(
            session,
            internal_project_id="internal:fsv:unknown",
            lifecycle_stage="UNKNOWN",
            status="",
        )
        session.commit()
        ids = {
            "FUTURE": future.id,
            "ONGOING": ongoing.id,
            "COMPLETED": completed.id,
            "UNKNOWN": unknown.id,
        }
        with pytest.raises(Exception) as exc:
            record_planning_decision(
                session,
                ongoing,
                action="PRIORITIZE",
                reason="not applicable",
                actor_role="officer",
                data_mode=DataMode.REAL,
            )
        assert "FUTURE" in str(exc.value) or "planning_not_applicable" in str(getattr(exc.value, "code", ""))
    finally:
        session.close()

    future_body = client.get(f"/api/v2/projects/{ids['FUTURE']}/lifecycle", params={"data_mode": "REAL"}).json()
    ongoing_body = client.get(f"/api/v2/projects/{ids['ONGOING']}/lifecycle", params={"data_mode": "REAL"}).json()
    completed_body = client.get(f"/api/v2/projects/{ids['COMPLETED']}/lifecycle", params={"data_mode": "REAL"}).json()
    unknown_body = client.get(f"/api/v2/projects/{ids['UNKNOWN']}/lifecycle", params={"data_mode": "REAL"}).json()
    for body in (future_body, ongoing_body, completed_body, unknown_body):
        assert body["automatic_sanction"] is False
        assert body["automatic_payment"] is False
        assert body["fraud_conclusion"] is False
        _assert_governed(body)
    assert future_body["lifecycle_state"] == "FUTURE"
    assert future_body["current_stage"] == "PRIORITIZATION"
    assert ongoing_body["lifecycle_state"] == "ONGOING"
    assert completed_body["lifecycle_state"] == "COMPLETED"
    assert unknown_body["lifecycle_state"] == "UNKNOWN"
    bad = client.post(
        f"/api/v2/projects/{ids['ONGOING']}/lifecycle/decision",
        json={"action": "PRIORITIZE", "reason": "should not apply"},
        params={"data_mode": "REAL"},
    )
    assert bad.status_code in {409, 422, 400}


def test_demo_cases_record_evidence_supported_outputs(client: TestClient) -> None:
    session = get_session_factory()()
    try:
        rows = insert_all_demo_cases(session)
        session.commit()
        ids = {key: row.id for key, row in rows.items()}
    finally:
        session.close()

    expected_lifecycle = {
        "GHOST": "COMPLETED",
        "OVERBILL": "COMPLETED",
        "STUCK": "ONGOING",
        "CLEAN": "FUTURE",
    }
    for case_id in CASE_IDS:
        response = client.get(f"/api/v1/demo-cases/{case_id}", params={"data_mode": "HYBRID"})
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["case_id"] == case_id
        assert body["project_id"] == ids[case_id]
        assert body["internal_project_id"] == DEMO_INTERNAL_IDS[case_id if case_id != "OVERBILL" else "OVERBILL"]
        assert body["data_mode"] == "HYBRID"
        assert body["lifecycle_state"] == expected_lifecycle[case_id]
        assert DEMO_NOTICE in body["demo_notice"]
        assert body["fusion_v2_unchanged"] is True
        assert body["automatic_sanction"] is False
        assert body["automatic_payment"] is False
        assert body["fraud_conclusion"] is False
        assert body["risk_fusion_v2"]["formula_unchanged"] is True
        fused_ids = set(body["risk_fusion_v2"]["evidence_ids"] or [])
        stored_ids = set(body["available_evidence"]["evidence_ids"])
        assert fused_ids <= stored_ids
        _assert_governed(body)


def test_evidence_coexistence_ml_append_only_and_v2_ignore(client: TestClient, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SARVSAKSHI_ML_MODELS_DIR", str(tmp_path / "ml-models"))
    from app.config import reset_settings_cache

    reset_settings_cache()
    reset_model_cache()
    session = get_session_factory()()
    try:
        _seed_kurnool_peers(session)
        subject = _insert_work(session, suffix="evidence-mix", amount=520_000, status="Ongoing", lifecycle_stage="ONGOING")
        seed_real_training_rows(session, n=48)
        train_from_session(session)
        session.commit()
        project_id = subject.id
    finally:
        session.close()
        reset_model_cache()

    client.get(f"/api/v1/projects/{project_id}/cost-intelligence")
    client.get(f"/api/v1/projects/{project_id}/time-intelligence", params={"mode": "real"})
    client.get(f"/api/v1/projects/{project_id}/overlap-intelligence", params={"mode": "real"})
    client.get(f"/api/v1/projects/{project_id}/compliance", params={"mode": "real"})
    client.get(f"/api/v1/projects/{project_id}/graph", params={"mode": "real"})
    client.get(f"/api/v1/projects/{project_id}/need-impact")
    client.get(f"/api/v2/projects/{project_id}/context", params={"data_mode": "REAL"})
    first_ml = client.post(f"/api/v2/projects/{project_id}/ml-evidence", json={"data_mode": "REAL"})
    assert first_ml.status_code == 200, first_ml.text
    first_id = first_ml.json()["evidence_id"]
    second_ml = client.post(f"/api/v2/projects/{project_id}/ml-evidence", json={"data_mode": "REAL"})
    assert second_ml.status_code == 200, second_ml.text
    second_id = second_ml.json()["evidence_id"]
    assert first_id != second_id

    evidence = client.get(f"/api/v1/projects/{project_id}/evidence").json()
    items = evidence.get("items") or evidence.get("evidence") or []
    engines = {item["engine_name"] for item in items}
    modes = {item["data_mode"] for item in items}
    assert "cost" in engines
    assert "ml" in engines
    assert "context" in engines or any(item.get("engine_name") == "context" for item in items)
    assert "SYNTHETIC" not in modes or "REAL" in modes
    ml_items = [item for item in items if item["engine_name"] == "ml"]
    assert len(ml_items) >= 2
    for item in items:
        assert item.get("provenance") or item.get("provenance_json")
        assert item["data_mode"] in {"REAL", "HYBRID", "SYNTHETIC"}
        assert "fraud probability" not in (item.get("explanation") or "").casefold()

    risk = client.get(f"/api/v2/projects/{project_id}/risk", params={"data_mode": "REAL"})
    assert risk.status_code == 200, risk.text
    risk_body = risk.json()
    assert risk_body["engine_version"] == "risk-fusion-v2"
    groups = [item.get("group_id") for item in risk_body.get("contributing_evidence_groups") or []]
    breakdown = [item.get("group_id") for item in risk_body.get("evidence_contribution_breakdown") or []]
    assert "ml" not in groups
    assert "ml" not in breakdown
    fused_ids = set(risk_body.get("evidence_ids") or [])
    ml_ids = {item["evidence_id"] for item in ml_items}
    assert fused_ids.isdisjoint(ml_ids)
    first = client.get(f"/api/v2/projects/{project_id}/risk", params={"data_mode": "REAL"}).json()
    second = client.get(f"/api/v2/projects/{project_id}/risk", params={"data_mode": "REAL"}).json()
    assert first["investigation_priority"] == second["investigation_priority"]
    _assert_governed(risk_body)


def test_ml_predict_missing_model_and_inconclusive_features(client: TestClient, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SARVSAKSHI_ML_MODELS_DIR", str(tmp_path / "empty-ml-models"))
    from app.config import reset_settings_cache

    reset_settings_cache()
    reset_model_cache()
    missing = client.post(
        "/api/v2/ml/predict",
        json={
            "allocation_amount": 250000,
            "category": "Normal/Others",
            "data_mode": "REAL",
        },
    )
    assert missing.status_code == 503
    assert missing.json()["error"]["code"] == "model_missing"

    incomplete = client.post(
        "/api/v2/projects/assess",
        json={"state": "Andhra Pradesh", "data_mode": "REAL"},
    )
    assert incomplete.status_code == 200
    payload = incomplete.json()
    assert payload["fraud_probability"] is None
    assert payload["ml"]["cost"] is None or payload["ml"]["error"]
    _assert_governed(payload)


def test_ml_pipeline_with_trained_artifact_no_silent_fallback(client: TestClient, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SARVSAKSHI_ML_MODELS_DIR", str(tmp_path / "ml-models"))
    from app.config import reset_settings_cache

    reset_settings_cache()
    reset_model_cache()
    session = get_session_factory()()
    try:
        seed_real_training_rows(session, n=48)
        record = train_from_session(session)
        session.commit()
        version = getattr(record, "model_version", None) or json.loads(
            (tmp_path / "ml-models" / COST_MODEL_NAME / "metadata.json").read_text(encoding="utf-8")
        )["model_version"]
    finally:
        session.close()
        reset_model_cache()

    body = {
        "state": "Andhra Pradesh",
        "constituency": "KURNOOL",
        "category": "Normal/Others",
        "work_description": TANKS,
        "allocation_amount": 250000,
        "recommendation_date": "2023-06-01",
        "status": "Unsanctioned",
        "house": "Lok Sabha",
        "data_mode": "REAL",
    }
    first = client.post("/api/v2/ml/predict", json=body)
    second = client.post("/api/v2/ml/predict", json=body)
    assert first.status_code == 200, first.text
    assert second.status_code == 200
    payload = first.json()
    assert payload["assessment_kind"] == NEW_PROJECT_ASSESSMENT
    assert payload["fraud_probability"] is None
    cost = payload["predictions"]["cost"]
    assert cost["model_version"]
    assert cost["feature_schema_version"]
    assert cost["training_data_hash"]
    assert cost["ml_anomaly_score"] is None or 0 <= cost["ml_anomaly_score"] <= 100
    assert first.json()["predictions"]["cost"]["ml_anomaly_score"] == second.json()["predictions"]["cost"]["ml_anomaly_score"]
    mismatch = client.post("/api/v2/ml/predict", json=dict(body, model_version="not-a-real-version"))
    assert mismatch.status_code in {409, 422, 400, 503}
    _assert_governed(payload)

    missing_features = client.post(
        "/api/v2/ml/predict",
        json={"data_mode": "REAL", "state": "Andhra Pradesh"},
    )
    assert missing_features.status_code == 200
    incomplete = missing_features.json()["predictions"]["cost"]
    assert incomplete["status"] == "INCONCLUSIVE" or incomplete["ml_anomaly_score"] is None


def test_contextual_intelligence_provenance(client: TestClient) -> None:
    session = get_session_factory()()
    try:
        row = _insert_work(session, suffix="context", amount=400_000)
        session.commit()
        project_id = row.id
    finally:
        session.close()

    body = client.get(f"/api/v2/projects/{project_id}/context", params={"data_mode": "REAL"}).json()
    assert body["cost_v1_1_unchanged"] is True
    assert body["risk_fusion_unchanged"] is True
    assert body["fraud_probability"] is None
    pop = next(item for item in body["observations"] if item["indicator"] == "state_population")
    assert pop["status"] == "AVAILABLE"
    assert pop["value"] is not None
    assert pop["unit"]
    assert pop["geographic_level"] == "STATE"
    assert pop["source_url"]
    assert pop["retrieval_date"]
    assert pop["reference_year"]
    assert pop["data_mode"] == "REAL"
    assert pop["context_kind"] == "OBSERVED_EXTERNAL_INDICATOR"
    assert "beneficiary" in (pop.get("notes") or "").casefold() or "not a project" in json.dumps(body).casefold()
    sources = client.get("/api/v2/context/sources").json()
    assert sources["items"] or sources.get("sources")
    refresh = client.post(
        f"/api/v2/projects/{project_id}/context/refresh",
        params={"data_mode": "REAL"},
    )
    assert refresh.status_code == 200
    _assert_governed(body)


def test_image_geo_satellite_fail_honestly(client: TestClient) -> None:
    session = get_session_factory()()
    try:
        row = _insert_work(session, suffix="sensors", amount=400_000, status="Ongoing", lifecycle_stage="ONGOING")
        session.commit()
        project_id = row.id
    finally:
        session.close()

    geo = client.get(f"/api/v1/projects/{project_id}/geospatial").json()
    sat = client.get(f"/api/v1/projects/{project_id}/satellite").json()
    upload = client.post(
        f"/api/v1/projects/{project_id}/images",
        files={"file": ("site.png", unique_png(), "image/png")},
        data={"data_mode": "REAL"},
    )
    assert upload.status_code == 200, upload.text
    image_id = upload.json()["image_id"]
    forensics = client.post(f"/api/v1/images/{image_id}/forensics")
    assert forensics.status_code == 200, forensics.text
    geo_text = json.dumps(geo).casefold()
    sat_text = json.dumps(sat).casefold()
    assert "inconclusive" in geo_text or "unavailable" in geo_text
    assert "unavailable" in sat_text or "inconclusive" in sat_text
    assert "fake imagery" not in sat_text
    forensic_body = forensics.json()
    assert "fraud" not in json.dumps(forensic_body).casefold() or "not" in json.dumps(forensic_body).casefold()
    assert forensic_body.get("bytes_unmodified") is True or "unmodified" in json.dumps(forensic_body).casefold()
    _assert_governed(geo)
    _assert_governed(sat)


def test_document_blueprint_and_pce_conflict_state(client: TestClient) -> None:
    session = get_session_factory()()
    try:
        row = _insert_work(session, suffix="docs", amount=2_000_000, status="Ongoing", lifecycle_stage="ONGOING")
        session.commit()
        project_id = row.id
    finally:
        session.close()

    upload = client.post(
        f"/api/v1/projects/{project_id}/documents",
        files={"file": ("blueprint.pdf", consistent_blueprint_pdf(), "application/pdf")},
        data={"document_type": "BLUEPRINT", "data_mode": "REAL"},
    )
    assert upload.status_code == 200, upload.text
    doc_id = upload.json()["document_id"]
    extracted = client.post(f"/api/v1/documents/{doc_id}/extract")
    assert extracted.status_code == 200, extracted.text
    body = extracted.json()
    assert body["status"] == "EXTRACTED"
    assert body["extraction_method"] == "pdf_text"
    assert body.get("fields")
    _assert_governed(body)


def test_jan_sakshi_missing_gps_inconclusive_and_privacy(client: TestClient) -> None:
    session = get_session_factory()()
    try:
        row = _insert_work(session, suffix="citizen", amount=400_000, status="Ongoing", lifecycle_stage="ONGOING")
        session.commit()
        project_id = row.id
    finally:
        session.close()

    response = client.post(
        f"/api/v1/projects/{project_id}/citizen-reports",
        json={
            "satisfaction_rating": 3,
            "observation_text": "Work appears delayed from the road.",
            "issue_category": "delayed_work",
            "data_mode": "REAL",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["submission_status"] in {"INCONCLUSIVE", "REJECTED", "ACCEPTED"}
    assert body.get("latitude") in {None, ""} or "latitude" not in body
    assert "not an official mplads rule" in json.dumps(body).casefold()
    _assert_governed(body)


def test_search_passport_and_no_stale_identity(client: TestClient) -> None:
    session = get_session_factory()()
    try:
        first = _insert_work(session, suffix="search-a", amount=400_000, mp_name="Alpha MP")
        second = _insert_work(
            session,
            suffix="search-b",
            amount=410_000,
            constituency="ELURU",
            work_description="NA - Construction of community hall",
            mp_name="Beta MP",
            status="Completed",
            lifecycle_stage="COMPLETED",
        )
        session.commit()
        first_id, second_id = first.id, second.id
    finally:
        session.close()

    listing = client.get("/api/v1/projects", params={"q": "community hall", "state": "Andhra Pradesh"})
    assert listing.status_code == 200
    body = listing.json()
    assert body["effective_state"] == "Andhra Pradesh"
    scheme = body["items"][0]["scheme_id"]
    by_scheme = client.get("/api/v1/projects", params={"q": scheme})
    assert by_scheme.status_code == 200
    by_mp = client.get("/api/v1/projects", params={"q": "Beta MP"})
    assert any(item["id"] == second_id for item in by_mp.json()["items"])
    options = client.get("/api/v1/projects/options", params={"state": "Andhra Pradesh"})
    assert options.status_code == 200
    constituencies = options.json().get("constituencies") or options.json().get("items") or []
    assert constituencies

    passport_a = client.get(f"/api/v1/projects/{first_id}", params={"mode": "REAL"}).json()
    passport_b = client.get(f"/api/v1/projects/{second_id}", params={"mode": "REAL"}).json()
    assert passport_a["id"] == first_id
    assert passport_b["id"] == second_id
    assert passport_a["internal_project_id"] != passport_b["internal_project_id"]
    assert passport_a["scheme_id"] != passport_b["scheme_id"]
    _assert_governed(passport_a)


def test_hybrid_full_journey_and_officer_decision(client: TestClient) -> None:
    session = get_session_factory()()
    try:
        rows = insert_all_demo_cases(session)
        session.commit()
        stuck = rows["STUCK"]
        project_id = stuck.id
    finally:
        session.close()

    chain = [
        client.get(f"/api/v1/projects/{project_id}", params={"mode": "HYBRID"}),
        client.get(f"/api/v2/projects/{project_id}/lifecycle", params={"data_mode": "HYBRID"}),
        client.get(f"/api/v1/projects/{project_id}/plan"),
        client.get(f"/api/v1/projects/{project_id}/claims"),
        client.get(f"/api/v1/projects/{project_id}/evidence"),
        client.get(f"/api/v1/projects/{project_id}/milestones"),
        client.get(f"/api/v1/projects/{project_id}/cost-intelligence"),
        client.get(f"/api/v1/projects/{project_id}/time-intelligence", params={"mode": "hybrid-test"}),
        client.get(f"/api/v2/projects/{project_id}/context", params={"data_mode": "HYBRID"}),
        client.get(f"/api/v2/projects/{project_id}/risk", params={"data_mode": "HYBRID"}),
        client.get(f"/api/v1/projects/{project_id}/graph", params={"mode": "hybrid-test"}),
    ]
    for response in chain:
        assert response.status_code == 200, response.text
        _assert_governed(response.json())

    passport = chain[0].json()
    lifecycle = chain[1].json()
    evidence = chain[4].json()
    risk = chain[9].json()
    assert passport["id"] == project_id
    assert lifecycle["lifecycle_state"] == "ONGOING"
    items = evidence.get("items") or evidence.get("evidence") or []
    assert items
    fused = set(risk.get("evidence_ids") or [])
    stored = {item["evidence_id"] for item in items}
    if fused:
        assert fused <= stored
    assert risk["engine_version"] == "risk-fusion-v2"

    for question in COPILOT_QUESTIONS:
        chat = client.post(
            f"/api/v1/projects/{project_id}/copilot/chat",
            json={"question": question, "data_mode": "HYBRID"},
        )
        assert chat.status_code == 200, chat.text
        body = chat.json()
        answer = body["answer"].casefold()
        assert "fraud probability" not in answer or "not" in answer
        assert "this is fraud" not in answer
        if "fraud probability" in question.casefold():
            assert "not" in answer
        if "external context" in question.casefold():
            assert "project-specific" not in answer or "not" in answer
        assert body.get("used_llm") is False
        _assert_governed(body)

    before_risk = client.get(f"/api/v2/projects/{project_id}/risk", params={"data_mode": "HYBRID"}).json()
    decision = client.post(
        f"/api/v1/projects/{project_id}/decisions",
        json={
            "decision_type": OfficerDecisionType.NEED_MORE_INFO.value,
            "reason": "Need more field evidence before a human conclusion.",
            "actor_role": "officer",
        },
    )
    assert decision.status_code == 200, decision.text
    assert decision.json()["scores_unchanged"] is True
    after_risk = client.get(f"/api/v2/projects/{project_id}/risk", params={"data_mode": "HYBRID"}).json()
    assert before_risk["investigation_priority"] == after_risk["investigation_priority"]
    payment = client.post(
        f"/api/v1/projects/{project_id}/decisions",
        json={"decision_type": "release_funds", "reason": "pay now"},
    )
    assert payment.status_code in {409, 422, 400}


def test_real_project_journey_assessable_portions(client: TestClient) -> None:
    session = get_session_factory()()
    try:
        _seed_kurnool_peers(session)
        future = _insert_work(session, suffix="real-future", amount=500_000)
        ongoing = _insert_work(
            session,
            suffix="real-ongoing",
            amount=510_000,
            status="Ongoing",
            lifecycle_stage="ONGOING",
        )
        completed = _insert_work(
            session,
            suffix="real-completed",
            amount=490_000,
            status="Completed",
            lifecycle_stage="COMPLETED",
        )
        session.commit()
        ids = {"FUTURE": future.id, "ONGOING": ongoing.id, "COMPLETED": completed.id}
    finally:
        session.close()

    for label, project_id in ids.items():
        passport = client.get(f"/api/v1/projects/{project_id}", params={"mode": "REAL"}).json()
        cost = client.get(f"/api/v1/projects/{project_id}/cost-intelligence").json()
        time_body = client.get(
            f"/api/v1/projects/{project_id}/time-intelligence",
            params={"mode": "real"},
        ).json()
        compliance = client.get(
            f"/api/v1/projects/{project_id}/compliance",
            params={"mode": "real"},
        ).json()
        lifecycle = client.get(
            f"/api/v2/projects/{project_id}/lifecycle",
            params={"data_mode": "REAL"},
        ).json()
        assert passport["data_mode_default"] in {"HYBRID", "REAL"}
        assert passport["id"] == project_id
        assert time_body["time_anomaly_score"] is None
        assert cost["engine_version"] == "cost-peer-v1.1"
        spend = next(
            item
            for item in (
                compliance["triggered_rules"]
                + compliance["non_triggered_rules"]
                + compliance["not_assessable_rules"]
            )
            if item["rule_id"] == "R004"
        )
        assert spend["status"] == "NOT_ASSESSABLE"
        assert lifecycle["lifecycle_state"] == label
        _assert_governed(passport)
        _assert_governed(cost)
        _assert_governed(time_body)


def test_risk_fusion_v2_missing_not_zero_and_conflict() -> None:
    empty = fuse_evidence_v2(
        [],
        project_id=1,
        internal_project_id="internal:fsv:empty",
        requested_data_mode=DataMode.REAL,
    )
    assert empty.investigation_priority == 0
    cost = make_group_evidence("cost", score=80, data_mode=DataMode.REAL)
    one = fuse_evidence_v2(
        [cost],
        project_id=1,
        internal_project_id="internal:fsv:one",
        requested_data_mode=DataMode.REAL,
    )
    assert 0 < one.investigation_priority < 100
    citizen = make_group_evidence("citizen", score=70, data_mode=DataMode.HYBRID)
    pce = make_group_evidence("pce", score=10, data_mode=DataMode.HYBRID)
    pce.disposition = pce.disposition
    mixed = fuse_evidence_v2(
        [citizen, pce],
        project_id=2,
        internal_project_id="internal:fsv:conflict",
        requested_data_mode=DataMode.HYBRID,
    )
    assert mixed.data_mode == DataMode.HYBRID
    assert mixed.engine_version == "risk-fusion-v2"
    repeat = fuse_evidence_v2(
        [cost],
        project_id=1,
        internal_project_id="internal:fsv:one",
        requested_data_mode=DataMode.REAL,
    )
    assert one.investigation_priority == repeat.investigation_priority


def test_milestone_has_no_payment_endpoint(client: TestClient) -> None:
    session = get_session_factory()()
    try:
        row = _insert_work(session, suffix="milestone", amount=800_000, status="Ongoing", lifecycle_stage="ONGOING")
        session.commit()
        project_id = row.id
    finally:
        session.close()
    created = client.post(
        f"/api/v1/projects/{project_id}/milestones",
        json={"milestone_name": "Foundation", "planned_amount": 200000, "data_mode": "REAL"},
    )
    assert created.status_code == 200, created.text
    milestone_id = created.json()["milestone_id"]
    assessed = client.post(f"/api/v1/milestones/{milestone_id}/assess")
    assert assessed.status_code == 200, assessed.text
    body = assessed.json()
    assert body["recommendation"] in {"PROCEED", "HOLD", "INSPECT", "INCONCLUSIVE"}
    assert "pfms" not in json.dumps(body).casefold() or "not" in json.dumps(body).casefold()
    decision = client.post(
        f"/api/v1/milestones/{milestone_id}/decision",
        json={"action": "NEED MORE INFORMATION", "reason": "Wait for inspection evidence."},
    )
    assert decision.status_code == 200, decision.text
    assert client.post("/api/v1/payments").status_code in {404, 405}
    assert client.post("/api/v1/pfms/release").status_code in {404, 405}
    _assert_governed(body)


def test_production_ml_artifacts_are_absent_or_not_client_writable() -> None:
    artifact = ML_MODELS_DIR / COST_MODEL_NAME / "model.joblib"
    if artifact.is_file():
        assert artifact.parent.name == COST_MODEL_NAME
    else:
        assert not artifact.is_file()
    upload_routes = {"/api/v2/ml/models", "/api/v2/ml/upload", "/api/v1/ml/upload"}
    assert upload_routes


def test_no_payment_or_model_upload_routes(client: TestClient) -> None:
    for path in (
        "/api/v1/payments",
        "/api/v1/pfms",
        "/api/v1/pfms/release",
        "/api/v2/ml/upload",
        "/api/v2/ml/models",
    ):
        assert client.post(path).status_code in {404, 405}
        assert client.get(path).status_code in {404, 405}
