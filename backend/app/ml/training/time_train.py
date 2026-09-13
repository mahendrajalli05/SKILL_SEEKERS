"""HYBRID_TEST time Isolation Forest. Does not claim real MPLADS delay rates."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from app.config import REPO_ROOT
from app.evidence.constants import HYBRID_ENRICHMENT_RELATIVE_PATH
from app.ml.constants import (
    DEFAULT_CONTAMINATION,
    DEFAULT_N_ESTIMATORS,
    FEATURE_SCHEMA_TIME,
    RANDOM_SEED,
    TIME_LIMITATION,
    TIME_MODEL_NAME,
    TIME_MODEL_TYPE,
)
from app.ml.features.forbidden import assert_no_label_leakage
from app.ml.features.time import TimeFeaturePipeline, TimeRow
from app.ml.inference.loader import reset_model_cache
from app.ml.registry.store import artifact_path, model_dir, models_root, save_record
from app.ml.training.cost_train import fingerprint
from app.ml.training.split import temporal_split
from app.ml.types import CostRow, RegistryRecord


def _parse_date(value: object) -> date | None:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    text = str(value).strip()
    if not text:
        return None
    return date.fromisoformat(text[:10])


def load_hybrid_time_rows(csv_path: Path) -> list[TimeRow]:
    frame = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    rows: list[TimeRow] = []
    for rec in frame.to_dict(orient="records"):
        payload = dict(rec)
        # Labels exist on the CSV but are never copied onto TimeRow.
        for forbidden in (
            "scenario_type",
            "demo_case_id",
            "mixed_signals",
            "anomaly_notes",
            "overlap_group_id",
            "coordinate_source",
        ):
            payload.pop(forbidden, None)
        assert_no_label_leakage(
            {
                "planned_start_date": payload.get("planned_start_date"),
                "planned_completion_date": payload.get("planned_completion_date"),
                "physical_progress_percent": payload.get("physical_progress_percent"),
                "real_allocation_amount": payload.get("real_allocation_amount"),
            }
        )
        start = _parse_date(payload.get("planned_start_date"))
        end = _parse_date(payload.get("planned_completion_date"))
        duration = None
        if start is not None and end is not None:
            duration = float((end - start).days)
        amount_raw = payload.get("real_allocation_amount") or payload.get("allocation_amount")
        amount = int(float(amount_raw)) if str(amount_raw).strip() else None
        progress_raw = payload.get("physical_progress_percent")
        progress = float(progress_raw) if str(progress_raw).strip() else None
        rec_date = _parse_date(payload.get("real_recommended_date"))
        rows.append(
            TimeRow(
                internal_project_id=str(payload.get("internal_project_id") or ""),
                planned_duration_days=duration,
                physical_progress_percent=progress,
                allocation_amount=amount,
                recommended_date=rec_date,
            )
        )
    return rows


def train_time_model(
    rows: list[TimeRow],
    *,
    root: Path | None = None,
    contamination: float = DEFAULT_CONTAMINATION,
    n_estimators: int = DEFAULT_N_ESTIMATORS,
) -> RegistryRecord:
    usable = [row for row in rows if row.planned_duration_days and row.planned_duration_days > 0]
    if len(usable) < 10:
        raise ValueError("HYBRID_TEST time training needs at least 10 rows with planned duration.")
    proxy = [
        CostRow(
            internal_project_id=row.internal_project_id,
            allocation_amount=row.allocation_amount,
            category="HYBRID_TEST",
            state="",
            constituency="",
            work_description="",
            recommended_date=row.recommended_date,
            status="",
            house="",
        )
        for row in usable
    ]
    split = temporal_split(proxy)
    by_id = {row.internal_project_id: row for row in usable}
    train_rows = [by_id[item] for item in split.train_ids]
    val_rows = [by_id[item] for item in split.validation_ids]
    pipeline = TimeFeaturePipeline()
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
    created = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    data_hash = fingerprint(
        split.train_ids,
        extra=f"{FEATURE_SCHEMA_TIME}|HYBRID_TEST|{RANDOM_SEED}",
    )
    record = RegistryRecord(
        model_name=TIME_MODEL_NAME,
        model_version=f"{TIME_MODEL_NAME}-{data_hash[:12]}",
        model_type=TIME_MODEL_TYPE,
        training_mode="HYBRID_TEST",
        training_data_hash=data_hash,
        feature_schema_version=FEATURE_SCHEMA_TIME,
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
            "train_anomaly_rate": float((model.predict(x_train) == -1).mean()),
            "validation_anomaly_rate": (
                float((model.predict(pipeline.transform(val_rows)) == -1).mean()) if val_rows else 0.0
            ),
            "n_features": int(x_train.shape[1]),
        },
        limitations=[
            TIME_LIMITATION,
            "TRAINING_DATA_MODE = HYBRID_TEST.",
            "Synthetic planned dates are not official MPLADS execution history.",
        ],
    )
    dest = models_root(root)
    dest.mkdir(parents=True, exist_ok=True)
    model_dir(TIME_MODEL_NAME, dest).mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {"model": model, "pipeline": pipeline, "record": record},
        artifact_path(TIME_MODEL_NAME, dest),
    )
    save_record(record, dest)
    reset_model_cache()
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Train HYBRID_TEST time IsolationForest.")
    parser.add_argument("--models-dir", type=Path, default=None)
    parser.add_argument(
        "--csv",
        type=Path,
        default=REPO_ROOT / HYBRID_ENRICHMENT_RELATIVE_PATH,
    )
    args = parser.parse_args(argv)
    rows = load_hybrid_time_rows(args.csv)
    record = train_time_model(rows, root=args.models_dir)
    print(
        json.dumps(
            {
                "model_name": record.model_name,
                "model_version": record.model_version,
                "training_mode": record.training_mode,
                "training_data_hash": record.training_data_hash,
                "limitation": TIME_LIMITATION,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
