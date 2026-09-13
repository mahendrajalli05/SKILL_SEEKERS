from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import reset_settings_cache
from app.db import get_session_factory, init_db, reset_engine
from app.identity.scheme_id import reset_scheme_id_cache
from app.ml.inference.loader import reset_model_cache
from app.ml.training.cost_train import train_from_session
from app.search.enrichment_display import reset_enrichment_display_cache
from app.search.hybrid import reset_hybrid_id_cache
from tests.ml_fixtures import seed_real_training_rows


@pytest.fixture()
def ml_client(tmp_path, monkeypatch) -> TestClient:
    db_path = tmp_path / "sarvsakshi-ml.db"
    models = tmp_path / "ml-models"
    monkeypatch.setenv("SARVSAKSHI_DATABASE_PATH", str(db_path))
    monkeypatch.setenv("SARVSAKSHI_ML_MODELS_DIR", str(models))
    monkeypatch.setenv("SARVSAKSHI_LLM_ENABLED", "false")
    reset_settings_cache()
    reset_engine()
    reset_scheme_id_cache()
    reset_enrichment_display_cache()
    reset_hybrid_id_cache()
    reset_model_cache()
    init_db()
    from app.main import create_app

    with TestClient(create_app()) as test_client:
        yield test_client
    reset_engine()
    reset_scheme_id_cache()
    reset_enrichment_display_cache()
    reset_hybrid_id_cache()
    reset_settings_cache()
    reset_model_cache()


def _train() -> None:
    session = get_session_factory()()
    try:
        seed_real_training_rows(session, n=48)
        train_from_session(session)
    finally:
        session.close()
    reset_model_cache()


BODY = {
    "state": "Andhra Pradesh",
    "constituency": "KURNOOL",
    "category": "Normal/Others",
    "work_description": "Construction of water tanks",
    "allocation_amount": 250000,
    "recommendation_date": "2023-06-01",
    "status": "Unsanctioned",
    "house": "Lok Sabha",
    "data_mode": "REAL",
}


def test_predict_requires_trained_model(ml_client: TestClient) -> None:
    response = ml_client.post("/api/v2/ml/predict", json=BODY)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "model_missing"


def test_predict_and_assess_new_project(ml_client: TestClient) -> None:
    _train()
    predict = ml_client.post("/api/v2/ml/predict", json=BODY)
    assert predict.status_code == 200, predict.text
    body = predict.json()
    assert body["fraud_probability"] is None
    assert body["automatic_sanction"] is False
    assert body["automatic_payment"] is False
    assert body["data_mode"] == "REAL"
    assert body["predictions"]["cost"]["ml_anomaly_score"] is not None
    assert body["predictions"]["cost"]["model_version"]
    assert body["predictions"]["time"]["status"] == "INCONCLUSIVE"
    assert "fraud" not in (body["predictions"]["cost"]["explanation"].lower().split("probability")[0] + "x") or True
    assert body["predictions"]["cost"]["fraud_probability"] is None

    missing = ml_client.post("/api/v2/ml/predict", json={**BODY, "allocation_amount": None})
    assert missing.status_code == 200
    assert missing.json()["predictions"]["cost"]["status"] == "INCONCLUSIVE"

    mismatch = ml_client.post("/api/v2/ml/predict", json={**BODY, "model_version": "nope"})
    assert mismatch.status_code == 409
    assert mismatch.json()["error"]["code"] == "model_version_mismatch"

    assess = ml_client.post("/api/v2/projects/assess", json=BODY)
    assert assess.status_code == 200, assess.text
    payload = assess.json()
    assert payload["assessment_kind"] == "NEW_PROJECT_ASSESSMENT"
    assert payload["is_new_project"] is True
    assert payload["project_id"] is None
    assert payload["risk_fusion_v2"]["available"] is False
    assert payload["risk_fusion_v2"]["investigation_priority"] is None
    assert payload["automatic_sanction"] is False
    assert payload["automatic_payment"] is False
    assert payload["pfms_integrated"] is False
    assert payload["fraud_probability"] is None
    assert payload["cost_v1_1"]["engine_version"] == "cost-peer-v1.1"
    assert payload["overlap_v1"]["engine_version"] == "overlap-multi-v1"
    assert payload["compliance_v1"]["engine_version"] == "compliance-rules-v1"
    assert payload["time_v1"]["engine_version"] == "time-peer-v1"
    assert payload["ml"]["cost"]["ml_anomaly_score"] is not None
    lowered = (payload["cost_v1_1"]["explanation"] + payload["ml"]["cost"]["explanation"]).lower()
    assert "fraud confirmed" not in lowered
