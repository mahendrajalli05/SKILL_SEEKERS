from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.db import get_session_factory
from app.ml.evaluation.cost_evaluate import evaluate_cost_rows, evaluate_synthetic_held_out
from app.ml.inference.loader import reset_model_cache
from app.ml.training.cost_train import load_real_cost_rows, train_from_session
from tests.ml_fixtures import seed_real_training_rows


def test_unsupervised_diagnostics_have_no_classification_metrics(client, tmp_path: Path) -> None:
    reset_model_cache()
    session = get_session_factory()()
    try:
        seed_real_training_rows(session, n=48)
        train_from_session(session, root=tmp_path)
        rows = load_real_cost_rows(session)
        report = evaluate_cost_rows(rows, root=tmp_path)
    finally:
        session.close()
    assert "score_distribution" in report
    assert report.get("accuracy") is None
    assert report.get("f1") is None
    assert report.get("auc") is None
    assert "classification metrics are not reported" in report["note"].lower()


def test_synthetic_labels_applied_after_scoring(client, tmp_path: Path) -> None:
    reset_model_cache()
    session = get_session_factory()()
    try:
        seed_real_training_rows(session, n=48)
        train_from_session(session, root=tmp_path)
    finally:
        session.close()
    csv_path = tmp_path / "heldout.csv"
    pd.DataFrame(
        [
            {
                "scenario_type": "NORMAL",
                "demo_case_id": "",
                "real_state": "Andhra Pradesh",
                "real_constituency": "KURNOOL",
                "real_category": "Normal/Others",
                "real_work_description": "Construction of water tanks",
                "real_allocation_amount": "250000",
                "real_recommended_date": "2023-06-01",
                "real_status": "Unsanctioned",
                "real_house": "Lok Sabha",
            },
            {
                "scenario_type": "COST_ANOMALY",
                "demo_case_id": "",
                "real_state": "Andhra Pradesh",
                "real_constituency": "KURNOOL",
                "real_category": "Normal/Others",
                "real_work_description": "Construction of water tanks",
                "real_allocation_amount": "25000000",
                "real_recommended_date": "2023-06-01",
                "real_status": "Unsanctioned",
                "real_house": "Lok Sabha",
            },
        ]
    ).to_csv(csv_path, index=False)
    report = evaluate_synthetic_held_out(csv_path, root=tmp_path)
    assert report["evaluation_kind"] == "SYNTHETIC_HELD_OUT"
    assert report["fraud_accuracy_claimed"] is False
    assert "scenario_type" in report["csv_columns_held_out"]
    assert "NORMAL" in report["by_scenario_type"]
    assert "COST_ANOMALY" in report["by_scenario_type"]
