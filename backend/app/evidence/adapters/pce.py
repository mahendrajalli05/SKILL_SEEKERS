"""Plan–Claim–Evidence V1 → canonical Evidence Object.

Does not change Cost/Time/Overlap/Compliance/Fusion scoring.
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
from app.engines.pce.constants import ENGINE_NAME, ENGINE_VERSION
from app.engines.pce.types import AssembledEvidenceItem, ConsistencyStatus, VerificationResult
from app.evidence.constants import DISPOSITION_TO_STATUS
from app.evidence.facts import make_fact
from app.evidence.ids import make_evidence_id
from app.evidence.provenance import build_provenance, build_source_ids
from app.models.project import Project
from app.models.snapshot import DatasetSnapshot


def _attachment_evidence_id(
    *,
    project_id: int,
    signal_type: str,
    data_mode: str,
    attachment_key: str,
) -> str:
    payload = "|".join(
        [ENGINE_NAME, ENGINE_VERSION, str(project_id), signal_type, data_mode, attachment_key]
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"ev:{ENGINE_NAME}:{project_id}:{signal_type}:{data_mode}:{digest}"


def _source_type(data_mode: DataMode, primary: SourceType) -> SourceType:
    if data_mode == DataMode.SYNTHETIC:
        return SourceType.SYNTHETIC_TEST_RECORD
    if data_mode == DataMode.HYBRID:
        return SourceType.HYBRID_ENRICHMENT
    return primary


def _disposition_for(status: ConsistencyStatus) -> EvidenceDisposition:
    if status == ConsistencyStatus.MISMATCH:
        return EvidenceDisposition.WHY_FLAGGED
    if status == ConsistencyStatus.CONSISTENT:
        return EvidenceDisposition.WHY_NOT_FLAGGED
    return EvidenceDisposition.INCONCLUSIVE


def attachment_to_evidence(
    project: Project,
    item: AssembledEvidenceItem,
    *,
    extra_ids: list[str],
    snapshot: DatasetSnapshot | None = None,
) -> EvidenceObject:
    is_image = item.evidence_kind in {"image", "photo"}
    signal = SignalType.IMAGE if is_image else SignalType.DOCUMENT
    engine = EvidenceEngine.IMAGE if is_image else EvidenceEngine.DOCUMENT
    primary = SourceType.IMAGE_ARTIFACT if is_image else SourceType.DOCUMENT_ARTIFACT
    source_type = _source_type(item.data_mode, primary)
    source_ids = build_source_ids(project.internal_project_id, extra_ids)
    provenance = build_provenance(
        project,
        data_mode=item.data_mode,
        source_type=source_type,
        source_ids=source_ids,
        snapshot=snapshot,
        extra_notes="Attachment recording only. Authenticity and satellite measurements are not assessed in V1.",
    )
    key = "|".join(
        [
            str(item.document_id or ""),
            str(item.photo_id or ""),
            item.filename or "",
            item.content_hash or "",
            item.evidence_kind,
        ]
    )
    evidence_id = _attachment_evidence_id(
        project_id=project.id,
        signal_type=signal.value,
        data_mode=item.data_mode.value,
        attachment_key=key,
    )
    finding = (
        "Officer-attached image evidence recorded"
        if is_image
        else "Officer-attached document evidence recorded"
    )
    facts = [
        make_fact("document_id", item.document_id, "document.id", kind=EvidenceFactKind.OBSERVATION),
        make_fact("photo_id", item.photo_id, "photo.id", kind=EvidenceFactKind.OBSERVATION),
        make_fact("filename", item.filename, "officer_upload", kind=EvidenceFactKind.OBSERVATION),
        make_fact("document_type", item.evidence_kind, "officer_upload"),
        make_fact("timestamp", item.timestamp, "officer_upload", kind=EvidenceFactKind.OBSERVATION),
        make_fact("latitude", item.latitude, "officer_upload", kind=EvidenceFactKind.OBSERVATION),
        make_fact("longitude", item.longitude, "officer_upload", kind=EvidenceFactKind.OBSERVATION),
        make_fact("content_hash", item.content_hash, "officer_upload", kind=EvidenceFactKind.OBSERVATION),
        make_fact("observed_quantity", item.observed_quantity, "officer_upload", kind=EvidenceFactKind.OBSERVATION),
        make_fact("observed_quantity_unit", item.observed_quantity_unit, "officer_upload"),
        make_fact("observed_expenditure", item.observed_expenditure, "officer_upload", kind=EvidenceFactKind.OBSERVATION),
        make_fact("source", item.source, "officer_upload"),
    ]
    return EvidenceObject(
        evidence_id=evidence_id,
        project_id=project.id,
        signal_type=signal,
        finding=finding,
        severity=EvidenceSeverity.INFO,
        score=None,
        confidence=0.2,
        source_type=source_type,
        source_ids=source_ids,
        evidence_facts=facts,
        explanation=(
            f"{finding} with structured metadata. This is a recording layer only "
            "and is not an image-authenticity or satellite measurement result."
        ),
        engine_name=engine.value,
        engine_version=ENGINE_VERSION,
        data_mode=item.data_mode,
        provenance=provenance,
        disposition=EvidenceDisposition.INCONCLUSIVE,
        status=DISPOSITION_TO_STATUS[EvidenceDisposition.INCONCLUSIVE],
    )


def verification_to_evidence(
    result: VerificationResult,
    project: Project,
    *,
    snapshot: DatasetSnapshot | None = None,
) -> EvidenceObject:
    disposition = _disposition_for(result.overall_result)
    source_type = _source_type(result.data_mode, SourceType.PLAN_RECORD)
    extra = list(result.evidence_ids)
    source_ids = build_source_ids(project.internal_project_id, extra)
    provenance = build_provenance(
        project,
        data_mode=result.data_mode,
        source_type=source_type,
        source_ids=source_ids,
        snapshot=snapshot,
        extra_notes="Deterministic Plan–Claim–Evidence consistency result. Not a legal finding.",
    )
    evidence_id = make_evidence_id(
        engine_name=ENGINE_NAME,
        engine_version=ENGINE_VERSION,
        project_id=project.id,
        signal_type=SignalType.PLAN_CLAIM_EVIDENCE.value,
        data_mode=result.data_mode.value,
    )
    facts = [
        make_fact("overall_result", result.overall_result.value, ENGINE_VERSION),
        make_fact("evidence_confidence", result.evidence_confidence, ENGINE_VERSION),
        make_fact("mismatch_count", len(result.mismatches), ENGINE_VERSION),
        make_fact("missing_information", result.missing_information, ENGINE_VERSION),
        make_fact("plan_findings", result.plan_findings, ENGINE_VERSION),
        make_fact("claim_findings", result.claim_findings, ENGINE_VERSION),
        make_fact("evidence_findings", result.evidence_findings, ENGINE_VERSION),
        make_fact(
            "comparison_statuses",
            {item.comparison_id: item.status.value for item in result.comparisons},
            ENGINE_VERSION,
        ),
    ]
    finding = f"Plan–Claim–Evidence result is {result.overall_result.value}"
    return EvidenceObject(
        evidence_id=evidence_id,
        project_id=project.id,
        signal_type=SignalType.PLAN_CLAIM_EVIDENCE,
        finding=finding,
        severity=(
            EvidenceSeverity.ATTENTION
            if result.overall_result == ConsistencyStatus.MISMATCH
            else EvidenceSeverity.INFO
        ),
        score=None,
        confidence=result.evidence_confidence,
        source_type=source_type,
        source_ids=source_ids,
        evidence_facts=facts,
        explanation=result.explanation,
        engine_name=EvidenceEngine.PCE.value,
        engine_version=ENGINE_VERSION,
        data_mode=result.data_mode,
        provenance=provenance,
        disposition=disposition,
        status=DISPOSITION_TO_STATUS[disposition],
    )
