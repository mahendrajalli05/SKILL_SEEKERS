"""Risk Fusion V1.1 orchestration.

Consumes stored Evidence Objects. Does not change Cost, Time, Overlap,
or Compliance analytical logic.
"""

from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import DataMode, EvidenceEngine
from app.domain.schemas.evidence import EvidenceObject
from app.engines.fusion.constants import CONFIG_VERSION, ENGINE_VERSION
from app.engines.fusion.fuse import fuse_evidence
from app.engines.fusion.types import FusionResult
from app.errors import AppError
from app.evidence.repository import list_project_evidence
from app.models.fusion import FusionScore
from app.models.project import Project


def _mode_value(data_mode: DataMode | str) -> DataMode:
    if isinstance(data_mode, DataMode):
        return data_mode
    text = str(data_mode).strip().upper().replace("-", "_")
    if text in {"HYBRID_TEST", "HYBRIDTEST"}:
        return DataMode.HYBRID
    return DataMode(text)


def select_evidence_for_mode(
    items: list[EvidenceObject],
    data_mode: DataMode,
) -> list[EvidenceObject]:
    """Choose evidence for the requested fusion mode.

    Cost V1.1 has no HYBRID-TEST mode, so REAL cost evidence is included when
    fusing HYBRID. Time/Overlap/Compliance prefer matching HYBRID objects.
    """
    if data_mode == DataMode.REAL:
        return [item for item in items if item.data_mode == DataMode.REAL]
    if data_mode == DataMode.SYNTHETIC:
        return [item for item in items if item.data_mode == DataMode.SYNTHETIC]
    selected: list[EvidenceObject] = []
    for item in items:
        engine = str(item.engine_name)
        if item.data_mode == DataMode.HYBRID:
            selected.append(item)
        elif (
            item.data_mode == DataMode.REAL
            and engine == EvidenceEngine.COST.value
        ):
            selected.append(item)
    return selected


def persist_fusion_score(session: Session, result: FusionResult) -> FusionScore:
    existing = session.scalars(
        select(FusionScore).where(FusionScore.project_id == result.project_id)
    ).first()
    why_flagged = result.explanation if result.explanation_type.value == "WHY_FLAGGED" else None
    why_not = result.explanation if result.explanation_type.value != "WHY_FLAGGED" else None
    payload = json.dumps(
        {
            "engine_version": ENGINE_VERSION,
            "data_mode": result.data_mode.value,
            "recommended_action": result.recommended_action.value,
            "explanation_type": result.explanation_type.value,
            "raw_risk": result.raw_risk,
            "investigation_priority_0_100": result.investigation_priority_0_100,
            "available_signal_weight": result.available_signal_weight,
            "unavailable_signal_weight": result.unavailable_signal_weight,
            "evidence_coverage": result.evidence_coverage,
            "contributing_signals": [item.as_payload() for item in result.contributing_signals],
            "unavailable_signals": [item.as_payload() for item in result.unavailable_signals],
            "evidence_ids": result.evidence_ids,
            "ignored_duplicate_evidence_ids": result.ignored_duplicate_evidence_ids,
        },
        sort_keys=True,
    )
    if existing is None:
        row = FusionScore(
            project_id=result.project_id,
            investigation_priority=result.investigation_priority,
            evidence_confidence=result.evidence_confidence,
            config_version=CONFIG_VERSION,
            why_flagged=why_flagged,
            why_not_flagged=why_not,
            data_mode=result.data_mode.value,
            recommended_action=result.recommended_action.value,
            explanation_type=result.explanation_type.value,
            payload_json=payload,
        )
        session.add(row)
    else:
        existing.investigation_priority = result.investigation_priority
        existing.evidence_confidence = result.evidence_confidence
        existing.config_version = CONFIG_VERSION
        existing.why_flagged = why_flagged
        existing.why_not_flagged = why_not
        existing.data_mode = result.data_mode.value
        existing.recommended_action = result.recommended_action.value
        existing.explanation_type = result.explanation_type.value
        existing.payload_json = payload
        row = existing
    session.flush()
    return row


def assess_project_risk(
    session: Session,
    project_id: int,
    *,
    data_mode: DataMode | str = DataMode.REAL,
    persist: bool = True,
) -> FusionResult:
    project = session.get(Project, project_id)
    if project is None:
        raise AppError("Project not found.", code="not_found", status_code=404)
    mode = _mode_value(data_mode)
    stored = list_project_evidence(session, project_id)
    selected = select_evidence_for_mode(stored, mode)
    result = fuse_evidence(
        selected,
        project_id=project_id,
        internal_project_id=project.internal_project_id,
        requested_data_mode=mode,
    )
    if persist:
        persist_fusion_score(session, result)
        session.commit()
    return result
