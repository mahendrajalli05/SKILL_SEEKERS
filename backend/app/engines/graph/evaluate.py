"""Held-out Relationship Graph evaluation on real works and HYBRID projects.

HYBRID ``scenario_type`` / ``demo_case_id`` / ``overlap_group_id`` are
attached AFTER scoring and are never graph inputs.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import REPO_ROOT
from app.db import get_session_factory
from app.engines.graph.constants import FORBIDDEN_MODEL_INPUT_COLUMNS
from app.engines.graph.service import assess_project_graph
from app.engines.graph.types import GraphIntelligenceResult, GraphMode
from app.engines.overlap.embeddings import HashedTokenEmbedder
from app.engines.overlap.enrichment import HeldOutOverlapLabel, load_held_out_overlap_labels
from app.engines.overlap.evaluate import select_hybrid_overlap_projects, select_real_overlap_projects
from app.models.project import Project
from app.pipeline.synthetic import DEFAULT_OUTPUT_CSV


@dataclass
class GraphEvaluationRow:
    dataset: str
    case_id: str
    project_id: int
    internal_project_id: str
    graph_mode: str
    data_mode: str
    connected_project_count: int
    same_constituency_count: int
    same_category_count: int
    same_ida_count: int
    similar_project_count: int
    strongest_relationship: str | None
    graph_finding: str
    evidence_confidence: int
    graph_score: int | None
    independent_signal_count: int
    ida_associated_project_count: int
    cluster_size: int
    explanation: str
    held_out_scenario_type: str | None = None
    held_out_demo_case_id: str | None = None


def _require_no_label_leakage(project: Project) -> None:
    leaked = set(FORBIDDEN_MODEL_INPUT_COLUMNS).intersection(project.__dict__.keys())
    if leaked:
        raise RuntimeError(f"Project row unexpectedly contains label columns: {sorted(leaked)}")


def assess_without_label_leakage(
    session: Session,
    project: Project,
    *,
    mode: GraphMode,
    embedder: HashedTokenEmbedder | None = None,
) -> GraphIntelligenceResult:
    _require_no_label_leakage(project)
    return assess_project_graph(
        session,
        project.id,
        mode=mode,
        persist=False,
        embedder=embedder or HashedTokenEmbedder(),
    )


def _row_from_result(
    *,
    dataset: str,
    case_id: str,
    result: GraphIntelligenceResult,
    held_out: HeldOutOverlapLabel | None,
) -> GraphEvaluationRow:
    data_mode = "HYBRID" if result.graph_mode == GraphMode.HYBRID_TEST else "REAL"
    if dataset == "HYBRID":
        data_mode = "HYBRID"
    return GraphEvaluationRow(
        dataset=dataset,
        case_id=case_id,
        project_id=result.project_id,
        internal_project_id=result.internal_project_id,
        graph_mode=result.graph_mode.value,
        data_mode=data_mode,
        connected_project_count=result.stats.connected_project_count,
        same_constituency_count=result.stats.same_constituency_count,
        same_category_count=result.stats.same_category_count,
        same_ida_count=result.stats.same_ida_count,
        similar_project_count=result.stats.similar_project_count,
        strongest_relationship=result.stats.strongest_relationship,
        graph_finding=result.finding.kind.value,
        evidence_confidence=result.evidence_confidence,
        graph_score=result.graph_score,
        independent_signal_count=result.stats.independent_signal_count,
        ida_associated_project_count=result.stats.ida_associated_project_count,
        cluster_size=result.stats.cluster_size,
        explanation=result.explanation,
        held_out_scenario_type=held_out.scenario_type if held_out else None,
        held_out_demo_case_id=held_out.demo_case_id if held_out else None,
    )


def run_relationship_graph_evaluation(
    *,
    session: Session | None = None,
    synthetic_csv: Path | None = None,
) -> list[GraphEvaluationRow]:
    own_session = session is None
    session = session or get_session_factory()()
    embedder = HashedTokenEmbedder()
    try:
        labels = load_held_out_overlap_labels(synthetic_csv)
        rows: list[GraphEvaluationRow] = []
        for case_id, project in select_real_overlap_projects(session):
            result = assess_without_label_leakage(
                session, project, mode=GraphMode.REAL, embedder=embedder
            )
            rows.append(
                _row_from_result(
                    dataset="REAL",
                    case_id=case_id,
                    result=result,
                    held_out=None,
                )
            )
        for case_id, project in select_hybrid_overlap_projects(session, labels):
            result = assess_without_label_leakage(
                session, project, mode=GraphMode.HYBRID_TEST, embedder=embedder
            )
            rows.append(
                _row_from_result(
                    dataset="HYBRID",
                    case_id=case_id,
                    result=result,
                    held_out=labels.get(project.internal_project_id),
                )
            )
        return rows
    finally:
        if own_session:
            session.close()


def format_evaluation_rows(rows: Sequence[GraphEvaluationRow]) -> str:
    lines: list[str] = []
    for index, row in enumerate(rows, start=1):
        lines.append(f"[{index}] {row.dataset} / {row.case_id}")
        lines.append(f"    project_id={row.project_id}")
        lines.append(f"    internal_project_id={row.internal_project_id}")
        lines.append(f"    data_mode={row.data_mode} graph_mode={row.graph_mode}")
        lines.append(f"    connected_projects={row.connected_project_count}")
        lines.append(f"    same_constituency_count={row.same_constituency_count}")
        lines.append(f"    same_category_count={row.same_category_count}")
        lines.append(f"    same_ida_count={row.same_ida_count}")
        lines.append(f"    similar_project_count={row.similar_project_count}")
        lines.append(f"    strongest_relationship={row.strongest_relationship}")
        lines.append(f"    graph_finding={row.graph_finding}")
        lines.append(f"    evidence_confidence={row.evidence_confidence}")
        lines.append(f"    graph_score={row.graph_score}")
        lines.append(f"    independent_signal_count={row.independent_signal_count}")
        lines.append(f"    ida_associated_project_count={row.ida_associated_project_count}")
        lines.append(f"    cluster_size={row.cluster_size}")
        if row.dataset == "HYBRID":
            lines.append(
                "    held_out_label="
                f"scenario_type={row.held_out_scenario_type} "
                f"demo_case_id={row.held_out_demo_case_id or '(none)'}"
            )
        lines.append(f"    explanation={row.explanation}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def evaluation_payload(rows: Sequence[GraphEvaluationRow]) -> list[dict[str, object]]:
    return [asdict(row) for row in rows]


def repo_root() -> Path:
    return REPO_ROOT
