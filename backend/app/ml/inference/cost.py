"""Cost Isolation Forest inference. Cost V1.1 is not replaced."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from app.ml.constants import ANOMALY_SCORE_FLAG, CONTRIBUTION_TOP_K, GOVERNANCE_NOTE
from app.ml.features.cost import CostFeaturePipeline, rows_from_payload
from app.ml.inference.loader import cost_bundle, require_version
from app.ml.types import (
    DataMode,
    FeatureContribution,
    MlPrediction,
    ModelIdentity,
    NewProjectInput,
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


def _to_score(raw: float, sorted_train: np.ndarray) -> int:
    if sorted_train.size == 0:
        return 0
    rank = float(np.searchsorted(sorted_train, raw, side="right")) / float(sorted_train.size)
    return int(round(100.0 * min(1.0, max(0.0, rank))))


def _contributions(
    pipeline: CostFeaturePipeline,
    model,
    row,
    x: np.ndarray,
    base_raw: float,
) -> list[FeatureContribution]:
    names = pipeline.feature_names_
    if pipeline.scaler_ is None or x.shape[1] != len(names):
        return []
    medians = pipeline.scaler_.mean_
    items: list[FeatureContribution] = []
    for i, name in enumerate(names):
        if name.startswith("text_svd_"):
            continue
        perturbed = x.copy()
        perturbed[0, i] = medians[i]
        new_raw = float(-model.score_samples(perturbed)[0])
        delta = base_raw - new_raw
        value = pipeline.feature_values(row).get(name, float(x[0, i]))
        items.append(
            FeatureContribution(
                feature=name,
                value=value,
                contribution=round(delta, 6),
                note="Score change when the feature is replaced with the train mean (scaled space).",
            )
        )
    items.sort(key=lambda item: abs(item.contribution), reverse=True)
    return items[:CONTRIBUTION_TOP_K]


def _explain(score: int | None, contributions: list[FeatureContribution], availability) -> str:
    if score is None:
        missing = ", ".join(availability.missing) or "required fields"
        return (
            f"INCONCLUSIVE: the Isolation Forest cost anomaly score was not produced because {missing} "
            "are missing. This is not a fraud finding."
        )
    top = contributions[0] if contributions else None
    if score >= ANOMALY_SCORE_FLAG and top and "allocation" in top.feature:
        body = (
            "Allocation is unusual relative to the training distribution for comparable projects."
        )
    elif score >= ANOMALY_SCORE_FLAG:
        body = (
            "The unsupervised model placed this proposal in the upper tail of the training "
            "anomaly-score distribution."
        )
    else:
        body = (
            "The unsupervised model did not place this proposal in the upper tail of the "
            "training anomaly-score distribution."
        )
    extra = f" Largest measured contribution: {top.feature}." if top else ""
    unseen = ""
    if availability.unseen:
        unseen = f" Unseen categoricals were frequency-encoded as 0: {', '.join(availability.unseen)}."
    return (
        f"{body}{extra}{unseen} Isolation Forest score {score}/100 is a distributional rank, "
        "not a fraud probability. Cost Intelligence V1.1 remains the interpretable peer baseline."
    )


def _payload_dict(payload: dict[str, Any] | NewProjectInput) -> tuple[dict[str, Any], str, str | None]:
    if isinstance(payload, NewProjectInput):
        return (
            {
                "state": payload.state,
                "constituency": payload.constituency,
                "category": payload.category,
                "work_description": payload.work_description,
                "allocation_amount": payload.allocation_amount,
                "recommendation_date": payload.recommendation_date,
                "status": payload.status,
                "house": payload.house,
            },
            payload.data_mode.value,
            payload.model_version,
        )
    return dict(payload), str(payload.get("data_mode") or DataMode.REAL.value), payload.get("model_version")


def predict_cost(
    payload: dict[str, Any] | NewProjectInput,
    *,
    root: Path | None = None,
    data_mode: str | None = None,
    requested_version: str | None = None,
) -> MlPrediction:
    body, inferred_mode, inferred_version = _payload_dict(payload)
    mode = data_mode or inferred_mode
    version = requested_version or inferred_version
    bundle = cost_bundle(root)
    record = require_version(bundle, version)
    row = rows_from_payload(body)
    pipeline: CostFeaturePipeline = bundle["pipeline"]
    model = bundle["model"]
    availability = pipeline.availability(row, body)
    identity = _identity(record)
    limitations = list(record.limitations)
    if GOVERNANCE_NOTE not in limitations:
        limitations.append(GOVERNANCE_NOTE)
    if row.allocation_amount is None or row.allocation_amount <= 0 or not row.category:
        return MlPrediction(
            model=identity,
            status=PredictionStatus.INCONCLUSIVE,
            ml_anomaly_score=None,
            decision_label="INCONCLUSIVE",
            feature_availability=availability,
            feature_values=pipeline.feature_values(row),
            contributions=[],
            explanation=_explain(None, [], availability),
            limitations=limitations,
            data_mode=mode,
        )
    x = pipeline.transform([row])
    raw = float(-model.score_samples(x)[0])
    sorted_train = np.asarray(bundle.get("sorted_train_raw", []), dtype=float)
    score = _to_score(raw, sorted_train)
    iso_flag = bool(model.predict(x)[0] == -1)
    contributions = _contributions(pipeline, model, row, x, raw)
    label = "ELEVATED" if score >= ANOMALY_SCORE_FLAG or iso_flag else "WITHIN_TRAINING_DISTRIBUTION"
    return MlPrediction(
        model=identity,
        status=PredictionStatus.SCORED,
        ml_anomaly_score=score,
        decision_label=label,
        feature_availability=availability,
        feature_values=pipeline.feature_values(row),
        contributions=contributions,
        explanation=_explain(score, contributions, availability),
        limitations=limitations,
        data_mode=mode,
    )
