from __future__ import annotations

from pathlib import Path

from app.engines.compliance.constants import ENGINE_VERSION as COMPLIANCE_VERSION
from app.engines.cost.constants import ENGINE_VERSION as COST_VERSION
from app.engines.fusion.constants import ENGINE_VERSION as FUSION_V1_VERSION
from app.engines.fusion.constants import INTEGRATED_WEIGHTS
from app.engines.fusion_v2.constants import ENGINE_VERSION as FUSION_V2_VERSION
from app.engines.fusion_v2.constants import GROUP_WEIGHTS
from app.engines.need.constants import (
    ENGINE_VERSION as NEED_VERSION,
    IMPACT_COMPONENT_WEIGHTS,
    NEED_COMPONENT_WEIGHTS,
    PRIORITY_WEIGHTS,
)
from app.engines.overlap.constants import ENGINE_VERSION as OVERLAP_VERSION
from app.engines.time.constants import ENGINE_VERSION as TIME_VERSION


def test_frozen_versions_and_weights_unchanged() -> None:
    assert COST_VERSION == "cost-peer-v1.1"
    assert TIME_VERSION == "time-peer-v1"
    assert OVERLAP_VERSION == "overlap-multi-v1"
    assert COMPLIANCE_VERSION == "compliance-rules-v1"
    assert FUSION_V1_VERSION == "risk-fusion-v1.1"
    assert FUSION_V2_VERSION == "risk-fusion-v2"
    assert NEED_VERSION == "need-impact-v1"
    assert INTEGRATED_WEIGHTS == {
        "cost": 0.25,
        "schedule": 0.15,
        "overlap": 0.15,
        "compliance": 0.15,
    }
    assert NEED_COMPONENT_WEIGHTS == {
        "population": 0.30,
        "infrastructure_gap": 0.25,
        "underserved_area": 0.20,
        "disaster_context": 0.25,
    }
    assert IMPACT_COMPONENT_WEIGHTS["beneficiary_count"] == 0.30
    assert PRIORITY_WEIGHTS["need"] == 0.45
    assert round(sum(GROUP_WEIGHTS.values()), 4) == 1.0
    assert GROUP_WEIGHTS["need"] == 0.00


def test_context_engine_does_not_import_cost_scoring() -> None:
    root = Path(__file__).resolve().parents[1] / "app" / "engines" / "context"
    text = ""
    for path in root.rglob("*.py"):
        text += path.read_text(encoding="utf-8")
    assert "cost_anomaly_score" not in text
    assert "NEED_COMPONENT_WEIGHTS" not in text
    assert "GROUP_WEIGHTS" not in text
    assert "IsolationForest" not in text


def test_cost_and_risk_scores_unchanged_when_context_persisted(client) -> None:
    from app.db import get_session_factory
    from tests.need_test_support import insert_project

    session = get_session_factory()()
    try:
        row = insert_project(session, internal_project_id="internal:context:score-freeze")
        session.commit()
        pid = row.id
    finally:
        session.close()

    cost_before = client.get(f"/api/v1/projects/{pid}/cost-intelligence").json()
    risk_before = client.get(f"/api/v1/projects/{pid}/risk", params={"data_mode": "REAL"}).json()
    risk_v2_before = client.get(f"/api/v2/projects/{pid}/risk", params={"data_mode": "REAL"}).json()
    client.get(f"/api/v2/projects/{pid}/context", params={"data_mode": "REAL"})
    cost_after = client.get(f"/api/v1/projects/{pid}/cost-intelligence").json()
    risk_after = client.get(f"/api/v1/projects/{pid}/risk", params={"data_mode": "REAL"}).json()
    risk_v2_after = client.get(f"/api/v2/projects/{pid}/risk", params={"data_mode": "REAL"}).json()
    assert cost_before["cost_anomaly_score"] == cost_after["cost_anomaly_score"]
    assert cost_before["engine_version"] == "cost-peer-v1.1"
    assert risk_before["investigation_priority"] == risk_after["investigation_priority"]
    assert risk_v2_before["investigation_priority"] == risk_v2_after["investigation_priority"]
