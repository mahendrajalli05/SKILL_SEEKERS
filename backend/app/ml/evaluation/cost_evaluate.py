"""Evaluate cost-anomaly-v1. Synthetic labels are applied AFTER scoring only."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.config import REPO_ROOT
from app.db import get_session_factory
from app.evidence.constants import HYBRID_ENRICHMENT_RELATIVE_PATH
from app.ml.constants import COST_MODEL_NAME, FORBIDDEN_MODEL_INPUT_COLUMNS
from app.ml.evaluation.diagnostics import group_medians, score_distribution
from app.ml.features.cost import CostFeaturePipeline, rows_from_payload
from app.ml.inference.cost import _to_score
from app.ml.inference.loader import cost_bundle
from app.ml.training.cost_train import load_real_cost_rows


def evaluate_cost_rows(rows, *, root: Path | None = None) -> dict:
    bundle = cost_bundle(root)
    pipeline: CostFeaturePipeline = bundle["pipeline"]
    model = bundle["model"]
    sorted_train = bundle.get("sorted_train_raw")
    usable = [row for row in rows if row.allocation_amount is not None and row.category]
    if not usable:
        return {
            "n_scored": 0,
            "score_distribution": {},
            "isolation_forest_anomaly_rate": 0.0,
            "model_name": COST_MODEL_NAME,
            "note": "Classification metrics are not reported: there is no fraud label set.",
        }
    matrix = pipeline.transform(usable)
    raw = -model.score_samples(matrix)
    flags = (model.predict(matrix) == -1).mean()
    scores = [_to_score(float(value), sorted_train) for value in raw]
    return {
        "n_scored": len(scores),
        "score_distribution": score_distribution(scores),
        "isolation_forest_anomaly_rate": float(flags),
        "model_name": COST_MODEL_NAME,
        "model_version": bundle["record"].model_version,
        "training_mode": bundle["record"].training_mode,
        "training_data_hash": bundle["record"].training_data_hash,
        "feature_schema_version": bundle["record"].feature_schema_version,
        "note": "Classification metrics are not reported: there is no fraud label set.",
    }


def evaluate_synthetic_held_out(csv_path: Path, *, root: Path | None = None) -> dict:
    """Score using REAL-trained features only; attach scenario_type after prediction."""
    frame = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    leaked = [col for col in frame.columns if col in FORBIDDEN_MODEL_INPUT_COLUMNS]
    bundle = cost_bundle(root)
    pipeline: CostFeaturePipeline = bundle["pipeline"]
    model = bundle["model"]
    sorted_train = bundle.get("sorted_train_raw")
    rows = []
    labels = []
    for rec in frame.to_dict(orient="records"):
        labels.append(rec.get("scenario_type") or "UNLABELLED")
        payload = {
            "state": rec.get("real_state"),
            "constituency": rec.get("real_constituency"),
            "category": rec.get("real_category"),
            "work_description": rec.get("real_work_description"),
            "allocation_amount": rec.get("real_allocation_amount"),
            "recommendation_date": rec.get("real_recommended_date"),
            "status": rec.get("real_status"),
            "house": rec.get("real_house"),
        }
        rows.append(rows_from_payload(payload))
    scored: dict[str, list[int]] = defaultdict(list)
    usable_idx = [
        i
        for i, row in enumerate(rows)
        if row.allocation_amount is not None and row.category
    ]
    if usable_idx:
        matrix = pipeline.transform([rows[i] for i in usable_idx])
        raw = -model.score_samples(matrix)
        for offset, i in enumerate(usable_idx):
            score = _to_score(float(raw[offset]), sorted_train)
            scored[labels[i]].append(score)
    return {
        "evaluation_kind": "SYNTHETIC_HELD_OUT",
        "csv_columns_held_out": leaked,
        "by_scenario_type": group_medians(scored),
        "note": (
            "scenario_type was attached after scoring. COST_ANOMALY labels are "
            "expenditure-versus-sanction, not allocation outliers, so Isolation Forest "
            "on allocation may not elevate them. This is not fraud-detection accuracy."
        ),
        "fraud_accuracy_claimed": False,
    }


def evaluate_from_session(session: Session, *, root: Path | None = None) -> dict:
    rows = load_real_cost_rows(session)
    return evaluate_cost_rows(rows, root=root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate cost-anomaly-v1 (unsupervised diagnostics).")
    parser.add_argument("--models-dir", type=Path, default=None)
    parser.add_argument("--synthetic-csv", type=Path, default=REPO_ROOT / HYBRID_ENRICHMENT_RELATIVE_PATH)
    parser.add_argument("--skip-synthetic", action="store_true")
    args = parser.parse_args(argv)
    session = get_session_factory()()
    try:
        real_report = evaluate_from_session(session, root=args.models_dir)
    finally:
        session.close()
    payload = {"real_unsupervised": real_report}
    if not args.skip_synthetic and args.synthetic_csv.is_file():
        payload["synthetic_held_out"] = evaluate_synthetic_held_out(
            args.synthetic_csv, root=args.models_dir
        )
    print(json.dumps(payload, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
