"""Geospatial Consistency V1 → canonical Evidence Object V1.

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
from app.engines.geo.constants import (
    ENGINE_NAME,
    ENGINE_VERSION,
    INCONCLUSIVE,
    LOCATION_CONSISTENT,
    LOCATION_MISMATCH,
)
from app.engines.geo.types import GeospatialResult, ImageConsistency
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
    return SourceType.GEOSPATIAL_RECORD


def _signal_for(result: str) -> SignalType:
    if result == LOCATION_CONSISTENT:
        return SignalType.GEOSPATIAL_LOCATION_CONSISTENCY
    if result == LOCATION_MISMATCH:
        return SignalType.GEOSPATIAL_LOCATION_MISMATCH
    return SignalType.GEOSPATIAL_INCONCLUSIVE


def _disposition(result: str) -> EvidenceDisposition:
    if result == LOCATION_MISMATCH:
        return EvidenceDisposition.WHY_FLAGGED
    if result == LOCATION_CONSISTENT:
        return EvidenceDisposition.WHY_NOT_FLAGGED
    return EvidenceDisposition.INCONCLUSIVE


def _severity(result: str) -> EvidenceSeverity:
    if result == LOCATION_MISMATCH:
        return EvidenceSeverity.WATCH
    return EvidenceSeverity.INFO


def _evidence_id(project_id: int, signal: str, data_mode: str, digest_key: str) -> str:
    payload = "|".join(
        [ENGINE_NAME, ENGINE_VERSION, str(project_id), signal, data_mode, digest_key]
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"ev:{ENGINE_NAME}:{project_id}:{signal}:{data_mode}:{digest}"


def _base_facts(result: GeospatialResult, image: ImageConsistency | None = None) -> list:
    source = ENGINE_VERSION
    facts = [
        make_fact("project_id", result.project_id, source, kind=EvidenceFactKind.OBSERVATION),
        make_fact(
            "project_location",
            result.project_location.as_dict(),
            result.project_location.source,
            kind=EvidenceFactKind.OBSERVATION,
        ),
        make_fact("threshold_meters", result.threshold_meters, source),
        make_fact("location_consistency", result.location_consistency, source),
        make_fact("data_mode", result.data_mode.value, source, kind=EvidenceFactKind.OBSERVATION),
        make_fact("satellite", result.satellite.as_dict(), ENGINE_VERSION),
    ]
    if image is not None:
        facts.extend(
            [
                make_fact("image_id", image.image_id, f"image:{image.image_id}", kind=EvidenceFactKind.OBSERVATION),
                make_fact(
                    "image_gps",
                    image.location.as_dict(),
                    image.location.source,
                    kind=EvidenceFactKind.OBSERVATION,
                ),
                make_fact("distance_meters", image.distance_meters, ENGINE_VERSION),
                make_fact("distance_km", image.distance_km, ENGINE_VERSION),
                make_fact("image_result", image.result, ENGINE_VERSION),
            ]
        )
    else:
        facts.append(make_fact("summary", result.summary.as_dict(), ENGINE_VERSION))
        facts.append(
            make_fact(
                "mixed_results",
                result.summary.mixed_results,
                ENGINE_VERSION,
                statement="One matching image does not make every other image trustworthy."
                if result.summary.mixed_results
                else None,
            )
        )
    return facts


def result_to_evidence_objects(
    project: Project,
    result: GeospatialResult,
    *,
    snapshot: DatasetSnapshot | None = None,
) -> list[EvidenceObject]:
    source_type = _source_type(result.data_mode)
    extra_ids = [f"image:{item.image_id}" for item in result.images]
    source_ids = build_source_ids(project.internal_project_id, extra_ids)
    extra_notes = (
        "Location consistency check only. Image GPS is reported metadata from the uploaded file. "
        "This does not prove authenticity, completion, or that the photograph depicts the claimed work."
    )
    if result.project_location.synthetic:
        extra_notes = f"{extra_notes} SYNTHETIC project coordinates. Not official MPLADS GPS."
    provenance = build_provenance(
        project,
        data_mode=result.data_mode,
        source_type=source_type,
        source_ids=source_ids,
        snapshot=snapshot,
        extra_notes=extra_notes,
    )
    objects: list[EvidenceObject] = []

    overall_signal = _signal_for(result.overall_result)
    overall_disposition = _disposition(result.overall_result)
    objects.append(
        EvidenceObject(
            evidence_id=_evidence_id(
                result.project_id,
                overall_signal.value,
                result.data_mode.value,
                "summary",
            ),
            project_id=result.project_id,
            signal_type=overall_signal,
            finding=result.overall_result,
            severity=_severity(result.overall_result),
            score=None if result.overall_result == INCONCLUSIVE else (
                0.0
                if result.overall_result == LOCATION_CONSISTENT
                else next((item.score for item in result.images if item.score), 70.0)
            ),
            confidence=result.evidence_confidence,
            source_type=source_type,
            source_ids=source_ids,
            evidence_facts=_base_facts(result),
            explanation=result.explanation,
            engine_name=EvidenceEngine.GEO.value,
            engine_version=ENGINE_VERSION,
            data_mode=result.data_mode,
            provenance=provenance,
            disposition=overall_disposition,
            status=DISPOSITION_TO_STATUS[overall_disposition],
        )
    )

    for image in result.images:
        signal = _signal_for(image.result)
        disposition = _disposition(image.result)
        image_ids = build_source_ids(project.internal_project_id, [f"image:{image.image_id}"])
        objects.append(
            EvidenceObject(
                evidence_id=_evidence_id(
                    result.project_id,
                    signal.value,
                    result.data_mode.value,
                    f"image:{image.image_id}",
                ),
                project_id=result.project_id,
                signal_type=signal,
                finding=image.finding,
                severity=_severity(image.result),
                score=image.score,
                confidence=image.confidence,
                source_type=source_type,
                source_ids=image_ids,
                evidence_facts=_base_facts(result, image),
                explanation=image.explanation,
                engine_name=EvidenceEngine.GEO.value,
                engine_version=ENGINE_VERSION,
                data_mode=result.data_mode,
                provenance=build_provenance(
                    project,
                    data_mode=result.data_mode,
                    source_type=source_type,
                    source_ids=image_ids,
                    snapshot=snapshot,
                    extra_notes=extra_notes,
                ),
                disposition=disposition,
                status=DISPOSITION_TO_STATUS[disposition],
            )
        )
    return objects
