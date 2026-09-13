"""Relationship Graph V1 orchestration.

Produces graph evidence. Does not run cost, time, overlap scoring
reimplementation, compliance, or Risk Fusion.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import EvidenceEngine
from app.engines.graph.builder import build_ego_graph, connected_project_records
from app.engines.graph.constants import ENGINE_NAME, ENGINE_VERSION, EVIDENCE_TYPE, SIGNAL_KIND
from app.engines.graph.explain import (
    finding_summary,
    project_explanation,
    why_flagged_text,
    why_not_flagged_text,
)
from app.engines.graph.findings import (
    classify_finding,
    evidence_confidence,
    graph_score,
    independent_signals,
    status_for,
)
from app.engines.graph.index import GraphIndex, candidate_strategy_label
from app.engines.graph.queries import build_stats
from app.engines.graph.relationships import similar_relations_for
from app.engines.graph.repository import load_graph_records, load_subject_record
from app.engines.graph.types import (
    GraphFinding,
    GraphIntelligenceResult,
    GraphMode,
    GraphRecord,
)
from app.engines.overlap.embeddings import EmbeddingBackend, HashedTokenEmbedder, get_default_embedder
from app.engines.overlap.enrichment import HybridGps, load_hybrid_gps
from app.models.evidence import EvidenceObjectRow
from app.models.graph import GraphEdge
from app.models.project import Project


def _reject_label_leakage(record: GraphRecord) -> None:
    from app.engines.graph.constants import FABRICATED_GRAPH_FIELDS, FORBIDDEN_MODEL_INPUT_COLUMNS
    from app.engines.graph.errors import GraphError

    fields = set(GraphRecord.__dataclass_fields__)
    leaked = fields.intersection(FORBIDDEN_MODEL_INPUT_COLUMNS | FABRICATED_GRAPH_FIELDS)
    if leaked:
        raise GraphError(f"GraphRecord contains forbidden fields: {sorted(leaked)}")
    blob = " ".join(
        [
            record.mp_name,
            record.work_description,
            record.category,
            record.constituency,
            record.ida,
            record.state,
        ]
    ).casefold()
    for token in ("scenario_type", "demo_case_id", "overlap_group_id", "coordinate_source"):
        if token in blob:
            raise GraphError(f"Synthetic label token leaked into graph input: {token}")


def assess_graph(
    subject: GraphRecord,
    records: Sequence[GraphRecord],
    *,
    mode: GraphMode = GraphMode.REAL,
    embedder: EmbeddingBackend | None = None,
    gps_by_id: dict[str, HybridGps] | None = None,
) -> GraphIntelligenceResult:
    """Pure assessment against an in-memory corpus. Does not write to the database."""
    _reject_label_leakage(subject)
    backend = embedder or HashedTokenEmbedder()
    gps_used = bool(mode == GraphMode.HYBRID_TEST and gps_by_id)
    dataset_type = "HYBRID" if mode == GraphMode.HYBRID_TEST else "REAL"
    index = GraphIndex(records)
    similar = similar_relations_for(
        subject,
        records,
        mode=mode,
        embedder=backend,
        gps_by_id=gps_by_id if mode == GraphMode.HYBRID_TEST else None,
    )
    cluster_peers = index.cluster_peers(subject)
    similar_pairs: list[tuple[GraphRecord, object]] = []
    by_id = {item.project_id: item for item in records}
    for relation in similar:
        peer = by_id.get(relation.linked_project_id)
        if peer is not None:
            similar_pairs.append((peer, relation))
    _graph, project_node, connected_nodes, relationships = build_ego_graph(
        subject,
        similar=similar_pairs,
        cluster_peers=cluster_peers,
    )
    connected = connected_project_records(connected_nodes, by_id, subject.project_id)
    signals = independent_signals(subject, similar)
    entity_edge_count = sum(1 for rel in relationships if rel.edge_type.value != "SIMILAR_TO")
    kind = classify_finding(
        subject,
        similar=similar,
        cluster_size=index.cluster_size(subject),
        entity_edge_count=entity_edge_count,
    )
    stats = build_stats(
        subject,
        index=index,
        connected=connected,
        similar=similar,
        cluster_peers=cluster_peers,
        relationships=relationships,
        independent_signals=signals,
    )
    score = graph_score(
        kind,
        similar_count=stats.similar_project_count,
        same_constituency_similar=stats.same_constituency_similar,
        same_ida_similar=stats.same_ida_similar,
        close_dates_similar=stats.close_dates_similar,
        independent_signal_count=stats.independent_signal_count,
    )
    confidence = evidence_confidence(
        subject,
        kind=kind,
        similar_count=len(similar),
        mode=mode,
        gps_used=gps_used,
    )
    status, severity, flagged = status_for(kind)
    explanation = project_explanation(
        kind=kind,
        stats=stats,
        subject=subject,
        similar=similar,
        mode=mode,
        cluster_peers=len(cluster_peers),
    )
    finding = GraphFinding(
        kind=kind,
        summary=finding_summary(kind),
        details=explanation,
        score=score,
        confidence=confidence,
        independent_signal_count=stats.independent_signal_count,
        independent_signals=stats.independent_signals,
    )
    return GraphIntelligenceResult(
        project_id=subject.project_id,
        internal_project_id=subject.internal_project_id,
        engine=ENGINE_NAME,
        engine_version=ENGINE_VERSION,
        evidence_type=EVIDENCE_TYPE,
        dataset_type=dataset_type,
        graph_mode=mode,
        finding_kind=kind,
        flagged=flagged,
        status=status,
        severity=severity,
        signal_kind=SIGNAL_KIND,
        graph_score=score,
        evidence_confidence=confidence,
        explanation=explanation,
        why_flagged=why_flagged_text(kind, stats),
        why_not_flagged=why_not_flagged_text(kind, stats, subject),
        finding=finding,
        stats=stats,
        project_node=project_node,
        connected_nodes=connected_nodes,
        relationships=relationships,
        mp_name=subject.mp_name,
        category=subject.category,
        constituency=subject.constituency,
        constituency_kind=subject.constituency_kind,
        constituency_usable=subject.constituency_usable,
        ida=subject.ida,
        state=subject.state,
        candidate_strategy=candidate_strategy_label(
            constituency_usable=subject.constituency_usable,
            gps_used=gps_used,
        ),
        gps_used=gps_used,
    )


def persist_graph_evidence(session: Session, result: GraphIntelligenceResult) -> EvidenceObjectRow:
    from app.evidence.adapters.graph import graph_result_to_evidence
    from app.evidence.repository import persist_evidence_object

    project = session.get(Project, result.project_id)
    if project is None:
        raise KeyError(f"Project {result.project_id} was not found.")
    obj = graph_result_to_evidence(result, project, snapshot=project.snapshot)
    row = persist_evidence_object(session, obj, replace_engine=EvidenceEngine.GRAPH)
    existing = session.scalars(
        select(GraphEdge).where(GraphEdge.from_project_id == result.project_id)
    ).all()
    for edge in existing:
        session.delete(edge)
    seen: set[tuple[int, int]] = set()
    for rel in result.relationships:
        if rel.edge_type.value != "SIMILAR_TO":
            continue
        if rel.from_project_id is None or rel.to_project_id is None:
            continue
        if rel.from_project_id == result.project_id:
            from_id, to_id = rel.from_project_id, rel.to_project_id
        elif rel.to_project_id == result.project_id:
            from_id, to_id = rel.to_project_id, rel.from_project_id
        else:
            continue
        key = (from_id, to_id)
        if key in seen:
            continue
        seen.add(key)
        session.add(
            GraphEdge(
                from_project_id=from_id,
                to_project_id=to_id,
                edge_type=rel.edge_type.value,
                weight=rel.similarity_score if rel.similarity_score is not None else rel.strength,
            )
        )
    session.flush()
    return row


def assess_project_graph(
    session: Session,
    project_id: int,
    *,
    mode: GraphMode = GraphMode.REAL,
    persist: bool = True,
    embedder: EmbeddingBackend | None = None,
) -> GraphIntelligenceResult:
    gps_map = load_hybrid_gps() if mode == GraphMode.HYBRID_TEST else None
    subject = load_subject_record(session, project_id)
    project = session.get(Project, project_id)
    if project is None:
        raise KeyError(f"Project {project_id} was not found.")
    records = load_graph_records(
        session,
        mode=mode,
        subject_is_synthetic=bool(project.is_synthetic),
    )
    backend = embedder or get_default_embedder()
    result = assess_graph(
        subject,
        records,
        mode=mode,
        embedder=backend,
        gps_by_id=gps_map,
    )
    if persist:
        persist_graph_evidence(session, result)
        session.commit()
    return result
