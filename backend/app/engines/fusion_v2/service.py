"""Risk Fusion V2 persistence and orchestration.

Consumes stored Evidence Objects. Does not change frozen engine logic.
Does not overwrite Risk Fusion V1.1 fusion_score rows.
Historical V2 results are appended, never mutated.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import DataMode, EvidenceEngine
from app.domain.schemas.evidence import EvidenceObject
from app.engines.fusion_v2.constants import CONFIG_VERSION, ENGINE_VERSION
from app.engines.fusion_v2.fuse import fuse_evidence_v2
from app.engines.fusion_v2.types import FusionV2Result
from app.errors import AppError
from app.evidence.repository import list_project_evidence
from app.models.fusion_v2 import FusionScoreV2, FusionScoreV2History
from app.models.project import Project


def _mode_value(data_mode: DataMode | str) -> DataMode:
    if isinstance(data_mode, DataMode):
        return data_mode
    text = str(data_mode).strip().upper().replace("-", "_")
    if text in {"HYBRID_TEST", "HYBRIDTEST"}:
        return DataMode.HYBRID
    return DataMode(text)


def select_evidence_for_mode_v2(
    items: list[EvidenceObject],
    data_mode: DataMode,
) -> list[EvidenceObject]:
    """Choose evidence for the requested V2 fusion mode.

    REAL never consumes HYBRID/SYNTHETIC objects.
    HYBRID prefers matching HYBRID objects and includes REAL objects for
    groups that have no HYBRID counterpart (Cost V1.1 has no HYBRID-TEST).
    """
    if data_mode == DataMode.REAL:
        return [item for item in items if item.data_mode == DataMode.REAL]
    if data_mode == DataMode.SYNTHETIC:
        return [item for item in items if item.data_mode == DataMode.SYNTHETIC]
    selected: list[EvidenceObject] = []
    hybrid_engines = {
        str(item.engine_name)
        for item in items
        if item.data_mode == DataMode.HYBRID
    }
    for item in items:
        engine = str(item.engine_name)
        if item.data_mode == DataMode.HYBRID:
            selected.append(item)
        elif item.data_mode == DataMode.REAL and engine not in hybrid_engines:
            selected.append(item)
        elif (
            item.data_mode == DataMode.REAL
            and engine == EvidenceEngine.COST.value
        ):
            selected.append(item)
    return selected


def result_payload(result: FusionV2Result) -> dict[str, object]:
    return {
        "engine_version": ENGINE_VERSION,
        "data_mode": result.data_mode.value,
        "investigation_priority": result.investigation_priority,
        "investigation_priority_0_100": result.investigation_priority_0_100,
        "raw_risk": result.raw_risk,
        "evidence_confidence": result.evidence_confidence,
        "risk_class": result.risk_class.value,
        "recommended_action": result.recommended_action.value,
        "explanation_type": result.explanation_type.value,
        "explanation": result.explanation,
        "recommendation": result.recommendation,
        "contributing_evidence_groups": [
            item.as_payload() for item in result.contributing_evidence_groups
        ],
        "independent_evidence_groups": [
            item.as_payload() for item in result.independent_evidence_groups
        ],
        "discounted_correlated_evidence": [
            item.as_payload() for item in result.discounted_correlated_evidence
        ],
        "unavailable_evidence": [item.as_payload() for item in result.unavailable_evidence],
        "not_assessable_evidence": [
            item.as_payload() for item in result.not_assessable_evidence
        ],
        "conflicting_evidence": [item.as_payload() for item in result.conflicting_evidence],
        "all_groups": [item.as_payload() for item in result.all_groups],
        "evidence_ids": result.evidence_ids,
        "ignored_duplicate_evidence_ids": result.ignored_duplicate_evidence_ids,
        "available_weight": result.available_weight,
        "unavailable_weight": result.unavailable_weight,
        "evidence_coverage": result.evidence_coverage,
        "synthetic_disclosure": result.synthetic_disclosure,
        "evidence_fingerprint": result.evidence_fingerprint,
        "weight_note": result.weight_note,
        "governance_note": result.governance_note,
    }


def persist_fusion_score_v2(session: Session, result: FusionV2Result) -> FusionScoreV2:
    """Upsert latest V2 row and append an immutable history snapshot."""
    payload = json.dumps(result_payload(result), sort_keys=True)
    existing = session.scalars(
        select(FusionScoreV2).where(
            FusionScoreV2.project_id == result.project_id,
            FusionScoreV2.data_mode == result.data_mode.value,
        )
    ).first()
    if existing is None:
        row = FusionScoreV2(
            project_id=result.project_id,
            data_mode=result.data_mode.value,
            investigation_priority=result.investigation_priority,
            evidence_confidence=result.evidence_confidence,
            risk_class=result.risk_class.value,
            recommended_action=result.recommended_action.value,
            explanation_type=result.explanation_type.value,
            config_version=CONFIG_VERSION,
            engine_version=ENGINE_VERSION,
            evidence_fingerprint=result.evidence_fingerprint,
            payload_json=payload,
        )
        session.add(row)
    else:
        existing.investigation_priority = result.investigation_priority
        existing.evidence_confidence = result.evidence_confidence
        existing.risk_class = result.risk_class.value
        existing.recommended_action = result.recommended_action.value
        existing.explanation_type = result.explanation_type.value
        existing.config_version = CONFIG_VERSION
        existing.engine_version = ENGINE_VERSION
        existing.evidence_fingerprint = result.evidence_fingerprint
        existing.payload_json = payload
        row = existing
    session.add(
        FusionScoreV2History(
            project_id=result.project_id,
            data_mode=result.data_mode.value,
            investigation_priority=result.investigation_priority,
            evidence_confidence=result.evidence_confidence,
            risk_class=result.risk_class.value,
            recommended_action=result.recommended_action.value,
            explanation_type=result.explanation_type.value,
            config_version=CONFIG_VERSION,
            engine_version=ENGINE_VERSION,
            evidence_fingerprint=result.evidence_fingerprint,
            payload_json=payload,
            computed_at=datetime.now(timezone.utc),
        )
    )
    session.flush()
    return row


def list_fusion_v2_history(
    session: Session,
    project_id: int,
    *,
    data_mode: DataMode | None = None,
) -> list[FusionScoreV2History]:
    stmt = select(FusionScoreV2History).where(FusionScoreV2History.project_id == project_id)
    if data_mode is not None:
        stmt = stmt.where(FusionScoreV2History.data_mode == data_mode.value)
    stmt = stmt.order_by(FusionScoreV2History.id.asc())
    return list(session.scalars(stmt).all())


def assess_project_risk_v2(
    session: Session,
    project_id: int,
    *,
    data_mode: DataMode | str = DataMode.REAL,
    persist: bool = True,
) -> FusionV2Result:
    project = session.get(Project, project_id)
    if project is None:
        raise AppError("Project not found.", code="not_found", status_code=404)
    mode = _mode_value(data_mode)
    stored = list_project_evidence(session, project_id)
    selected = select_evidence_for_mode_v2(stored, mode)
    result = fuse_evidence_v2(
        selected,
        project_id=project_id,
        internal_project_id=project.internal_project_id,
        requested_data_mode=mode,
    )
    if persist:
        persist_fusion_score_v2(session, result)
        session.commit()
    return result
