from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from app.db import get_session_factory
from app.ml.errors import ModelMissingError, ModelVersionMismatchError
from app.ml.inference.cost import predict_cost
from app.ml.inference.loader import reset_model_cache
from app.ml.inference.time import predict_time
from app.ml.training.cost_train import train_from_session
from app.ml.types import PredictionStatus
from tests.ml_fixtures import seed_real_training_rows


@pytest.fixture()
def trained_root(client, tmp_path: Path) -> Path:
    reset_model_cache()
    session = get_session_factory()()
    try:
        seed_real_training_rows(session, n=48)
        train_from_session(session, root=tmp_path)
    finally:
        session.close()
    reset_model_cache()
    return tmp_path


def _base(**overrides):
    body = {
        "state": "Andhra Pradesh",
        "constituency": "KURNOOL",
        "category": "Normal/Others",
        "work_description": "Construction of water tanks",
        "allocation_amount": 250000,
        "recommendation_date": date(2023, 6, 1),
        "status": "Unsanctioned",
        "house": "Lok Sabha",
    }
    body.update(overrides)
    return body


def test_valid_new_project_is_deterministic(trained_root: Path) -> None:
    first = predict_cost(_base(), root=trained_root, data_mode="REAL")
    second = predict_cost(_base(), root=trained_root, data_mode="REAL")
    assert first.status == PredictionStatus.SCORED
    assert first.ml_anomaly_score == second.ml_anomaly_score
    assert first.model.training_mode == "REAL"
    assert first.model.model_version
    assert first.model.training_data_hash
    assert first.fraud_probability is None
    assert "fraud probability" in first.explanation.lower() or "not a fraud" in first.explanation.lower()


def test_missing_amount_and_category_are_inconclusive(trained_root: Path) -> None:
    missing_amount = predict_cost(_base(allocation_amount=None), root=trained_root)
    assert missing_amount.status == PredictionStatus.INCONCLUSIVE
    missing_category = predict_cost(_base(category=""), root=trained_root)
    assert missing_category.status == PredictionStatus.INCONCLUSIVE


def test_unseen_category_still_scores(trained_root: Path) -> None:
    result = predict_cost(_base(category="Unseen Prototype Category"), root=trained_root)
    assert result.status == PredictionStatus.SCORED
    assert "category" in result.feature_availability.unseen


def test_missing_model_errors(tmp_path: Path) -> None:
    with pytest.raises(ModelMissingError):
        predict_cost(_base(), root=tmp_path / "empty")


def test_model_version_mismatch(trained_root: Path) -> None:
    with pytest.raises(ModelVersionMismatchError):
        predict_cost(_base(), root=trained_root, requested_version="not-this-version")


def test_real_time_ml_is_inconclusive_without_fallback(trained_root: Path) -> None:
    result = predict_time(_base(), root=trained_root, data_mode="REAL")
    assert result.status == PredictionStatus.INCONCLUSIVE
    assert result.ml_anomaly_score is None
    assert "silent fallback" in result.explanation.lower() or "not used" in result.explanation.lower()
