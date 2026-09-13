"""Create stored ML Evidence Objects from existing inference.

Does not retrain models, duplicate feature engineering, or write fusion scores.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.domain.enums import DataMode
from app.domain.schemas.evidence import EvidenceObject
from app.errors import AppError
from app.evidence.adapters.ml import evidence_summary, prediction_to_evidence
from app.evidence.errors import EvidenceValidationError
from app.evidence.repository import add_evidence_object
from app.ml.constants import COST_MODEL_NAME, TIME_MODEL_NAME
from app.ml.errors import (
    MalformedMlInferenceError,
    ModelMissingError,
    ModelVersionMismatchError,
    UnsupportedDataModeError,
)
from app.ml.inference.cost import predict_cost
from app.ml.inference.time import predict_time
from app.ml.registry.store import load_record
from app.ml.types import MlPrediction, PredictionStatus
from app.models.project import Project


def _mode_token(value: str | DataMode | None) -> str:
    if isinstance(value, DataMode):
        return value.value
    return str(value or "").strip().upper().replace("-", "_")


def resolve_ml_data_mode(project: Project, requested: str | DataMode | None) -> DataMode:
    token = _mode_token(requested) or DataMode.REAL.value
    if token not in {DataMode.REAL.value, DataMode.HYBRID.value, DataMode.SYNTHETIC.value}:
        raise UnsupportedDataModeError(token)
    if project.is_synthetic:
        if token != DataMode.SYNTHETIC.value:
            raise UnsupportedDataModeError(token)
        return DataMode.SYNTHETIC
    if token == DataMode.SYNTHETIC.value:
        raise UnsupportedDataModeError(token)
    return DataMode(token)


def _project_payload(project: Project, data_mode: DataMode, model_version: str | None) -> dict[str, Any]:
    rec = project.recommended_date
    return {
        "internal_project_id": project.internal_project_id,
        "state": project.state,
        "constituency": project.constituency,
        "category": project.category,
        "work_description": project.work_description,
        "allocation_amount": project.allocation_amount,
        "recommendation_date": rec.isoformat() if rec else None,
        "status": project.status,
        "house": project.house,
        "is_synthetic": bool(project.is_synthetic),
        "data_mode": data_mode.value,
        "model_version": model_version,
    }


def _select_family(requested_version: str | None) -> str:
    cost_record = load_record(COST_MODEL_NAME)
    time_record = load_record(TIME_MODEL_NAME)
    if requested_version:
        if cost_record and requested_version == cost_record.model_version:
            return COST_MODEL_NAME
        if time_record and requested_version == time_record.model_version:
            return TIME_MODEL_NAME
        if cost_record is None and time_record is None:
            raise ModelMissingError(COST_MODEL_NAME)
        loaded = (cost_record.model_version if cost_record else None) or (
            time_record.model_version if time_record else "none"
        )
        raise ModelVersionMismatchError(requested_version, str(loaded))
    if cost_record is None:
        raise ModelMissingError(COST_MODEL_NAME)
    return COST_MODEL_NAME


def _run_inference(
    project: Project,
    data_mode: DataMode,
    requested_version: str | None,
) -> MlPrediction:
    payload = _project_payload(project, data_mode, requested_version)
    family = _select_family(requested_version)
    if family == TIME_MODEL_NAME:
        return predict_time(
            payload,
            data_mode=data_mode.value,
            requested_version=requested_version,
        )
    return predict_cost(
        payload,
        data_mode=data_mode.value,
        requested_version=requested_version,
    )


def _require_well_formed(prediction: MlPrediction) -> None:
    if not prediction.model.model_name or not str(prediction.explanation).strip():
        raise MalformedMlInferenceError(
            "ML inference did not return a model name and explanation."
        )
    if prediction.status == PredictionStatus.SCORED and prediction.ml_anomaly_score is None:
        raise MalformedMlInferenceError(
            "ML inference reported SCORED without an ml_anomaly_score."
        )


def create_project_ml_evidence(
    session: Session,
    project_id: int,
    *,
    data_mode: str | DataMode | None = DataMode.REAL.value,
    model_version: str | None = None,
) -> tuple[EvidenceObject, MlPrediction]:
    project = session.get(Project, project_id)
    if project is None:
        raise AppError("Project not found.", code="not_found", status_code=404)
    mode = resolve_ml_data_mode(project, data_mode)
    prediction = _run_inference(project, mode, model_version)
    _require_well_formed(prediction)
    obj = prediction_to_evidence(
        prediction,
        project,
        data_mode=mode,
        snapshot=getattr(project, "snapshot", None),
    )
    try:
        add_evidence_object(session, obj)
    except EvidenceValidationError as exc:
        raise AppError(str(exc), code="evidence_validation_error", status_code=422) from exc
    session.flush()
    return obj, prediction


def create_project_ml_evidence_payload(
    session: Session,
    project_id: int,
    *,
    data_mode: str | DataMode | None = DataMode.REAL.value,
    model_version: str | None = None,
) -> dict[str, Any]:
    obj, _prediction = create_project_ml_evidence(
        session,
        project_id,
        data_mode=data_mode,
        model_version=model_version,
    )
    payload = evidence_summary(obj)
    evidence = payload["evidence"]
    payload["evidence"] = evidence.model_dump(mode="json")
    return payload
