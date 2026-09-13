"""Jan-Sakshi / Citizen Evidence V1 → canonical Evidence Object V1.

Does not change Evidence Object validation or frozen engine scoring.
Does not add citizen weighting to Risk Fusion.
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
from app.engines.citizen.constants import (
    ENGINE_NAME,
    ENGINE_VERSION,
    GOVERNANCE_NOTE,
    LOCATION_REJECTED,
    LOCATION_VERIFIED,
    PCE_CONTRADICTION,
    SIGNAL_AGGREGATE,
    SIGNAL_FEEDBACK,
    SIGNAL_IMAGE,
    SIGNAL_LOCATION,
    STATUS_REJECTED,
)
from app.engines.citizen.types import CitizenReportRecord, CitizenSummary
from app.evidence.constants import DISPOSITION_TO_STATUS
from app.evidence.facts import make_fact
from app.evidence.provenance import build_provenance, build_source_ids
from app.models.project import Project
from app.models.snapshot import DatasetSnapshot


def _source_type(data_mode: DataMode) -> SourceType:
    if data_mode == DataMode.SYNTHETIC:
        return SourceType.SYNTHETIC_TEST_RECORD
    return SourceType.CITIZEN_REPORT


def _evidence_id(project_id: int, signal: str, data_mode: str, digest_key: str) -> str:
    payload = "|".join([ENGINE_NAME, ENGINE_VERSION, str(project_id), signal, data_mode, digest_key])
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"ev:{ENGINE_NAME}:{project_id}:{signal}:{data_mode}:{digest}"


def _signal_enum(signal: str) -> SignalType:
    mapping = {
        SIGNAL_LOCATION: SignalType.CITIZEN_LOCATION,
        SIGNAL_FEEDBACK: SignalType.CITIZEN_FEEDBACK,
        SIGNAL_IMAGE: SignalType.CITIZEN_IMAGE,
        SIGNAL_AGGREGATE: SignalType.CITIZEN_AGGREGATE,
    }
    return mapping.get(signal, SignalType.CITIZEN)


def _base(
    project: Project,
    *,
    data_mode: DataMode,
    snapshot: DatasetSnapshot | None,
    extra_ids: list[str],
    extra_notes: str,
) -> tuple[SourceType, list[str], object]:
    source_type = _source_type(data_mode)
    source_ids = build_source_ids(project.internal_project_id, extra_ids)
    provenance = build_provenance(
        project,
        data_mode=data_mode,
        source_type=source_type,
        source_ids=source_ids,
        snapshot=snapshot,
        extra_notes=extra_notes,
    )
    return source_type, source_ids, provenance


def report_to_evidence_objects(
    project: Project,
    record: CitizenReportRecord,
    *,
    data_mode: DataMode,
    snapshot: DatasetSnapshot | None = None,
) -> list[EvidenceObject]:
    objects: list[EvidenceObject] = []
    extra = [f"citizen_report:{record.citizen_report_id}"]
    if record.image_id is not None:
        extra.append(f"image:{record.image_id}")
    source_type, source_ids, provenance = _base(
        project,
        data_mode=data_mode,
        snapshot=snapshot,
        extra_ids=extra,
        extra_notes=f"{GOVERNANCE_NOTE} Citizen report {record.citizen_report_id}.",
    )
    location = record.location_verification or {}
    loc_result = str(location.get("result") or record.verification_result)
    if loc_result == LOCATION_REJECTED:
        loc_disposition = EvidenceDisposition.WHY_FLAGGED
        loc_severity = EvidenceSeverity.WATCH
    elif loc_result == LOCATION_VERIFIED:
        loc_disposition = EvidenceDisposition.WHY_NOT_FLAGGED
        loc_severity = EvidenceSeverity.INFO
    else:
        loc_disposition = EvidenceDisposition.INCONCLUSIVE
        loc_severity = EvidenceSeverity.INFO
    loc_facts = [
        make_fact("citizen_report_id", record.citizen_report_id, ENGINE_VERSION, kind=EvidenceFactKind.OBSERVATION),
        make_fact("project_id", record.project_id, ENGINE_VERSION, kind=EvidenceFactKind.OBSERVATION),
        make_fact("verification_result", loc_result, ENGINE_VERSION),
        make_fact("distance_band", location.get("distance_band"), ENGINE_VERSION),
        make_fact("threshold_meters", location.get("threshold_meters"), ENGINE_VERSION),
        make_fact("project_gps_available", location.get("project_gps_available"), ENGINE_VERSION, kind=EvidenceFactKind.OBSERVATION),
        make_fact("citizen_gps_available", location.get("citizen_gps_available"), ENGINE_VERSION, kind=EvidenceFactKind.OBSERVATION),
    ]
    objects.append(
        EvidenceObject(
            evidence_id=_evidence_id(project.id, SIGNAL_LOCATION, data_mode.value, str(record.citizen_report_id)),
            project_id=project.id,
            signal_type=_signal_enum(SIGNAL_LOCATION),
            finding=f"Citizen location verification is {loc_result}",
            severity=loc_severity,
            score=None,
            confidence=0.34 if loc_result == LOCATION_VERIFIED else 0.18,
            source_type=source_type,
            source_ids=source_ids,
            evidence_facts=loc_facts,
            explanation=str(location.get("reason") or record.rejection_reason or GOVERNANCE_NOTE),
            engine_name=EvidenceEngine.CITIZEN.value,
            engine_version=ENGINE_VERSION,
            data_mode=data_mode,
            provenance=provenance,
            disposition=loc_disposition,
            status=DISPOSITION_TO_STATUS[loc_disposition],
        )
    )
    feedback = record.analysis or {}
    pce = record.plan_claim_evidence or {}
    feedback_flagged = record.submission_status == STATUS_REJECTED or pce.get("result") == PCE_CONTRADICTION
    fb_disposition = EvidenceDisposition.WHY_FLAGGED if feedback_flagged else (
        EvidenceDisposition.INCONCLUSIVE if record.submission_status != "ACCEPTED" else EvidenceDisposition.WHY_NOT_FLAGGED
    )
    objects.append(
        EvidenceObject(
            evidence_id=_evidence_id(project.id, SIGNAL_FEEDBACK, data_mode.value, str(record.citizen_report_id)),
            project_id=project.id,
            signal_type=_signal_enum(SIGNAL_FEEDBACK),
            finding=(
                f"Citizen feedback recorded. Sentiment is {feedback.get('sentiment', 'INCONCLUSIVE')}. "
                "Sentiment is not proof of project quality."
            ),
            severity=EvidenceSeverity.WATCH if pce.get("result") == PCE_CONTRADICTION else EvidenceSeverity.INFO,
            score=None,
            confidence=float(feedback.get("evidence_confidence") or 0.18),
            source_type=source_type,
            source_ids=source_ids,
            evidence_facts=[
                make_fact("citizen_report_id", record.citizen_report_id, ENGINE_VERSION, kind=EvidenceFactKind.OBSERVATION),
                make_fact("satisfaction_rating", record.satisfaction_rating, ENGINE_VERSION, kind=EvidenceFactKind.OBSERVATION),
                make_fact("issue_category", record.issue_category, ENGINE_VERSION, kind=EvidenceFactKind.OBSERVATION),
                make_fact("sentiment", feedback.get("sentiment"), ENGINE_VERSION),
                make_fact("pce_result", pce.get("result"), ENGINE_VERSION),
                make_fact("claim_marked_false", False, ENGINE_VERSION),
            ],
            explanation=str(feedback.get("explanation") or GOVERNANCE_NOTE) + " " + str(pce.get("note") or ""),
            engine_name=EvidenceEngine.CITIZEN.value,
            engine_version=ENGINE_VERSION,
            data_mode=data_mode,
            provenance=provenance,
            disposition=fb_disposition,
            status=DISPOSITION_TO_STATUS[fb_disposition],
        )
    )
    if record.image_id is not None:
        objects.append(
            EvidenceObject(
                evidence_id=_evidence_id(
                    project.id,
                    SIGNAL_IMAGE,
                    data_mode.value,
                    f"{record.citizen_report_id}:{record.image_id}",
                ),
                project_id=project.id,
                signal_type=_signal_enum(SIGNAL_IMAGE),
                finding="Citizen photograph stored as supporting evidence using Image Evidence V1.",
                severity=EvidenceSeverity.WATCH if (record.duplicate or {}).get("flagged") else EvidenceSeverity.INFO,
                score=None,
                confidence=0.28,
                source_type=source_type,
                source_ids=source_ids,
                evidence_facts=[
                    make_fact("citizen_report_id", record.citizen_report_id, ENGINE_VERSION, kind=EvidenceFactKind.OBSERVATION),
                    make_fact("image_id", record.image_id, ENGINE_VERSION, kind=EvidenceFactKind.OBSERVATION),
                    make_fact("image_hash", record.image_hash, ENGINE_VERSION, kind=EvidenceFactKind.OBSERVATION),
                    make_fact("duplicate_flag", (record.duplicate or {}).get("flag"), ENGINE_VERSION),
                    make_fact("original_image_preserved", record.original_image_preserved, ENGINE_VERSION),
                    make_fact("metadata_source", "reported metadata from uploaded file", ENGINE_VERSION, kind=EvidenceFactKind.OBSERVATION),
                ],
                explanation=(
                    "Citizen image stored on the existing photo table. EXIF is reported metadata "
                    "from the uploaded file. The original image is not altered. "
                    + GOVERNANCE_NOTE
                ),
                engine_name=EvidenceEngine.CITIZEN.value,
                engine_version=ENGINE_VERSION,
                data_mode=data_mode,
                provenance=provenance,
                disposition=(
                    EvidenceDisposition.WHY_FLAGGED
                    if (record.duplicate or {}).get("flagged")
                    else EvidenceDisposition.WHY_NOT_FLAGGED
                ),
                status=DISPOSITION_TO_STATUS[
                    EvidenceDisposition.WHY_FLAGGED
                    if (record.duplicate or {}).get("flagged")
                    else EvidenceDisposition.WHY_NOT_FLAGGED
                ],
            )
        )
    return objects


def summary_to_evidence(
    project: Project,
    summary: CitizenSummary,
    *,
    data_mode: DataMode,
    snapshot: DatasetSnapshot | None = None,
) -> EvidenceObject:
    source_type, source_ids, provenance = _base(
        project,
        data_mode=data_mode,
        snapshot=snapshot,
        extra_ids=["citizen_aggregate"],
        extra_notes=(
            f"{GOVERNANCE_NOTE} Aggregate citizen evidence. A single report does not "
            "dominate the project conclusion. Not fused into Investigation Priority."
        ),
    )
    if summary.aggregate_finding == "POTENTIAL_COMMUNITY_CONCERN":
        disposition = EvidenceDisposition.WHY_FLAGGED
        severity = EvidenceSeverity.WATCH
    elif summary.total_submissions == 0:
        disposition = EvidenceDisposition.NOT_ASSESSABLE
        severity = EvidenceSeverity.INFO
    else:
        disposition = EvidenceDisposition.INCONCLUSIVE
        severity = EvidenceSeverity.INFO
    return EvidenceObject(
        evidence_id=_evidence_id(project.id, SIGNAL_AGGREGATE, data_mode.value, "aggregate"),
        project_id=project.id,
        signal_type=_signal_enum(SIGNAL_AGGREGATE),
        finding=(
            f"Citizen aggregate: {summary.aggregate_finding}. "
            f"{summary.sample_size_status}."
        ),
        severity=severity,
        score=None,
        confidence=summary.citizen_evidence_confidence,
        source_type=source_type,
        source_ids=source_ids,
        evidence_facts=[
            make_fact("total_submissions", summary.total_submissions, ENGINE_VERSION, kind=EvidenceFactKind.OBSERVATION),
            make_fact("verified_location_submissions", summary.verified_location_submissions, ENGINE_VERSION, kind=EvidenceFactKind.OBSERVATION),
            make_fact("rejected_submissions", summary.rejected_submissions, ENGINE_VERSION, kind=EvidenceFactKind.OBSERVATION),
            make_fact("average_satisfaction", summary.average_satisfaction, ENGINE_VERSION, kind=EvidenceFactKind.OBSERVATION),
            make_fact("sample_size_status", summary.sample_size_status, ENGINE_VERSION),
            make_fact("aggregate_finding", summary.aggregate_finding, ENGINE_VERSION),
            make_fact("investigation_priority_unchanged", True, ENGINE_VERSION),
        ],
        explanation=summary.explanation,
        engine_name=EvidenceEngine.CITIZEN.value,
        engine_version=ENGINE_VERSION,
        data_mode=data_mode,
        provenance=provenance,
        disposition=disposition,
        status=DISPOSITION_TO_STATUS[disposition],
    )
