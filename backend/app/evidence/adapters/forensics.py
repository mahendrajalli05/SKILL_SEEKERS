"""Image Forensics V1 → canonical Evidence Object V1.

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
from app.engines.forensics.constants import (
    ENGINE_NAME,
    ENGINE_VERSION,
    INCONCLUSIVE,
    METADATA_ANOMALY,
    POTENTIAL_MANIPULATION,
    REVIEW_REQUIRED,
    TEST_WATERMARK,
)
from app.engines.forensics.types import ForensicResult, ForensicSignal
from app.evidence.constants import DISPOSITION_TO_STATUS
from app.evidence.facts import make_fact
from app.evidence.provenance import build_provenance, build_source_ids
from app.models.project import Project
from app.models.snapshot import DatasetSnapshot


def _source_type(data_mode: DataMode) -> SourceType:
    if data_mode == DataMode.SYNTHETIC:
        return SourceType.SYNTHETIC_TEST_RECORD
    if data_mode == DataMode.HYBRID:
        return SourceType.HYBRID_ENRICHMENT
    return SourceType.IMAGE_ARTIFACT


def _evidence_id(project_id: int, image_id: int, signal: str, data_mode: str, digest_key: str) -> str:
    payload = "|".join(
        [ENGINE_NAME, ENGINE_VERSION, str(project_id), str(image_id), signal, data_mode, digest_key]
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"ev:{ENGINE_NAME}:{project_id}:{signal}:{data_mode}:{digest}"


def _disposition(result: str) -> EvidenceDisposition:
    if result in {
        POTENTIAL_MANIPULATION,
        METADATA_ANOMALY,
        "EXACT_DUPLICATE",
        "POTENTIAL_IMAGE_REUSE",
        REVIEW_REQUIRED,
    }:
        return EvidenceDisposition.WHY_FLAGGED
    if result in {"NO_STRONG_FORENSIC_SIGNAL", "UNIQUE", "TIMESTAMP_AVAILABLE"}:
        return EvidenceDisposition.WHY_NOT_FLAGGED
    return EvidenceDisposition.INCONCLUSIVE


def _severity(result: str) -> EvidenceSeverity:
    if result in {POTENTIAL_MANIPULATION, METADATA_ANOMALY, REVIEW_REQUIRED}:
        return EvidenceSeverity.WATCH
    return EvidenceSeverity.INFO


def _base_facts(result: ForensicResult) -> list:
    source = f"image:{result.image_id}"
    return [
        make_fact("image_id", result.image_id, source, kind=EvidenceFactKind.OBSERVATION),
        make_fact("project_id", result.project_id, source, kind=EvidenceFactKind.OBSERVATION),
        make_fact("content_sha256", result.content_sha256, source, kind=EvidenceFactKind.OBSERVATION),
        make_fact("data_mode", result.data_mode.value, ENGINE_VERSION, kind=EvidenceFactKind.OBSERVATION),
        make_fact("overall_assessment", result.overall_assessment, ENGINE_VERSION),
        make_fact("bytes_unmodified", result.bytes_unmodified, ENGINE_VERSION),
        make_fact("external_transmission", False, ENGINE_VERSION),
        make_fact("prototype_assessment_label", result.prototype_assessment_label, ENGINE_VERSION),
    ]


def _object_for_signal(
    project: Project,
    result: ForensicResult,
    *,
    signal_type: SignalType,
    signal: ForensicSignal,
    provenance,
    source_type: SourceType,
    source_ids: list[str],
) -> EvidenceObject:
    disposition = _disposition(signal.result)
    facts = list(_base_facts(result))
    facts.append(make_fact("signal_result", signal.as_dict(), ENGINE_VERSION))
    finding = f"{signal.result}: {signal.findings[0]}" if signal.findings else signal.result
    explanation = " ".join([result.explanation, *signal.findings, *signal.notes])
    return EvidenceObject(
        evidence_id=_evidence_id(
            project.id,
            result.image_id,
            signal_type.value,
            result.data_mode.value,
            f"{signal.result}:{result.content_sha256 or ''}",
        ),
        project_id=project.id,
        signal_type=signal_type,
        finding=finding,
        severity=_severity(signal.result),
        score=None,
        confidence=signal.confidence,
        source_type=source_type,
        source_ids=source_ids,
        evidence_facts=facts,
        explanation=explanation,
        engine_name=EvidenceEngine.FORENSICS.value,
        engine_version=ENGINE_VERSION,
        data_mode=result.data_mode,
        provenance=provenance,
        disposition=disposition,
        status=DISPOSITION_TO_STATUS[disposition],
    )


def result_to_evidence_objects(
    project: Project,
    result: ForensicResult,
    *,
    snapshot: DatasetSnapshot | None = None,
) -> list[EvidenceObject]:
    source_type = _source_type(result.data_mode)
    source_ids = build_source_ids(project.internal_project_id, [f"image:{result.image_id}"])
    extra_notes = (
        "Image Forensics V1 on an Image Evidence V1 photograph. "
        "Prototype forensic assessment — not a validated authenticity decision. "
        "Missing EXIF is not proof of manipulation."
    )
    if result.data_mode == DataMode.SYNTHETIC:
        extra_notes = f"{extra_notes} {TEST_WATERMARK}"
    elif result.data_mode == DataMode.HYBRID:
        extra_notes = (
            f"{extra_notes} HYBRID/TEST image context. "
            "Synthetic images are not official photographs."
        )
    provenance = build_provenance(
        project,
        data_mode=result.data_mode,
        source_type=source_type,
        source_ids=source_ids,
        snapshot=snapshot,
        extra_notes=extra_notes,
    )
    objects = [
        _object_for_signal(
            project,
            result,
            signal_type=SignalType.IMAGE_FORENSIC_MANIPULATION,
            signal=result.manipulation_signal,
            provenance=provenance,
            source_type=source_type,
            source_ids=source_ids,
        ),
        _object_for_signal(
            project,
            result,
            signal_type=SignalType.IMAGE_FORENSIC_AI_GENERATION,
            signal=result.ai_generation_signal,
            provenance=provenance,
            source_type=source_type,
            source_ids=source_ids,
        ),
        _object_for_signal(
            project,
            result,
            signal_type=SignalType.IMAGE_FORENSIC_METADATA,
            signal=result.metadata_signal,
            provenance=provenance,
            source_type=source_type,
            source_ids=source_ids,
        ),
    ]
    if result.overall_assessment == INCONCLUSIVE:
        inconclusive = ForensicSignal(
            name="overall",
            result=INCONCLUSIVE,
            confidence_label=INCONCLUSIVE,
            confidence=result.evidence_confidence,
            available=False,
            findings=["Forensic assessment is INCONCLUSIVE on currently available signals."],
            notes=["Insufficient independent forensic evidence for a stronger review signal."],
        )
        objects.append(
            _object_for_signal(
                project,
                result,
                signal_type=SignalType.IMAGE_FORENSIC_INCONCLUSIVE,
                signal=inconclusive,
                provenance=provenance,
                source_type=source_type,
                source_ids=source_ids,
            )
        )
    return objects
