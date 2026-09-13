"""Milestone Advisor V1 → canonical Evidence Object V1.

Does not change Evidence Object validation or frozen engine scoring.
"""

from __future__ import annotations

import hashlib

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
from app.engines.milestone.assess import HOLD, INSPECT, PROCEED
from app.engines.milestone.constants import ENGINE_NAME, ENGINE_VERSION
from app.engines.milestone.types import AssessmentResult
from app.evidence.constants import DISPOSITION_TO_STATUS
from app.evidence.facts import make_fact
from app.evidence.provenance import build_provenance, build_source_ids
from app.models.milestone import Milestone
from app.models.project import Project
from app.models.snapshot import DatasetSnapshot


def _source_type(data_mode: DataMode) -> SourceType:
    if data_mode == DataMode.SYNTHETIC:
        return SourceType.SYNTHETIC_TEST_RECORD
    if data_mode == DataMode.HYBRID:
        return SourceType.HYBRID_ENRICHMENT
    return SourceType.MILESTONE_CLAIM


def _disposition(recommendation: str) -> EvidenceDisposition:
    if recommendation == INSPECT:
        return EvidenceDisposition.WHY_FLAGGED
    if recommendation == HOLD:
        return EvidenceDisposition.WHY_FLAGGED
    if recommendation == PROCEED:
        return EvidenceDisposition.WHY_NOT_FLAGGED
    return EvidenceDisposition.INCONCLUSIVE


def _severity(recommendation: str) -> EvidenceSeverity:
    if recommendation == INSPECT:
        return EvidenceSeverity.ATTENTION
    if recommendation == HOLD:
        return EvidenceSeverity.WATCH
    return EvidenceSeverity.INFO


def _evidence_id(project_id: int, milestone_id: int, data_mode: str) -> str:
    signal = "milestone"
    payload = "|".join(
        [ENGINE_NAME, ENGINE_VERSION, str(project_id), signal, data_mode, str(milestone_id)]
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"ev:{ENGINE_NAME}:{project_id}:{signal}:{data_mode}:{digest}"


def assessment_to_evidence(
    project: Project,
    milestone: Milestone,
    result: AssessmentResult,
    *,
    data_mode: DataMode,
    snapshot: DatasetSnapshot | None = None,
) -> EvidenceObject:
    source_type = _source_type(data_mode)
    extra = [f"milestone:{milestone.id}"]
    source_ids = build_source_ids(project.internal_project_id, extra)
    extra_notes = (
        "Milestone Advisor V1 recommendation only. Authorized officials make "
        "the final administrative decision. SARVSAKSHI does not release funds. "
        "Not a legal finding."
    )
    if data_mode != DataMode.REAL:
        extra_notes = (
            f"{extra_notes} HYBRID/SYNTHETIC milestone or execution values are labelled "
            "and are not official MPLADS records."
        )
    provenance = build_provenance(
        project,
        data_mode=data_mode,
        source_type=source_type,
        source_ids=source_ids,
        snapshot=snapshot,
        extra_notes=extra_notes,
    )
    disposition = _disposition(result.recommendation)
    facts = [
        make_fact("milestone_id", milestone.id, ENGINE_VERSION, kind=EvidenceFactKind.OBSERVATION),
        make_fact("milestone_number", milestone.milestone_number, ENGINE_VERSION, kind=EvidenceFactKind.OBSERVATION),
        make_fact("recommendation", result.recommendation, ENGINE_VERSION),
        make_fact("pce_result", result.pce_result, ENGINE_VERSION),
        make_fact("evidence_status", result.evidence_status, ENGINE_VERSION),
        make_fact("independent_concerns", result.independent_concerns, ENGINE_VERSION),
        make_fact("supporting_evidence", result.supporting_evidence, ENGINE_VERSION),
        make_fact("conflicting_evidence", result.conflicting_evidence, ENGINE_VERSION),
        make_fact("missing_evidence", result.missing_evidence, ENGINE_VERSION),
        make_fact("funds_released", False, ENGINE_VERSION),
        make_fact("payment_executed", False, ENGINE_VERSION),
        make_fact("automatic_sanction", False, ENGINE_VERSION),
    ]
    finding = f"Milestone recommendation is {result.recommendation}"
    return EvidenceObject(
        evidence_id=_evidence_id(project.id, milestone.id, data_mode.value),
        project_id=project.id,
        signal_type=SignalType.MILESTONE,
        finding=finding,
        severity=_severity(result.recommendation),
        score=None,
        confidence=result.evidence_confidence,
        source_type=source_type,
        source_ids=source_ids,
        evidence_facts=facts,
        explanation=result.explanation,
        engine_name=EvidenceEngine.MILESTONE.value,
        engine_version=ENGINE_VERSION,
        data_mode=data_mode,
        provenance=provenance,
        disposition=disposition,
        status=DISPOSITION_TO_STATUS[disposition],
    )
