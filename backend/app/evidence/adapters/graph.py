"""Relationship Graph V1 → canonical Evidence Object.

Does not change Overlap scoring or Risk Fusion. Scenario labels are not copied.
"""

from __future__ import annotations

from app.domain.enums import (
    DataMode,
    EvidenceDisposition,
    EvidenceEngine,
    EvidenceFactKind,
    SignalType,
    SourceType,
)
from app.domain.schemas.evidence import EvidenceObject
from app.engines.graph.constants import ENGINE_NAME, ENGINE_VERSION
from app.engines.graph.types import GraphFindingKind, GraphIntelligenceResult, GraphMode
from app.evidence.constants import DISPOSITION_TO_STATUS
from app.evidence.facts import confidence_unit, make_fact
from app.evidence.ids import make_evidence_id
from app.evidence.provenance import build_provenance, build_source_ids
from app.models.project import Project
from app.models.snapshot import DatasetSnapshot


def _disposition(kind: GraphFindingKind) -> EvidenceDisposition:
    if kind == GraphFindingKind.POTENTIAL_PATTERN_OF_INTEREST:
        return EvidenceDisposition.WHY_FLAGGED
    if kind == GraphFindingKind.INSUFFICIENT_EVIDENCE:
        return EvidenceDisposition.INCONCLUSIVE
    return EvidenceDisposition.WHY_NOT_FLAGGED


def graph_result_to_evidence(
    result: GraphIntelligenceResult,
    project: Project,
    *,
    snapshot: DatasetSnapshot | None = None,
) -> EvidenceObject:
    data_mode = (
        DataMode.SYNTHETIC
        if bool(project.is_synthetic)
        else DataMode.HYBRID
        if result.graph_mode == GraphMode.HYBRID_TEST
        else DataMode.REAL
    )
    source_type = (
        SourceType.SYNTHETIC_TEST_RECORD
        if data_mode == DataMode.SYNTHETIC
        else SourceType.HYBRID_ENRICHMENT
        if data_mode == DataMode.HYBRID
        else SourceType.MPLADS_PROJECT_RECORD
    )
    extra_ids = [
        node.internal_project_id
        for node in result.connected_nodes
        if node.internal_project_id
    ]
    source_ids = build_source_ids(result.internal_project_id, extra_ids)
    extra_notes = None
    if result.graph_mode == GraphMode.HYBRID_TEST:
        extra_notes = (
            "HYBRID/TEST graph: SIMILAR_TO may use Overlap GPS proximity. "
            "GPS is not a REAL graph node or edge type."
        )
    provenance = build_provenance(
        project,
        data_mode=data_mode,
        source_type=source_type,
        source_ids=source_ids,
        snapshot=snapshot,
        extra_notes=extra_notes,
    )
    derived = ENGINE_VERSION
    stats = result.stats
    facts = [
        make_fact("mp_name", result.mp_name, "project.mp_name", kind=EvidenceFactKind.OBSERVATION),
        make_fact("observed_category", result.category, "project.category"),
        make_fact("constituency", result.constituency, "project.constituency"),
        make_fact("ida", result.ida, "project.ida"),
        make_fact("state", result.state, "project.state", kind=EvidenceFactKind.OBSERVATION),
        make_fact("signal_kind", result.signal_kind, derived),
        make_fact("finding_kind", result.finding_kind.value, derived),
        make_fact("flagged", result.flagged, derived),
        make_fact("graph_score", result.graph_score, derived),
        make_fact("evidence_confidence", result.evidence_confidence, derived),
        make_fact("connected_project_count", stats.connected_project_count, derived),
        make_fact("similar_project_count", stats.similar_project_count, derived),
        make_fact("same_constituency_count", stats.same_constituency_count, derived),
        make_fact("same_category_count", stats.same_category_count, derived),
        make_fact("same_ida_count", stats.same_ida_count, derived),
        make_fact("ida_associated_project_count", stats.ida_associated_project_count, derived),
        make_fact("cluster_size", stats.cluster_size, derived),
        make_fact("independent_signal_count", stats.independent_signal_count, derived),
        make_fact("independent_signals", list(stats.independent_signals), derived),
        make_fact("strongest_relationship", stats.strongest_relationship, derived),
        make_fact("candidate_strategy", result.candidate_strategy, derived),
        make_fact("graph_mode", result.graph_mode.value, derived),
        make_fact("dataset_type", result.dataset_type, derived),
        make_fact("data_mode", data_mode.value, derived),
        make_fact("gps_used", result.gps_used, derived),
        make_fact("why_flagged", result.why_flagged, derived),
        make_fact("why_not_flagged", result.why_not_flagged, derived),
    ]
    comparables = []
    for rel in result.relationships:
        if rel.edge_type.value != "SIMILAR_TO":
            continue
        if rel.from_project_id and rel.to_project_id and rel.from_project_id > rel.to_project_id:
            continue
        item = {
            "from_project_id": rel.from_project_id,
            "to_project_id": rel.to_project_id,
            "edge_type": rel.edge_type.value,
            "strength": rel.strength,
            "similarity_score": rel.similarity_score,
            "semantic_similarity": rel.semantic_similarity,
            "same_constituency": rel.same_constituency,
            "same_category": rel.same_category,
            "same_ida": rel.same_ida,
            "similar_allocation": rel.similar_allocation,
            "close_recommendation_dates": rel.close_recommendation_dates,
            "date_gap_days": rel.date_gap_days,
            "overlap_outcome": rel.overlap_outcome,
        }
        if result.graph_mode == GraphMode.HYBRID_TEST and rel.gps_distance_m is not None:
            item["gps_distance_m"] = rel.gps_distance_m
        comparables.append(item)
    disposition = _disposition(result.finding_kind)
    return EvidenceObject(
        evidence_id=make_evidence_id(
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            project_id=result.project_id,
            signal_type=result.signal_kind,
            data_mode=data_mode.value,
        ),
        project_id=result.project_id,
        signal_type=SignalType.RELATIONSHIP_GRAPH,
        finding=result.finding.summary + ": " + (
            result.why_flagged or result.why_not_flagged or result.finding.summary
        ),
        severity=result.severity,
        score=result.graph_score,
        confidence=confidence_unit(result.evidence_confidence),
        source_type=source_type,
        source_ids=source_ids,
        evidence_facts=facts,
        explanation=result.explanation,
        engine_name=EvidenceEngine.GRAPH,
        engine_version=ENGINE_VERSION,
        data_mode=data_mode,
        provenance=provenance,
        disposition=disposition,
        status=DISPOSITION_TO_STATUS[disposition],
        comparables=comparables,
    )
