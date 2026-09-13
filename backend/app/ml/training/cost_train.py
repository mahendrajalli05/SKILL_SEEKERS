"""Train Isolation Forest cost-anomaly-v1 on REAL MPLADS allocation fields.

Does not train on synthetic scenario labels. Does not replace Cost V1.1.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_session_factory
from app.ml.constants import (
    COST_MODEL_NAME,
    COST_MODEL_TYPE,
    DEFAULT_CONTAMINATION,
    DEFAULT_N_ESTIMATORS,
    FEATURE_SCHEMA_COST,
    GOVERNANCE_NOTE,
    RANDOM_SEED,
)
from app.ml.features.cost import CostFeaturePipeline
from app.ml.features.forbidden import assert_no_label_leakage
from app.ml.types import CostRow
from app.ml.inference.loader import reset_model_cache
from app.ml.registry.store import artifact_path, model_dir, models_root, save_record
from app.ml.training.split import temporal_split
from app.ml.types import RegistryRecord
from app.models.project import Project


def fingerprint(train_ids: Sequence[str], *, extra: str = "") -> str:
    payload = json.dumps({"ids": list(train_ids), "extra": extra}, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_real_cost_rows(session: Session) -> list[CostRow]:
    stmt = select(Project).where(Project.is_synthetic == False)  # noqa: E712
    rows = session.scalars(stmt).all()
    out: list[CostRow] = []
    for row in rows:
        out.append(
            CostRow(
                internal_project_id=row.internal_project_id,
                allocation_amount=row.allocation_amount,
                category=(row.category or "").strip(),
                state=(row.state or "").strip(),
                constituency=(row.constituency or "").strip(),
                work_description=(row.work_description or "").strip(),
                recommended_date=row.recommended_date,
                status=(row.status or "").strip(),
                house=(row.house or "").strip(),
                is_synthetic=bool(row.is_synthetic),
            )
        )
    return out


def _score_distribution(raw: np.ndarray) -> dict[str, float]:
    if raw.size == 0:
        return {}
    return {
        "min": float(np.min(raw)),
        "p25": float(np.percentile(raw, 25)),
        "median": float(np.percentile(raw, 50)),
        "p75": float(np.percentile(raw, 75)),
        "p95": float(np.percentile(raw, 95)),
        "max": float(np.max(raw)),
        "mean": float(np.mean(raw)),
        "std": float(np.std(raw)),
    }


def train_cost_model(
    rows: Sequence[CostRow],
    *,
    root: Path | None = None,
    contamination: float = DEFAULT_CONTAMINATION,
    n_estimators: int = DEFAULT_N_ESTIMATORS,
    tfidf_max_features: int | None = None,
    tfidf_min_df: int | None = None,
    svd_components: int | None = None,
) -> RegistryRecord:
    """Fit IsolationForest on REAL observed fields. Labels are never inputs."""
    for row in rows:
        assert_no_label_leakage(row.__dict__)
    usable = [
        row
        for row in rows
        if row.allocation_amount is not None and row.allocation_amount > 0 and row.category
    ]
    if len(usable) < 10:
        raise ValueError("Need at least 10 REAL rows with allocation and category to train.")
    split = temporal_split(usable)
    by_id = {row.internal_project_id: row for row in usable}
    train_rows = [by_id[item] for item in split.train_ids]
    val_rows = [by_id[item] for item in split.validation_ids]
    test_rows = [by_id[item] for item in split.test_ids]

    pipeline_kwargs: dict = {}
    if tfidf_max_features is not None:
        pipeline_kwargs["tfidf_max_features"] = tfidf_max_features
    if tfidf_min_df is not None:
        pipeline_kwargs["tfidf_min_df"] = tfidf_min_df
    if svd_components is not None:
        pipeline_kwargs["svd_components"] = svd_components
    pipeline = CostFeaturePipeline(**pipeline_kwargs)
    pipeline.fit(train_rows)
    x_train = pipeline.transform(train_rows)
    model = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=RANDOM_SEED,
        n_jobs=1,
        max_samples=min(256, len(train_rows)),
    )
    model.fit(x_train)
    train_raw = -model.score_samples(x_train)
    val_raw = -model.score_samples(pipeline.transform(val_rows)) if val_rows else np.array([])
    test_raw = -model.score_samples(pipeline.transform(test_rows)) if test_rows else np.array([])
    sorted_train = np.sort(train_raw)
    train_flags = (model.predict(x_train) == -1).mean()
    val_flags = float((model.predict(pipeline.transform(val_rows)) == -1).mean()) if val_rows else 0.0
    test_flags = float((model.predict(pipeline.transform(test_rows)) == -1).mean()) if test_rows else 0.0

    created = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    data_hash = fingerprint(
        split.train_ids,
        extra=f"{FEATURE_SCHEMA_COST}|{COST_MODEL_TYPE}|{RANDOM_SEED}|{contamination}",
    )
    record = RegistryRecord(
        model_name=COST_MODEL_NAME,
        model_version=f"{COST_MODEL_NAME}-{data_hash[:12]}",
        model_type=COST_MODEL_TYPE,
        training_mode="REAL",
        training_data_hash=data_hash,
        feature_schema_version=FEATURE_SCHEMA_COST,
        created_at=created,
        n_train=split.train_count,
        n_validation=split.validation_count,
        n_test=split.test_count,
        split_method=split.method,
        algorithm_params={
            "n_estimators": n_estimators,
            "contamination": contamination,
            "random_state": RANDOM_SEED,
            "n_jobs": 1,
        },
        validation_metrics={
            "train_score_distribution": _score_distribution(train_raw),
            "validation_score_distribution": _score_distribution(val_raw),
            "test_score_distribution": _score_distribution(test_raw),
            "train_anomaly_rate": float(train_flags),
            "validation_anomaly_rate": val_flags,
            "test_anomaly_rate": test_flags,
            "n_features": int(x_train.shape[1]),
            "feature_names": list(pipeline.feature_names_),
        },
        limitations=[
            GOVERNANCE_NOTE,
            "No authoritative fraud/not-fraud labels were used.",
            "Classification metrics such as precision, recall, F1, and ROC-AUC are not reported.",
            "Cost Intelligence V1.1 remains the authoritative peer baseline.",
        ],
    )
    dest_root = models_root(root)
    dest_root.mkdir(parents=True, exist_ok=True)
    model_dir(COST_MODEL_NAME, dest_root).mkdir(parents=True, exist_ok=True)
    bundle = {
        "model": model,
        "pipeline": pipeline,
        "sorted_train_raw": sorted_train,
        "record": record,
        "split": {
            "train_ids": list(split.train_ids),
            "validation_ids": list(split.validation_ids),
            "test_ids": list(split.test_ids),
            "method": split.method,
        },
    }
    joblib.dump(bundle, artifact_path(COST_MODEL_NAME, dest_root))
    save_record(record, dest_root)
    reset_model_cache()
    return record


def train_from_session(session: Session, *, root: Path | None = None) -> RegistryRecord:
    rows = load_real_cost_rows(session)
    return train_cost_model(rows, root=root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Train REAL IsolationForest cost-anomaly-v1.")
    parser.add_argument("--models-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    settings = get_settings()
    session = get_session_factory()()
    try:
        record = train_from_session(session, root=args.models_dir)
    finally:
        session.close()
    print(
        json.dumps(
            {
                "model_name": record.model_name,
                "model_version": record.model_version,
                "training_mode": record.training_mode,
                "training_data_hash": record.training_data_hash,
                "n_train": record.n_train,
                "n_validation": record.n_validation,
                "n_test": record.n_test,
                "database": str(settings.sqlite_path),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
