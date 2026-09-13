"""Satellite / Remote-Sensing Consistency V1 → canonical Evidence Object V1.

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
from app.engines.satellite.constants import (
    ENGINE_NAME,
    ENGINE_VERSION,
    EVIDENCE_AVAILABILITY,
    EVIDENCE_CHANGE,
    EVIDENCE_INCONCLUSIVE,
    EVIDENCE_LOCATION,
    EVIDENCE_TEMPORAL,
    SATELLITE_CONSISTENT,
    SATELLITE_INCONCLUSIVE,
    SATELLITE_INCONSISTENT,
    SATELLITE_UNAVAILABLE,
)
from app.engines.satellite.types import SatelliteResult
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
    return SourceType.SATELLITE_OBSERVATION


def _disposition(result: str) -> EvidenceDisposition:
    if result == SATELLITE_INCONSISTENT:
        return EvidenceDisposition.WHY_FLAGGED
    if result == SATELLITE_CONSISTENT:
        return EvidenceDisposition.WHY_NOT_FLAGGED
    if result == SATELLITE_UNAVAILABLE:
        return EvidenceDisposition.NOT_ASSESSABLE
    return EvidenceDisposition.INCONCLUSIVE


def _severity(result: str) -> EvidenceSeverity:
    if result == SATELLITE_INCONSISTENT:
        return EvidenceSeverity.WATCH
    return EvidenceSeverity.INFO


def _evidence_id(project_id: int, signal: str, data_mode: str, digest_key: str) -> str:
    payload = "|".join(
        [ENGINE_NAME, ENGINE_VERSION, str(project_id), signal, data_mode, digest_key]
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"ev:{ENGINE_NAME}:{project_id}:{signal}:{data_mode}:{digest}"


def _base_facts(result: SatelliteResult) -> list:
    source = ENGINE_VERSION
    facts = [
        make_fact("project_id", result.project_id, source, kind=EvidenceFactKind.OBSERVATION),
        make_fact("provider", result.provider, source, kind=EvidenceFactKind.OBSERVATION),
        make_fact("imagery_available", result.imagery_available, source, kind=EvidenceFactKind.OBSERVATION),
        make_fact("acquisition_date", result.acquisition_date, source, kind=EvidenceFactKind.OBSERVATION),
        make_fact(
            "spatial_resolution_m",
            result.spatial_resolution_m,
            source,
            kind=EvidenceFactKind.OBSERVATION,
        ),
        make_fact("image_reference", [item.get("image_reference") for item in result.scenes], source),
        make_fact("overall_result", result.overall_result, source),
        make_fact("finding", result.finding, source),
        make_fact("data_mode", result.data_mode.value, source, kind=EvidenceFactKind.OBSERVATION),
        make_fact("labelled_synthetic", result.labelled_synthetic, source, kind=EvidenceFactKind.OBSERVATION),
        make_fact("official_imagery", result.official_imagery, source, kind=EvidenceFactKind.OBSERVATION),
        make_fact("project_location", result.project_location, source, kind=EvidenceFactKind.OBSERVATION),
        make_fact("work_scale", result.work_scale, source),
    ]
    if result.location_analysis:
        facts.append(make_fact("location_analysis", result.location_analysis, source))
    if result.temporal_analysis:
        facts.append(make_fact("temporal_analysis", result.temporal_analysis, source))
    if result.change_analysis:
        facts.append(make_fact("change_analysis", result.change_analysis, source))
    if result.resolution_analysis:
        facts.append(make_fact("resolution_analysis", result.resolution_analysis, source))
    return facts


def _object(
    project: Project,
    result: SatelliteResult,
    *,
    signal_type: SignalType,
    finding: str,
    explanation: str,
    result_code: str,
    digest_key: str,
    provenance,
    source_type: SourceType,
    source_ids: list[str],
) -> EvidenceObject:
    disposition = _disposition(result_code)
    return EvidenceObject(
        evidence_id=_evidence_id(
            result.project_id,
            signal_type.value,
            result.data_mode.value,
            digest_key,
        ),
        project_id=result.project_id,
        signal_type=signal_type,
        finding=finding,
        severity=_severity(result_code),
        score=None,
        confidence=result.evidence_confidence,
        source_type=source_type,
        source_ids=source_ids,
        evidence_facts=_base_facts(result),
        explanation=explanation,
        engine_name=EvidenceEngine.SATELLITE.value,
        engine_version=ENGINE_VERSION,
        data_mode=result.data_mode,
        provenance=provenance,
        disposition=disposition,
        status=DISPOSITION_TO_STATUS[disposition],
    )


def result_to_evidence_objects(
    project: Project,
    result: SatelliteResult,
    *,
    snapshot: DatasetSnapshot | None = None,
) -> list[EvidenceObject]:
    source_type = _source_type(result.data_mode)
    refs = [str(item.get("image_reference")) for item in result.scenes if item.get("image_reference")]
    source_ids = build_source_ids(project.internal_project_id, [result.provider, *refs])
    extra_notes = (
        "Satellite / Remote-Sensing Consistency V1. "
        "Decision-support imagery evidence only. Not a legal finding and not proof of "
        "completion, physical measurements, or authenticity."
    )
    if result.labelled_synthetic:
        extra_notes = (
            f"{extra_notes} TEST/SYNTHETIC mocked provider metadata. "
            "Not official government or commercial satellite imagery."
        )
    if result.official_imagery is False:
        extra_notes = f"{extra_notes} Official imagery was not used."
    provenance = build_provenance(
        project,
        data_mode=result.data_mode,
        source_type=source_type,
        source_ids=source_ids,
        snapshot=snapshot,
        extra_notes=extra_notes,
    )
    objects = [
        _object(
            project,
            result,
            signal_type=SignalType.SATELLITE_AVAILABILITY,
            finding=f"{EVIDENCE_AVAILABILITY}: {'available' if result.imagery_available else 'unavailable'}",
            explanation=str(result.availability.get("reason") or result.explanation),
            result_code=result.overall_result if result.imagery_available else SATELLITE_UNAVAILABLE,
            digest_key="availability",
            provenance=provenance,
            source_type=source_type,
            source_ids=source_ids,
        )
    ]
    if result.location_analysis:
        objects.append(
            _object(
                project,
                result,
                signal_type=SignalType.SATELLITE_LOCATION,
                finding=str(result.location_analysis.get("finding") or EVIDENCE_LOCATION),
                explanation=str(result.location_analysis.get("explanation") or result.explanation),
                result_code=str(result.location_analysis.get("result") or SATELLITE_INCONCLUSIVE),
                digest_key="location",
                provenance=provenance,
                source_type=source_type,
                source_ids=source_ids,
            )
        )
    if result.change_analysis:
        objects.append(
            _object(
                project,
                result,
                signal_type=SignalType.SATELLITE_CHANGE,
                finding=str(result.change_analysis.get("finding") or EVIDENCE_CHANGE),
                explanation=str(result.change_analysis.get("explanation") or result.explanation),
                result_code=str(result.change_analysis.get("result") or SATELLITE_INCONCLUSIVE),
                digest_key="change",
                provenance=provenance,
                source_type=source_type,
                source_ids=source_ids,
            )
        )
    if result.temporal_analysis:
        objects.append(
            _object(
                project,
                result,
                signal_type=SignalType.SATELLITE_TEMPORAL,
                finding=str(result.temporal_analysis.get("finding") or EVIDENCE_TEMPORAL),
                explanation=str(result.temporal_analysis.get("explanation") or result.explanation),
                result_code=str(result.temporal_analysis.get("result") or SATELLITE_INCONCLUSIVE),
                digest_key="temporal",
                provenance=provenance,
                source_type=source_type,
                source_ids=source_ids,
            )
        )
    if result.overall_result in {SATELLITE_INCONCLUSIVE, SATELLITE_UNAVAILABLE}:
        objects.append(
            _object(
                project,
                result,
                signal_type=SignalType.SATELLITE_INCONCLUSIVE,
                finding=f"{EVIDENCE_INCONCLUSIVE}: {result.finding}",
                explanation=result.explanation,
                result_code=result.overall_result,
                digest_key="inconclusive",
                provenance=provenance,
                source_type=source_type,
                source_ids=source_ids,
            )
        )
    return objects
