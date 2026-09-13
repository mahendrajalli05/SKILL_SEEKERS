"""New-project ML prediction orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.ml.constants import COMPLIANCE_NOTE, GOVERNANCE_NOTE, OVERLAP_NOTE, RISK_NOTE, TIME_LIMITATION
from app.ml.inference.cost import predict_cost
from app.ml.inference.time import predict_time
from app.ml.types import DataMode, MlPrediction, NewProjectInput


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return float(value)
    if hasattr(value, "item"):
        try:
            return _json_safe(value.item())
        except Exception:  # noqa: BLE001
            return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return str(value)


def predict_new_project(
    payload: dict[str, Any] | NewProjectInput,
    *,
    root: Path | None = None,
    data_mode: str = DataMode.REAL.value,
    requested_version: str | None = None,
) -> dict[str, Any]:
    if isinstance(payload, NewProjectInput):
        data_mode = payload.data_mode.value
        requested_version = requested_version or payload.model_version
        body = {
            "state": payload.state,
            "constituency": payload.constituency,
            "category": payload.category,
            "work_description": payload.work_description,
            "allocation_amount": payload.allocation_amount,
            "recommendation_date": payload.recommendation_date,
            "status": payload.status,
            "house": payload.house,
            "planned_start_date": payload.planned_start_date,
            "planned_completion_date": payload.planned_completion_date,
            "physical_progress_percent": payload.physical_progress_percent,
        }
    else:
        body = dict(payload)
        data_mode = str(body.get("data_mode") or data_mode)
        requested_version = requested_version or body.get("model_version")
    cost = predict_cost(body, root=root, data_mode=data_mode, requested_version=requested_version)
    time = predict_time(body, root=root, data_mode=data_mode, requested_version=None)
    return {
        "cost": cost,
        "time": time,
        "data_mode": data_mode,
        "notes": [GOVERNANCE_NOTE, OVERLAP_NOTE, COMPLIANCE_NOTE, RISK_NOTE, TIME_LIMITATION],
    }


def prediction_to_dict(item: MlPrediction) -> dict[str, Any]:
    return {
        "model_name": item.model.model_name,
        "model_version": item.model.model_version or None,
        "model_type": item.model.model_type,
        "training_mode": item.model.training_mode,
        "training_data_hash": item.model.training_data_hash or None,
        "feature_schema_version": item.model.feature_schema_version or None,
        "created_at": item.model.created_at or None,
        "status": item.status.value,
        "ml_anomaly_score": item.ml_anomaly_score,
        "decision_label": item.decision_label,
        "feature_availability": {
            "available": item.feature_availability.available,
            "missing": item.feature_availability.missing,
            "unseen": item.feature_availability.unseen,
            "unsupported": item.feature_availability.unsupported,
            "coverage": item.feature_availability.coverage,
        },
        "feature_values": _json_safe(item.feature_values),
        "contributions": [
            {
                "feature": row.feature,
                "value": _json_safe(row.value),
                "contribution": float(row.contribution),
                "note": row.note,
            }
            for row in item.contributions
        ],
        "explanation": item.explanation,
        "limitations": item.limitations,
        "data_mode": item.data_mode,
        "fraud_probability": None,
    }
