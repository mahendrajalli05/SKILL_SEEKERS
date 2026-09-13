"""ML Training & Inference V1 → canonical Evidence Object.

Reuses Evidence Object V1 fields. Does not change Isolation Forest scoring,
Cost V1.1, or Risk Fusion. Stored text is a distributional anomaly signal only.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from uuid import uuid4

from app.domain.enums import (
    DataMode,
    EvidenceDisposition,
    EvidenceEngine,
    EvidenceFactKind,
    EvidenceSeverity,
    SignalType,
    SourceType,
)
from app.domain.schemas.evidence import EvidenceObject
from app.evidence.constants import DISPOSITION_TO_STATUS
from app.evidence.facts import format_amount_statement, make_fact
from app.evidence.ids import make_evidence_id
from app.evidence.provenance import build_provenance, build_source_ids
from app.ml.constants import (
    ML_EVIDENCE_ENGINE,
    ML_EVIDENCE_LAYER,
    ML_EVIDENCE_NOTE,
    PROJECT_STORED_EVIDENCE,
)
from app.ml.types import MlPrediction, PredictionStatus
from app.models.project import Project
from app.models.snapshot import DatasetSnapshot

_FRAUD_TOKEN = re.compile(r"\bfraud(ulent)?\b", re.IGNORECASE)

# Stored ML evidence must not imply legal conclusions. Copilot may still say
# "not a fraud probability" because chat answers are not Evidence Objects.
PROHIBITED_STORED_ML_PHRASES = (
    "probability of wrongdoing",
    "likelihood of wrongdoing",
    "legal finding",
    "legal guilt",
    "corruption",
    "fraud probability",
    "fraud detected",
    "confirmed misconduct",
    "fraudulent",
    "fraud",
)

_PHRASE_REPLACEMENTS: tuple[tuple[re.Pattern[str], str], ...] = tuple(
    (re.compile(pattern, re.IGNORECASE), replacement)
    for pattern, replacement in (
        (
            r"they are not a fraud probability,\s*legal finding,\s*sanction, or payment release",
            "They measure unusualness relative to the training distribution only "
            "and are not a sanction or payment release",
        ),
        (
            r"it is not a legal finding,\s*not a probability of wrongdoing",
            "It measures unusualness relative to the training distribution only",
        ),
        (
            r"this is an ML anomaly\s+signal, not a legal finding",
            "This is an ML anomaly signal only",
        ),
        (
            r"this is not a fraud finding",
            "No anomaly score was produced from the available features",
        ),
        (
            r"not a fraud probability",
            "an unsupervised distributional rank versus the training set",
        ),
        (r"not a fraud finding", "not a scored anomaly signal"),
        (
            r"this is not a legal finding",
            "The model measures unusualness relative to the training distribution only",
        ),
        (r"not a legal finding", "an unsupervised anomaly signal only"),
        (r"fraud probability", "distributional anomaly rank"),
        (r"fraud detected", "elevated anomaly signal"),
        (r"fraud finding", "anomaly signal"),
        (r"probability of wrongdoing", "distributional unusualness"),
        (r"likelihood of wrongdoing", "distributional unusualness"),
        (r"legal guilt", "legal determination"),
        (r"legal finding", "anomaly signal"),
        (r"confirmed misconduct", "elevated anomaly signal"),
        (r"\bcorruption\b", "unusualness"),
    )
)


def stored_ml_text_is_neutral(value: str) -> bool:
    blob = (value or "").casefold()
    return not any(phrase in blob for phrase in PROHIBITED_STORED_ML_PHRASES)


def sanitize_ml_text(value: str) -> str:
    """Rewrite inference text so stored Evidence Objects stay distributional."""
    text = value or ""
    for pattern, replacement in _PHRASE_REPLACEMENTS:
        text = pattern.sub(replacement, text)
    text = _FRAUD_TOKEN.sub("anomaly", text)
    return re.sub(r"[ \t]{2,}", " ", text).strip()


def _source_type(data_mode: DataMode) -> SourceType:
    if data_mode == DataMode.SYNTHETIC:
        return SourceType.SYNTHETIC_TEST_RECORD
    if data_mode == DataMode.HYBRID:
        return SourceType.HYBRID_ENRICHMENT
    return SourceType.ML_MODEL


def _disposition(prediction: MlPrediction) -> EvidenceDisposition:
    if prediction.status != PredictionStatus.SCORED or prediction.ml_anomaly_score is None:
        return EvidenceDisposition.INCONCLUSIVE
    if prediction.decision_label == "ELEVATED":
        return EvidenceDisposition.WHY_FLAGGED
    return EvidenceDisposition.WHY_NOT_FLAGGED


def _finding(prediction: MlPrediction) -> str:
    if prediction.status != PredictionStatus.SCORED or prediction.ml_anomaly_score is None:
        missing = ", ".join(prediction.feature_availability.missing) or "required observed fields"
        return (
            f"INCONCLUSIVE: ML anomaly signal was not scored because {missing} "
            "are unavailable. The model produced no anomaly score from the available "
            "features."
        )
    if prediction.decision_label == "ELEVATED":
        return (
            "ELEVATED_ANOMALY_SIGNAL: The model produced an elevated anomaly signal "
            "from the available features. The allocation is unusual relative to the "
            "model's training distribution."
        )
    return (
        "ML_ANOMALY_SIGNAL: The observed feature pattern is not in the upper tail "
        "of the model's training distribution."
    )


def _severity(disposition: EvidenceDisposition) -> EvidenceSeverity:
    if disposition == EvidenceDisposition.WHY_FLAGGED:
        return EvidenceSeverity.WATCH
    return EvidenceSeverity.INFO


def prediction_to_evidence(
    prediction: MlPrediction,
    project: Project,
    *,
    data_mode: DataMode,
    snapshot: DatasetSnapshot | None = None,
    observed_at: datetime | None = None,
) -> EvidenceObject:
    created_at = observed_at or datetime.now(timezone.utc)
    source_type = _source_type(data_mode)
    model_version = prediction.model.model_version or "unknown"
    extra_ids = [
        f"model:{prediction.model.model_name}",
        f"model_version:{model_version}",
        f"feature_schema:{prediction.model.feature_schema_version or 'unknown'}",
        f"training_data_hash:{prediction.model.training_data_hash or 'unknown'}",
    ]
    source_ids = build_source_ids(project.internal_project_id, extra_ids)
    extra_notes = sanitize_ml_text(
        f"Source is the ML model {prediction.model.model_name} "
        f"(version {model_version}, feature schema "
        f"{prediction.model.feature_schema_version or 'unknown'}, "
        f"training_mode {prediction.model.training_mode}, "
        f"training_data_hash {prediction.model.training_data_hash or 'unknown'}). "
        f"{ML_EVIDENCE_NOTE}"
    )
    provenance = build_provenance(
        project,
        data_mode=data_mode,
        source_type=source_type,
        source_ids=source_ids,
        snapshot=snapshot,
        extra_notes=extra_notes,
    )
    derived = f"{prediction.model.model_name}:{model_version}"
    availability = {
        "available": list(prediction.feature_availability.available),
        "missing": list(prediction.feature_availability.missing),
        "unseen": list(prediction.feature_availability.unseen),
        "unsupported": list(prediction.feature_availability.unsupported),
        "coverage": prediction.feature_availability.coverage,
    }
    limitations = [sanitize_ml_text(item) for item in prediction.limitations]
    note = sanitize_ml_text(ML_EVIDENCE_NOTE)
    if note not in limitations:
        limitations.append(note)
    facts = [
        make_fact(
            "allocation_amount",
            project.allocation_amount,
            "project.allocation_amount",
            kind=EvidenceFactKind.OBSERVATION,
            statement=format_amount_statement(project.allocation_amount),
        ),
        make_fact("observed_category", project.category, "project.category"),
        make_fact("constituency", project.constituency, "project.constituency"),
        make_fact("work_description", project.work_description, "project.work_description"),
        make_fact("recommended_date", project.recommended_date, "project.recommended_date"),
        make_fact("ml_anomaly_observation", True, derived, kind=EvidenceFactKind.OBSERVATION),
        make_fact("model_name", prediction.model.model_name, derived),
        make_fact("model_version", model_version, derived),
        make_fact("model_type", prediction.model.model_type, derived),
        make_fact("feature_schema_version", prediction.model.feature_schema_version, derived),
        make_fact("training_data_hash", prediction.model.training_data_hash, derived),
        make_fact("training_mode", prediction.model.training_mode, derived),
        make_fact("data_mode", data_mode.value, derived),
        make_fact("ml_anomaly_score", prediction.ml_anomaly_score, derived),
        make_fact("ml_anomaly_finding", sanitize_ml_text(_finding(prediction)), derived),
        make_fact("decision_label", prediction.decision_label, derived),
        make_fact("prediction_status", prediction.status.value, derived),
        make_fact("feature_availability", availability, derived),
        make_fact("feature_values", prediction.feature_values, derived),
        make_fact(
            "contributions",
            [
                {
                    "feature": row.feature,
                    "value": row.value,
                    "contribution": row.contribution,
                    "note": row.note,
                }
                for row in prediction.contributions
            ],
            derived,
        ),
        make_fact("limitations", limitations, derived),
        make_fact("assessment_kind", PROJECT_STORED_EVIDENCE, derived),
        make_fact("evidence_source", "ml_model", derived),
        make_fact("ml_evidence_layer", ML_EVIDENCE_LAYER, derived),
        make_fact("not_fused_into_investigation_priority", True, derived),
        make_fact("ml_score_is_distributional_rank", True, derived),
    ]
    disposition = _disposition(prediction)
    observation_token = f"{created_at.isoformat()}:{uuid4().hex[:8]}"
    return EvidenceObject(
        evidence_id=make_evidence_id(
            engine_name=ML_EVIDENCE_ENGINE,
            engine_version=model_version,
            project_id=project.id,
            signal_type=SignalType.ML_ANOMALY_SIGNAL.value,
            data_mode=data_mode.value,
            extra=observation_token,
        ),
        project_id=project.id,
        signal_type=SignalType.ML_ANOMALY_SIGNAL,
        finding=sanitize_ml_text(_finding(prediction)),
        severity=_severity(disposition),
        score=prediction.ml_anomaly_score,
        confidence=max(0.0, min(1.0, float(prediction.feature_availability.coverage))),
        source_type=source_type,
        source_ids=source_ids,
        evidence_facts=facts,
        explanation=sanitize_ml_text(prediction.explanation),
        engine_name=EvidenceEngine.ML,
        engine_version=model_version,
        created_at=created_at,
        data_mode=data_mode,
        provenance=provenance,
        disposition=disposition,
        status=DISPOSITION_TO_STATUS[disposition],
    )


def evidence_summary(obj: EvidenceObject) -> dict[str, object]:
    facts = {fact.key: fact.value for fact in obj.evidence_facts}
    availability = facts.get("feature_availability") or {}
    limitations = facts.get("limitations") or []
    if not isinstance(availability, dict):
        availability = {}
    if not isinstance(limitations, list):
        limitations = [str(limitations)]
    return {
        "assessment_kind": PROJECT_STORED_EVIDENCE,
        "evidence_kind": PROJECT_STORED_EVIDENCE,
        "persisted": True,
        "project_id": obj.project_id,
        "internal_project_id": obj.provenance.internal_project_id,
        "evidence_id": obj.evidence_id,
        "signal_type": obj.signal_type.value
        if hasattr(obj.signal_type, "value")
        else str(obj.signal_type),
        "finding": obj.finding,
        "disposition": obj.disposition.value,
        "ml_anomaly_score": None if obj.score is None else int(obj.score),
        "confidence": obj.confidence,
        "data_mode": obj.data_mode.value,
        "model_name": facts.get("model_name"),
        "model_version": facts.get("model_version") or obj.engine_version,
        "feature_schema_version": facts.get("feature_schema_version"),
        "training_data_hash": facts.get("training_data_hash"),
        "training_mode": facts.get("training_mode"),
        "explanation": obj.explanation,
        "limitations": [str(item) for item in limitations],
        "feature_availability": availability,
        "fraud_probability": None,
        "evidence": obj,
    }
