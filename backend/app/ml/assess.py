"""Combine existing engines with ML for a project that has no stored ID.

Does not persist Evidence Objects, does not fuse Investigation Priority,
and does not duplicate engine logic.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.engines.compliance.constants import REAL_OBSERVATION_DATE
from app.engines.compliance.service import assess_compliance
from app.engines.compliance.types import ComplianceContext, ComplianceMode
from app.engines.cost.repository import SqlPeerSource
from app.engines.cost.service import assess_cost
from app.engines.cost.types import PeerRecord
from app.engines.cost.work_type import derive_work_type
from app.engines.overlap.repository import load_overlap_records
from app.engines.overlap.service import assess_overlap
from app.engines.overlap.text import (
    combine_place_text,
    constituency_fields,
    embedding_text,
    rare_block_tokens,
)
from app.engines.overlap.types import OverlapMode, OverlapRecord
from app.engines.time.constants import REAL_OBSERVATION_DATE as TIME_OBS
from app.engines.time.repository import SqlTimePeerSource
from app.engines.time.service import assess_time
from app.engines.time.types import TimeMode, TimePeerRecord
from app.engines.context.service import assess_new_project_context
from app.ml.constants import (
    COMPLIANCE_NOTE,
    GOVERNANCE_NOTE,
    NEW_PROJECT_ASSESSMENT,
    NEW_PROJECT_EVIDENCE_NOTE,
    NEW_PROJECT_RISK_REASON,
    OVERLAP_NOTE,
    RISK_NOTE,
    TIME_LIMITATION,
)
from app.ml.errors import ModelMissingError, ModelVersionMismatchError
from app.ml.inference.cost import predict_cost
from app.ml.inference.service import prediction_to_dict
from app.ml.inference.time import predict_time
from app.ml.types import DataMode


NEW_PROJECT_ID = 0
NEW_INTERNAL_ID = "new-project-assessment"


def _lifecycle(status: str) -> str:
    key = (status or "").strip().lower()
    if key == "completed":
        return "COMPLETED"
    if key == "ongoing":
        return "ONGOING"
    if key in {"unsanctioned", "sanctioned"}:
        return "FUTURE"
    return "UNKNOWN"


def _parse_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value.strip():
        return date.fromisoformat(value.strip()[:10])
    return None


def _amount(payload: dict[str, Any]) -> int | None:
    raw = payload.get("allocation_amount")
    if raw is None or raw == "":
        return None
    return int(raw)


def assess_new_project(session: Session, payload: dict[str, Any]) -> dict[str, Any]:
    data_mode = str(payload.get("data_mode") or DataMode.REAL.value)
    requested_version = payload.get("model_version")
    amount = _amount(payload)
    rec_date = _parse_date(payload.get("recommendation_date") or payload.get("recommended_date"))
    category = (payload.get("category") or "").strip()
    state = (payload.get("state") or "").strip()
    constituency = (payload.get("constituency") or "").strip()
    work = (payload.get("work_description") or "").strip()
    status = (payload.get("status") or "").strip()
    house = (payload.get("house") or "").strip()

    cost_engine = None
    if amount is not None and amount > 0:
        subject = PeerRecord(
            project_id=NEW_PROJECT_ID,
            internal_project_id=NEW_INTERNAL_ID,
            constituency=constituency,
            category=category,
            state=state,
            work_description=work,
            derived_work_type=derive_work_type(work),
            allocation_amount=amount,
            recommended_date=rec_date,
            is_synthetic=False,
        )
        cost_engine = assess_cost(subject, SqlPeerSource(session, subject_is_synthetic=False))

    const_value, usable, kind, _exclusion = constituency_fields(constituency)
    overlap_subject = OverlapRecord(
        project_id=NEW_PROJECT_ID,
        internal_project_id=NEW_INTERNAL_ID,
        source_work=work,
        work_description=work,
        embedding_text=embedding_text(work),
        category=category,
        constituency=const_value,
        constituency_usable=usable,
        constituency_kind=kind,
        state=state,
        allocation_amount=amount,
        recommended_date=rec_date,
        place_text=combine_place_text(),
        rare_tokens=rare_block_tokens(work),
    )
    corpus = load_overlap_records(session, mode=OverlapMode.REAL, subject_is_synthetic=False)
    overlap_engine = assess_overlap(overlap_subject, corpus, mode=OverlapMode.REAL)

    time_subject = TimePeerRecord(
        project_id=NEW_PROJECT_ID,
        internal_project_id=NEW_INTERNAL_ID,
        constituency=constituency,
        category=category,
        state=state,
        work_description=work,
        derived_work_type=derive_work_type(work),
        status=status,
        lifecycle_stage=_lifecycle(status),
        recommended_date=rec_date,
        time_mode=TimeMode.REAL,
        observation_date=TIME_OBS,
    )
    time_engine = assess_time(
        time_subject,
        SqlTimePeerSource(session, time_mode=TimeMode.REAL, observation_date=TIME_OBS),
    )

    compliance_engine = assess_compliance(
        ComplianceContext(
            project_id=NEW_PROJECT_ID,
            internal_project_id=NEW_INTERNAL_ID,
            mode=ComplianceMode.REAL,
            mp_name="",
            work_description=work,
            category=category,
            state=state,
            constituency=constituency,
            ida="",
            city="",
            ward="",
            block="",
            village="",
            recommended_date=rec_date,
            allocation_amount=amount,
            ida_approval="",
            status=status,
            house=house,
            lifecycle_stage=_lifecycle(status),
            observation_date=REAL_OBSERVATION_DATE,
        )
    )

    ml_cost = None
    ml_cost_error = None
    try:
        ml_cost = predict_cost(
            payload,
            data_mode=data_mode,
            requested_version=requested_version,
        )
    except (ModelMissingError, ModelVersionMismatchError) as exc:
        ml_cost_error = {"code": exc.code, "message": exc.message}

    ml_time = predict_time(payload, data_mode=data_mode)

    context_payload = assess_new_project_context(session, payload).as_dict()

    return {
        "assessment_kind": NEW_PROJECT_ASSESSMENT,
        "is_new_project": True,
        "project_id": None,
        "data_mode": data_mode,
        "ml": {
            "cost": prediction_to_dict(ml_cost) if ml_cost else None,
            "time": prediction_to_dict(ml_time),
            "error": ml_cost_error,
        },
        "cost_v1_1": _cost_brief(cost_engine),
        "time_v1": _time_brief(time_engine),
        "overlap_v1": _overlap_brief(overlap_engine),
        "compliance_v1": _compliance_brief(compliance_engine),
        "risk_fusion_v2": {
            "available": False,
            "investigation_priority": None,
            "evidence_confidence": None,
            "recommended_action": None,
            "reason": NEW_PROJECT_RISK_REASON,
        },
        "limitations": [
            GOVERNANCE_NOTE,
            OVERLAP_NOTE,
            COMPLIANCE_NOTE,
            RISK_NOTE,
            TIME_LIMITATION,
            NEW_PROJECT_RISK_REASON,
            "No Evidence Objects were stored for this assessment.",
            NEW_PROJECT_EVIDENCE_NOTE,
        ],
        "fraud_probability": None,
        "automatic_sanction": False,
        "automatic_payment": False,
        "pfms_integrated": False,
        "evidence_kind": NEW_PROJECT_ASSESSMENT,
        "persisted": False,
        "contextual_v1": context_payload,
    }


def _cost_brief(result) -> dict[str, Any] | None:
    if result is None:
        return {
            "available": False,
            "reason": "Allocation amount is required for Cost Intelligence V1.1.",
            "engine_version": "cost-peer-v1.1",
        }
    return {
        "available": True,
        "engine": result.engine,
        "engine_version": result.engine_version,
        "outcome": result.outcome.value,
        "flagged": result.flagged,
        "cost_anomaly_score": result.cost_anomaly_score,
        "evidence_confidence": result.evidence_confidence,
        "peer_scope_label": result.peer_scope_label,
        "peer_count": result.peer_count,
        "baseline": result.baseline,
        "actual_amount": result.actual_amount,
        "explanation": result.explanation,
        "why_flagged": result.why_flagged,
        "why_not_flagged": result.why_not_flagged,
    }


def _time_brief(result) -> dict[str, Any]:
    return {
        "available": result.time_anomaly_score is not None,
        "engine": result.engine,
        "engine_version": result.engine_version,
        "outcome": result.outcome.value,
        "time_anomaly_score": result.time_anomaly_score,
        "evidence_confidence": result.evidence_confidence,
        "explanation": result.explanation,
        "limitation": TIME_LIMITATION,
    }


def _overlap_brief(result) -> dict[str, Any]:
    matches = [
        {
            "linked_project_id": item.linked_project_id,
            "linked_work_description": item.linked_work_description,
            "overlap_score": item.overall_overlap_score,
            "semantic_similarity": item.semantic_similarity,
        }
        for item in result.matches[:5]
    ]
    return {
        "available": True,
        "engine": result.engine,
        "engine_version": result.engine_version,
        "outcome": result.outcome.value,
        "flagged": result.flagged,
        "overlap_score": result.overlap_score,
        "evidence_confidence": result.evidence_confidence,
        "match_count": result.match_count,
        "matches": matches,
        "explanation": result.explanation,
        "note": OVERLAP_NOTE,
    }


def _compliance_brief(result) -> dict[str, Any]:
    return {
        "available": True,
        "engine": result.engine,
        "engine_version": result.engine_version,
        "status": result.compliance_status.value,
        "triggered_rule_ids": list(result.triggered_rule_ids),
        "explanation": result.explanation,
        "note": COMPLIANCE_NOTE,
    }
