from __future__ import annotations

from datetime import date
from pathlib import Path

from app.db import get_session_factory
from app.ml.constants import COST_MODEL_NAME, COST_MODEL_TYPE, FEATURE_SCHEMA_COST, RANDOM_SEED
from app.ml.features.forbidden import FORBIDDEN_MODEL_INPUT_COLUMNS
from app.ml.inference.cost import predict_cost
from app.ml.inference.loader import reset_model_cache
from app.ml.registry.store import load_record
from app.ml.training.cost_train import train_cost_model, train_from_session
from app.ml.training.time_train import train_time_model
from app.ml.features.time import TimeRow
from tests.ml_fixtures import seed_real_training_rows


def test_real_training_is_deterministic(client, tmp_path: Path) -> None:
    reset_model_cache()
    session = get_session_factory()()
    try:
        seed_real_training_rows(session, n=48)
        first = train_from_session(session, root=tmp_path / "a")
        second = train_from_session(session, root=tmp_path / "b")
    finally:
        session.close()
    assert first.training_data_hash == second.training_data_hash
    assert first.model_version == second.model_version
    assert first.model_type == COST_MODEL_TYPE
    assert first.training_mode == "REAL"
    assert first.feature_schema_version == FEATURE_SCHEMA_COST
    assert first.algorithm_params["random_state"] == RANDOM_SEED
    assert (tmp_path / "a" / COST_MODEL_NAME / "model.joblib").is_file()
    record = load_record(COST_MODEL_NAME, tmp_path / "a")
    assert record is not None
    assert record.n_train >= 10
    assert "temporal" in record.split_method


def test_training_excludes_synthetic_labels(client, tmp_path: Path) -> None:
    session = get_session_factory()()
    try:
        seed_real_training_rows(session, n=40)
        rows = __import__("app.ml.training.cost_train", fromlist=["load_real_cost_rows"]).load_real_cost_rows(session)
    finally:
        session.close()
    for row in rows:
        assert set(row.__dict__).isdisjoint(FORBIDDEN_MODEL_INPUT_COLUMNS)
    train_cost_model(rows, root=tmp_path, tfidf_min_df=1, tfidf_max_features=32, svd_components=2)
    prediction = predict_cost(
        {
            "state": "Andhra Pradesh",
            "constituency": "KURNOOL",
            "category": "Normal/Others",
            "work_description": "Construction of water tanks",
            "allocation_amount": 250000,
            "recommendation_date": "2023-06-01",
        },
        root=tmp_path,
    )
    assert prediction.ml_anomaly_score is not None
    assert prediction.fraud_probability is None
    assert "scenario_type" not in prediction.feature_values


def test_hybrid_time_training_is_labelled_hybrid_test(tmp_path: Path) -> None:
    rows = []
    for i in range(24):
        rows.append(
            TimeRow(
                internal_project_id=f"t-{i}",
                planned_duration_days=80 + i,
                physical_progress_percent=20 + (i % 5),
                allocation_amount=300_000,
                recommended_date=date(2023, 1, 1 + (i % 27)),
            )
        )
    record = train_time_model(rows, root=tmp_path)
    assert record.training_mode == "HYBRID_TEST"
    assert record.model_name == "time-anomaly-v1"
    assert any("real MPLADS" in item for item in record.limitations)
