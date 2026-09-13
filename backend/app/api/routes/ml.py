from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain.schemas.ml import (
    FeatureAvailabilityRead,
    MlEvidenceCreateRequest,
    MlEvidenceCreateResponse,
    MlPredictRequest,
    MlPredictResponse,
    MlSignalRead,
    ProjectAssessRequest,
    ProjectAssessResponse,
)
from app.ml.assess import assess_new_project
from app.ml.constants import NEW_PROJECT_ASSESSMENT, NEW_PROJECT_EVIDENCE_NOTE
from app.ml.evidence import create_project_ml_evidence_payload
from app.ml.inference.service import predict_new_project, prediction_to_dict

router = APIRouter()


def _signal(payload: dict | None) -> MlSignalRead | None:
    if not payload:
        return None
    return MlSignalRead(
        model_name=payload["model_name"],
        model_version=payload.get("model_version"),
        model_type=payload["model_type"],
        training_mode=payload["training_mode"],
        training_data_hash=payload.get("training_data_hash"),
        feature_schema_version=payload.get("feature_schema_version"),
        created_at=payload.get("created_at"),
        status=payload["status"],
        ml_anomaly_score=payload.get("ml_anomaly_score"),
        decision_label=payload.get("decision_label"),
        feature_availability=FeatureAvailabilityRead(**payload["feature_availability"]),
        feature_values=payload.get("feature_values") or {},
        contributions=payload.get("contributions") or [],
        explanation=payload["explanation"],
        limitations=payload.get("limitations") or [],
        data_mode=payload["data_mode"],
        fraud_probability=None,
    )


@router.post("/ml/predict", response_model=MlPredictResponse)
def post_ml_predict(body: MlPredictRequest) -> MlPredictResponse:
    """Unsupervised ML signals for a proposed work. Not a fraud probability."""
    result = predict_new_project(body.model_dump(), data_mode=body.data_mode)
    cost = prediction_to_dict(result["cost"])
    time = prediction_to_dict(result["time"])
    signals = []
    if cost.get("decision_label") == "ELEVATED":
        signals.append("ml_cost_anomaly")
    if time.get("decision_label") == "ELEVATED":
        signals.append("ml_time_anomaly_hybrid_test")
    cost_read = _signal(cost)
    return MlPredictResponse(
        data_mode=body.data_mode,
        model_versions={
            "cost-anomaly-v1": cost.get("model_version"),
            "time-anomaly-v1": time.get("model_version"),
        },
        predictions={"cost": cost_read, "time": _signal(time)},
        anomaly_signals=signals,
        explanation=cost.get("explanation") or "",
        limitations=list(result["notes"]) + [NEW_PROJECT_EVIDENCE_NOTE],
        feature_availability=cost_read.feature_availability if cost_read else None,
        fraud_probability=None,
        automatic_sanction=False,
        automatic_payment=False,
        assessment_kind=NEW_PROJECT_ASSESSMENT,
        evidence_kind=NEW_PROJECT_ASSESSMENT,
        persisted=False,
    )


@router.post("/projects/assess", response_model=ProjectAssessResponse)
def post_project_assess(
    body: ProjectAssessRequest,
    db: Session = Depends(get_db),
) -> ProjectAssessResponse:
    """New-project assessment using existing engines plus ML. Does not persist."""
    payload = assess_new_project(db, body.model_dump())
    return ProjectAssessResponse(**payload)


@router.post(
    "/projects/{project_id}/ml-evidence",
    response_model=MlEvidenceCreateResponse,
)
def post_project_ml_evidence(
    project_id: int,
    body: MlEvidenceCreateRequest | None = None,
    db: Session = Depends(get_db),
) -> MlEvidenceCreateResponse:
    """Persist an ML Evidence Object for an existing project. Not a legal finding."""
    request = body or MlEvidenceCreateRequest()
    payload = create_project_ml_evidence_payload(
        db,
        project_id,
        data_mode=request.data_mode,
        model_version=request.model_version,
    )
    db.commit()
    return MlEvidenceCreateResponse(**payload)
