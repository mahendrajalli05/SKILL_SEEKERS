"""Image Evidence V1 → canonical Evidence Object V1.

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
from app.engines.image.constants import (
    ENGINE_NAME,
    ENGINE_VERSION,
    EXACT_DUPLICATE_CONFIDENCE,
    METADATA_CONFIDENCE,
    QUALITY_CONFIDENCE,
    UNAVAILABLE_CONFIDENCE,
)
from app.engines.image.explain import (
    duplicate_explanation,
    duplicate_finding,
    metadata_explanation,
    metadata_finding,
    quality_explanation,
    quality_finding,
)
from app.engines.image.types import ImageAnalysis
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


def _base_facts(analysis: ImageAnalysis) -> list:
    source = f"image:{analysis.image_id}"
    return [
        make_fact("image_id", analysis.image_id, source, kind=EvidenceFactKind.OBSERVATION),
        make_fact("project_id", analysis.project_id, source, kind=EvidenceFactKind.OBSERVATION),
        make_fact("content_sha256", analysis.content_sha256, source, kind=EvidenceFactKind.OBSERVATION),
        make_fact("ahash", analysis.ahash, ENGINE_VERSION),
        make_fact("dhash", analysis.dhash, ENGINE_VERSION),
        make_fact("phash", analysis.phash, ENGINE_VERSION),
        make_fact("integrity_status", analysis.integrity_status, ENGINE_VERSION),
        make_fact("data_mode", analysis.data_mode.value, ENGINE_VERSION, kind=EvidenceFactKind.OBSERVATION),
        make_fact(
            "advanced_authenticity",
            analysis.authenticity.as_dict(),
            ENGINE_VERSION,
        ),
    ]


def analysis_to_evidence_objects(
    project: Project,
    analysis: ImageAnalysis,
    *,
    snapshot: DatasetSnapshot | None = None,
) -> list[EvidenceObject]:
    source_type = _source_type(analysis.data_mode)
    source_ids = build_source_ids(
        project.internal_project_id,
        [f"image:{analysis.image_id}", *(f"image:{item.matched_image_id}" for item in analysis.exact_matches + analysis.reuse_matches)],
    )
    extra_notes = (
        "Officer-uploaded photograph. Reported EXIF is not independently verified. "
        "This is supporting evidence only and not an official government photograph merely because it was uploaded."
    )
    if analysis.data_mode == DataMode.SYNTHETIC:
        extra_notes = f"{extra_notes} SYNTHETIC test fixture. Not a government project."
    elif analysis.data_mode == DataMode.HYBRID:
        extra_notes = f"{extra_notes} HYBRID/TEST image context. Synthetic images are not official photographs."
    provenance = build_provenance(
        project,
        data_mode=analysis.data_mode,
        source_type=source_type,
        source_ids=source_ids,
        snapshot=snapshot,
        extra_notes=extra_notes,
    )
    base_facts = _base_facts(analysis)
    objects: list[EvidenceObject] = []

    dup_disposition = (
        EvidenceDisposition.WHY_FLAGGED
        if analysis.exact_duplicate or analysis.potential_reuse
        else EvidenceDisposition.WHY_NOT_FLAGGED
    )
    dup_severity = EvidenceSeverity.WATCH if analysis.exact_duplicate or analysis.potential_reuse else EvidenceSeverity.INFO
    dup_signal = (
        SignalType.IMAGE_EXACT_DUPLICATE
        if analysis.exact_duplicate
        else SignalType.IMAGE_POTENTIAL_REUSE
        if analysis.potential_reuse
        else SignalType.IMAGE_POTENTIAL_REUSE
    )
    dup_confidence = (
        EXACT_DUPLICATE_CONFIDENCE
        if analysis.exact_duplicate
        else (analysis.reuse_matches[0].confidence if analysis.reuse_matches else UNAVAILABLE_CONFIDENCE)
    )
    dup_facts = list(base_facts)
    if analysis.exact_matches:
        dup_facts.append(make_fact("exact_matches", [item.as_dict() for item in analysis.exact_matches], ENGINE_VERSION))
    if analysis.reuse_matches:
        dup_facts.append(make_fact("reuse_matches", [item.as_dict() for item in analysis.reuse_matches], ENGINE_VERSION))
    objects.append(
        EvidenceObject(
            evidence_id=_evidence_id(
                project.id,
                analysis.image_id,
                dup_signal.value,
                analysis.data_mode.value,
                analysis.content_sha256,
            ),
            project_id=project.id,
            signal_type=dup_signal,
            finding=duplicate_finding(analysis),
            severity=dup_severity,
            score=None,
            confidence=dup_confidence,
            source_type=source_type,
            source_ids=source_ids,
            evidence_facts=dup_facts,
            explanation=duplicate_explanation(analysis),
            engine_name=EvidenceEngine.IMAGE.value,
            engine_version=ENGINE_VERSION,
            data_mode=analysis.data_mode,
            provenance=provenance,
            disposition=dup_disposition,
            status=DISPOSITION_TO_STATUS[dup_disposition],
        )
    )

    meta_available = analysis.gps_available or bool(analysis.capture_timestamp)
    meta_disposition = EvidenceDisposition.INCONCLUSIVE
    meta_facts = list(base_facts)
    for item in analysis.metadata_fields:
        meta_facts.append(
            make_fact(
                item.field,
                item.as_dict(),
                item.source,
                kind=EvidenceFactKind.OBSERVATION,
            )
        )
    objects.append(
        EvidenceObject(
            evidence_id=_evidence_id(
                project.id,
                analysis.image_id,
                SignalType.IMAGE_METADATA.value,
                analysis.data_mode.value,
                str(analysis.metadata_status),
            ),
            project_id=project.id,
            signal_type=SignalType.IMAGE_METADATA,
            finding=metadata_finding(analysis),
            severity=EvidenceSeverity.INFO,
            score=None,
            confidence=METADATA_CONFIDENCE if meta_available else UNAVAILABLE_CONFIDENCE,
            source_type=source_type,
            source_ids=source_ids,
            evidence_facts=meta_facts,
            explanation=metadata_explanation(analysis),
            engine_name=EvidenceEngine.IMAGE.value,
            engine_version=ENGINE_VERSION,
            data_mode=analysis.data_mode,
            provenance=provenance,
            disposition=meta_disposition,
            status=DISPOSITION_TO_STATUS[meta_disposition],
        )
    )

    quality_readable = bool((analysis.quality or {}).get("readable"))
    quality_warnings = list((analysis.quality or {}).get("warnings") or [])
    quality_disposition = EvidenceDisposition.INCONCLUSIVE
    quality_facts = list(base_facts)
    quality_facts.append(make_fact("quality", analysis.quality, ENGINE_VERSION))
    objects.append(
        EvidenceObject(
            evidence_id=_evidence_id(
                project.id,
                analysis.image_id,
                SignalType.IMAGE_QUALITY.value,
                analysis.data_mode.value,
                str((analysis.quality or {}).get("width")) + str(quality_readable),
            ),
            project_id=project.id,
            signal_type=SignalType.IMAGE_QUALITY,
            finding=quality_finding(analysis),
            severity=EvidenceSeverity.INFO,
            score=None,
            confidence=QUALITY_CONFIDENCE if quality_readable else UNAVAILABLE_CONFIDENCE,
            source_type=source_type,
            source_ids=source_ids,
            evidence_facts=quality_facts,
            explanation=quality_explanation(analysis),
            engine_name=EvidenceEngine.IMAGE.value,
            engine_version=ENGINE_VERSION,
            data_mode=analysis.data_mode,
            provenance=provenance,
            disposition=quality_disposition,
            status=DISPOSITION_TO_STATUS[quality_disposition],
        )
    )
    _ = quality_warnings
    return objects
