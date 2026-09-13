"""Overlap Intelligence V1 → canonical Evidence Object.

Does not change Overlap scoring. Scenario labels are not copied.
"""

from __future__ import annotations

from app.domain.enums import (
    DataMode,
    EvidenceDisposition,
    EvidenceEngine,
    SignalType,
    SourceType,
)
from app.domain.schemas.evidence import EvidenceObject
from app.engines.overlap.constants import ENGINE_NAME, ENGINE_VERSION
from app.engines.overlap.types import OverlapAssessmentOutcome, OverlapIntelligenceResult
from app.evidence.constants import DISPOSITION_TO_STATUS
from app.evidence.facts import confidence_unit, make_fact
from app.evidence.ids import make_evidence_id
from app.evidence.provenance import build_provenance, build_source_ids, resolve_data_mode
from app.models.project import Project
from app.models.snapshot import DatasetSnapshot


def _disposition(outcome: OverlapAssessmentOutcome) -> EvidenceDisposition:
    if outcome in {
        OverlapAssessmentOutcome.POTENTIAL_DUPLICATE,
        OverlapAssessmentOutcome.POTENTIAL_OVERLAP,
    }:
        return EvidenceDisposition.WHY_FLAGGED
    if outcome == OverlapAssessmentOutcome.NOT_LINKED:
        return EvidenceDisposition.WHY_NOT_FLAGGED
    return EvidenceDisposition.INCONCLUSIVE


def _finding(result: OverlapIntelligenceResult) -> str:
    if result.outcome == OverlapAssessmentOutcome.POTENTIAL_DUPLICATE:
        return "Potential Duplicate: high semantic similarity with supporting signals"
    if result.outcome == OverlapAssessmentOutcome.POTENTIAL_OVERLAP:
        return "Potential Overlap: multi-signal similarity above the review threshold"
    if result.outcome == OverlapAssessmentOutcome.INSUFFICIENT_EVIDENCE:
        return "Potential Overlap is inconclusive: blocked candidates are insufficient"
    if result.overlap_score is not None:
        return (
            f"Not linked: best overlap score {result.overlap_score} is below the "
            "Potential Overlap / Potential Duplicate threshold"
        )
    return "Not linked: no Potential Overlap or Potential Duplicate match"


def overlap_result_to_evidence(
    result: OverlapIntelligenceResult,
    project: Project,
    *,
    snapshot: DatasetSnapshot | None = None,
) -> EvidenceObject:
    data_mode = resolve_data_mode(
        is_synthetic=bool(project.is_synthetic),
        engine_mode=result.overlap_mode.value,
    )
    source_type = (
        SourceType.SYNTHETIC_TEST_RECORD
        if data_mode == DataMode.SYNTHETIC
        else SourceType.HYBRID_ENRICHMENT
        if data_mode == DataMode.HYBRID
        else SourceType.MPLADS_PROJECT_RECORD
    )
    extra_ids = [item.linked_internal_project_id for item in result.matches]
    source_ids = build_source_ids(result.internal_project_id, extra_ids)
    provenance = build_provenance(
        project,
        data_mode=data_mode,
        source_type=source_type,
        source_ids=source_ids,
        snapshot=snapshot,
    )
    derived = ENGINE_VERSION
    facts = [
        make_fact("source_work", result.source_work, "project.source_work"),
        make_fact("work_description", result.work_description, "project.work_description"),
        make_fact("observed_category", result.observed_category, "project.category"),
        make_fact("constituency", result.constituency, "project.constituency"),
        make_fact("signal_kind", result.signal_kind, derived),
        make_fact("outcome", result.outcome.value, derived),
        make_fact("flagged", result.flagged, derived),
        make_fact("overlap_score", result.overlap_score, derived),
        make_fact("evidence_confidence", result.evidence_confidence, derived),
        make_fact("candidate_count", result.candidate_count, derived),
        make_fact("match_count", result.match_count, derived),
        make_fact("embedding_backend", result.embedding_backend, derived),
        make_fact("blocking_strategy", result.blocking_strategy, derived),
        make_fact("geographic_evidence_available", result.geographic_evidence_available, derived),
        make_fact("gps_used", result.gps_used, derived),
        make_fact("why_linked", result.why_linked, derived),
        make_fact("why_not_linked", result.why_not_linked, derived),
        make_fact("overlap_mode", result.overlap_mode.value, derived),
        make_fact("dataset_type", result.dataset_type, derived),
        make_fact("data_mode", data_mode.value, derived),
    ]
    matches = [
        {
            "linked_project_id": item.linked_project_id,
            "linked_internal_project_id": item.linked_internal_project_id,
            "semantic_similarity": item.semantic_similarity,
            "category_match": item.category_match,
            "constituency_match": item.constituency_match,
            "amount_similarity": item.amount_similarity,
            "date_proximity": item.date_proximity,
            "location_similarity": item.location_similarity,
            "gps_distance_m": item.gps_distance_m,
            "overall_overlap_score": item.overall_overlap_score,
            "evidence_confidence": item.evidence_confidence,
            "outcome": item.outcome.value,
            "reasons": list(item.reasons),
        }
        for item in result.matches
    ]
    disposition = _disposition(result.outcome)
    return EvidenceObject(
        evidence_id=make_evidence_id(
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            project_id=result.project_id,
            signal_type=result.signal_kind,
            data_mode=data_mode.value,
        ),
        project_id=result.project_id,
        signal_type=SignalType.POTENTIAL_OVERLAP,
        finding=_finding(result),
        severity=result.severity,
        score=result.overlap_score,
        confidence=confidence_unit(result.evidence_confidence),
        source_type=source_type,
        source_ids=source_ids,
        evidence_facts=facts,
        explanation=result.explanation,
        engine_name=EvidenceEngine.OVERLAP,
        engine_version=ENGINE_VERSION,
        data_mode=data_mode,
        provenance=provenance,
        disposition=disposition,
        status=DISPOSITION_TO_STATUS[disposition],
        comparables=matches,
    )
