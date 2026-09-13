"""Held-out Risk Fusion V2 evaluation on REAL and HYBRID projects.

Frozen engines are consumed via Evidence Objects. Held-out scenario labels
are attached AFTER fusion.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session_factory
from app.domain.enums import DataMode
from app.engines.fusion.evaluate import collect_evidence_objects
from app.engines.fusion_v2.fuse import fuse_evidence_v2
from app.engines.fusion_v2.types import FusionV2Result
from app.engines.graph.service import assess_project_graph
from app.engines.graph.types import GraphMode
from app.engines.overlap.embeddings import HashedTokenEmbedder
from app.engines.overlap.enrichment import load_held_out_overlap_labels
from app.engines.overlap.evaluate import select_hybrid_overlap_projects, select_real_overlap_projects
from app.evidence.adapters.graph import graph_result_to_evidence
from app.models.project import Project
from app.pipeline.synthetic import DEFAULT_OUTPUT_CSV


@dataclass
class FusionV2EvaluationRow:
    dataset: str
    case_id: str
    project_id: int
    internal_project_id: str
    data_mode: str
    investigation_priority: int
    evidence_confidence: int
    risk_class: str
    explanation_type: str
    recommended_action: str
    top_evidence_groups: list[str]
    discounted_evidence: list[str]
    conflicting_evidence: list[str]
    unavailable_evidence: list[str]
    explanation: str
    held_out_scenario_type: str | None = None
    held_out_demo_case_id: str | None = None


def _extra_real_projects(session: Session, used: set[int], needed: int) -> list[tuple[str, Project]]:
    rows = list(
        session.scalars(
            select(Project)
            .where(Project.is_synthetic == False, Project.state == "Andhra Pradesh")  # noqa: E712
            .order_by(Project.id.asc())
            .limit(80)
        ).all()
    )
    extra: list[tuple[str, Project]] = []
    for row in rows:
        if row.id in used:
            continue
        extra.append((f"real_extra_{row.id}", row))
        used.add(row.id)
        if len(extra) >= needed:
            break
    return extra


def _extra_hybrid_projects(
    session: Session,
    labels: dict,
    used: set[str],
    needed: int,
) -> list[tuple[str, Project]]:
    extra: list[tuple[str, Project]] = []
    for internal_id in sorted(labels):
        if internal_id in used:
            continue
        row = session.scalars(
            select(Project).where(Project.internal_project_id == internal_id)
        ).first()
        if row is None:
            continue
        extra.append((f"hybrid_extra_{row.id}", row))
        used.add(internal_id)
        if len(extra) >= needed:
            break
    return extra


def fuse_project_v2(
    session: Session,
    project: Project,
    *,
    data_mode: DataMode,
    embedder: HashedTokenEmbedder,
) -> FusionV2Result:
    objects = collect_evidence_objects(
        session, project, data_mode=data_mode, embedder=embedder
    )
    graph_mode = GraphMode.HYBRID_TEST if data_mode == DataMode.HYBRID else GraphMode.REAL
    try:
        graph_result = assess_project_graph(
            session, project.id, mode=graph_mode, persist=False, embedder=embedder
        )
        objects.append(graph_result_to_evidence(graph_result, project, snapshot=project.snapshot))
    except Exception:
        pass
    return fuse_evidence_v2(
        objects,
        project_id=project.id,
        internal_project_id=project.internal_project_id,
        requested_data_mode=data_mode,
    )


def _row_from_result(
    *,
    dataset: str,
    case_id: str,
    result: FusionV2Result,
    held_out_scenario_type: str | None = None,
    held_out_demo_case_id: str | None = None,
) -> FusionV2EvaluationRow:
    top = [
        f"{item.display_name}:{item.raw_evidence_score}"
        for item in result.contributing_evidence_groups[:3]
    ]
    discounted = [
        item.display_name for item in result.discounted_correlated_evidence
    ]
    conflicting = [
        f"{item.left_group} vs {item.right_group}" for item in result.conflicting_evidence
    ]
    unavailable = [item.display_name for item in result.unavailable_evidence]
    return FusionV2EvaluationRow(
        dataset=dataset,
        case_id=case_id,
        project_id=result.project_id,
        internal_project_id=result.internal_project_id or "",
        data_mode=result.data_mode.value,
        investigation_priority=result.investigation_priority,
        evidence_confidence=result.evidence_confidence,
        risk_class=result.risk_class.value,
        explanation_type=result.explanation_type.value,
        recommended_action=result.recommended_action.value,
        top_evidence_groups=top,
        discounted_evidence=discounted,
        conflicting_evidence=conflicting,
        unavailable_evidence=unavailable,
        explanation=result.explanation,
        held_out_scenario_type=held_out_scenario_type,
        held_out_demo_case_id=held_out_demo_case_id,
    )


def run_risk_fusion_v2_evaluation(
    *,
    session: Session | None = None,
) -> list[FusionV2EvaluationRow]:
    own_session = session is None
    session = session or get_session_factory()()
    embedder = HashedTokenEmbedder()
    try:
        labels = load_held_out_overlap_labels(DEFAULT_OUTPUT_CSV)
        rows: list[FusionV2EvaluationRow] = []
        real_pairs = list(select_real_overlap_projects(session))
        used_real = {project.id for _, project in real_pairs}
        real_pairs.extend(_extra_real_projects(session, used_real, max(0, 15 - len(real_pairs))))
        for case_id, project in real_pairs[:15]:
            result = fuse_project_v2(session, project, data_mode=DataMode.REAL, embedder=embedder)
            rows.append(_row_from_result(dataset="REAL", case_id=case_id, result=result))
        hybrid_pairs = list(select_hybrid_overlap_projects(session, labels))
        used_hybrid = {project.internal_project_id for _, project in hybrid_pairs}
        hybrid_pairs.extend(
            _extra_hybrid_projects(session, labels, used_hybrid, max(0, 15 - len(hybrid_pairs)))
        )
        for case_id, project in hybrid_pairs[:15]:
            result = fuse_project_v2(session, project, data_mode=DataMode.HYBRID, embedder=embedder)
            held = labels.get(project.internal_project_id)
            rows.append(
                _row_from_result(
                    dataset="HYBRID",
                    case_id=case_id,
                    result=result,
                    held_out_scenario_type=held.scenario_type if held else None,
                    held_out_demo_case_id=held.demo_case_id if held else None,
                )
            )
        return rows
    finally:
        if own_session:
            session.close()


def format_evaluation_rows(rows: Sequence[FusionV2EvaluationRow]) -> str:
    lines: list[str] = []
    for index, row in enumerate(rows, start=1):
        lines.append(f"[{index}] {row.dataset} / {row.case_id}")
        lines.append(f"    project={row.project_id} {row.internal_project_id}")
        lines.append(f"    data_mode={row.data_mode}")
        lines.append(f"    priority={row.investigation_priority}")
        lines.append(f"    confidence={row.evidence_confidence}")
        lines.append(f"    risk_class={row.risk_class}")
        lines.append(f"    top_evidence_groups={', '.join(row.top_evidence_groups) or '(none)'}")
        lines.append(f"    discounted_evidence={', '.join(row.discounted_evidence) or '(none)'}")
        lines.append(f"    conflicting_evidence={', '.join(row.conflicting_evidence) or '(none)'}")
        lines.append(f"    unavailable_evidence={', '.join(row.unavailable_evidence) or '(none)'}")
        lines.append(f"    recommendation={row.recommended_action}")
        if row.dataset == "HYBRID":
            lines.append(
                f"    held_out_label=scenario_type={row.held_out_scenario_type} "
                f"demo_case_id={row.held_out_demo_case_id or '(none)'}"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def evaluation_payload(rows: Sequence[FusionV2EvaluationRow]) -> list[dict[str, object]]:
    return [asdict(row) for row in rows]
