"""HYBRID_TEST time ML inference. REAL always returns INCONCLUSIVE."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from app.ml.constants import ANOMALY_SCORE_FLAG, TIME_LIMITATION
from app.ml.errors import ModelMissingError
from app.ml.features.time import TimeFeaturePipeline, time_row_from_payload
from app.ml.inference.loader import require_version, time_bundle
from app.ml.types import (
    FeatureAvailability,
    MlPrediction,
    ModelIdentity,
    PredictionStatus,
)


def _identity(record) -> ModelIdentity:
    return ModelIdentity(
        model_name=record.model_name,
        model_version=record.model_version,
        model_type=record.model_type,
        training_mode=record.training_mode,
        training_data_hash=record.training_data_hash,
        feature_schema_version=record.feature_schema_version,
        created_at=record.created_at,
    )


def predict_time(
    payload: dict[str, Any],
    *,
    root: Path | None = None,
    data_mode: str = "REAL",
    requested_version: str | None = None,
) -> MlPrediction:
    if data_mode == "REAL":
        return MlPrediction(
            model=ModelIdentity(
                model_name="time-anomaly-v1",
                model_version="",
                model_type="IsolationForest",
                training_mode="HYBRID_TEST",
                training_data_hash="",
                feature_schema_version="",
                created_at="",
            ),
            status=PredictionStatus.INCONCLUSIVE,
            ml_anomaly_score=None,
            decision_label="INCONCLUSIVE",
            feature_availability=FeatureAvailability(
                missing=["execution_start_date", "execution_completion_date"],
                coverage=0.0,
            ),
            feature_values={},
            contributions=[],
            explanation=(
                "INCONCLUSIVE: REAL MPLADS records have no verified execution start or completion "
                "dates. The HYBRID_TEST time model is not used as a silent fallback."
            ),
            limitations=[TIME_LIMITATION],
            data_mode=data_mode,
        )
    try:
        bundle = time_bundle(root)
    except ModelMissingError:
        return MlPrediction(
            model=ModelIdentity(
                model_name="time-anomaly-v1",
                model_version="",
                model_type="IsolationForest",
                training_mode="HYBRID_TEST",
                training_data_hash="",
                feature_schema_version="",
                created_at="",
            ),
            status=PredictionStatus.NOT_AVAILABLE,
            ml_anomaly_score=None,
            decision_label="INCONCLUSIVE",
            feature_availability=FeatureAvailability(missing=["model"], coverage=0.0),
            feature_values={},
            contributions=[],
            explanation=(
                "INCONCLUSIVE: time-anomaly-v1 (HYBRID_TEST) is not loaded. "
                + TIME_LIMITATION
            ),
            limitations=[TIME_LIMITATION],
            data_mode=data_mode,
        )
    record = require_version(bundle, requested_version)
    row = time_row_from_payload(payload)
    pipeline: TimeFeaturePipeline = bundle["pipeline"]
    model = bundle["model"]
    identity = _identity(record)
    if row.planned_duration_days is None or row.planned_duration_days <= 0:
        return MlPrediction(
            model=identity,
            status=PredictionStatus.INCONCLUSIVE,
            ml_anomaly_score=None,
            decision_label="INCONCLUSIVE",
            feature_availability=FeatureAvailability(
                missing=["planned_duration_days"],
                coverage=0.0,
            ),
            feature_values={},
            contributions=[],
            explanation=(
                "INCONCLUSIVE: HYBRID_TEST time scoring needs a planned duration. "
                + TIME_LIMITATION
            ),
            limitations=[TIME_LIMITATION],
            data_mode=data_mode,
        )
    x = pipeline.transform([row])
    raw = float(-model.score_samples(x)[0])
    flags = bool(model.predict(x)[0] == -1)
    # Rank against a simple logistic squash of raw score; HYBRID_TEST only.
    score = int(round(100.0 / (1.0 + np.exp(-2.0 * (raw - 0.5)))))
    score = min(100, max(0, score))
    label = "ELEVATED" if flags or score >= ANOMALY_SCORE_FLAG else "WITHIN_TRAINING_DISTRIBUTION"
    return MlPrediction(
        model=identity,
        status=PredictionStatus.SCORED,
        ml_anomaly_score=score,
        decision_label=label,
        feature_availability=FeatureAvailability(
            available=["planned_duration_days", "physical_progress_percent", "allocation_amount"],
            coverage=0.75,
        ),
        feature_values={
            "planned_duration_days": row.planned_duration_days,
            "physical_progress_percent": row.physical_progress_percent,
            "allocation_amount": row.allocation_amount,
        },
        contributions=[],
        explanation=(
            f"HYBRID_TEST Isolation Forest time score {score}/100. "
            "This used synthetic planned dates. It is not a real MPLADS delay rate. "
            "Not a fraud probability."
        ),
        limitations=[TIME_LIMITATION],
        data_mode=data_mode,
    )
