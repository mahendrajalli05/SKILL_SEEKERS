"""Held-out Risk Fusion evaluation on REAL works and HYBRID evidence.

Cost, Time, Overlap, and Compliance scores are consumed via Evidence Objects.
HYBRID ``scenario_type`` / ``demo_case_id`` are attached AFTER fusion.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import REPO_ROOT
from app.db import get_session_factory
from app.domain.enums import DataMode
from app.engines.compliance.service import assess_project_compliance
from app.engines.compliance.types import ComplianceMode
from app.engines.cost.service import assess_project_cost
from app.engines.fusion.constants import FORBIDDEN_MODEL_INPUT_COLUMNS
from app.engines.fusion.fuse import fuse_evidence
from app.engines.fusion.types import FusionResult
from app.engines.overlap.embeddings import HashedTokenEmbedder
from app.engines.overlap.enrichment import load_held_out_overlap_labels
from app.engines.overlap.evaluate import select_hybrid_overlap_projects, select_real_overlap_projects
from app.engines.overlap.service import assess_project_overlap
from app.engines.overlap.types import OverlapMode
from app.engines.time.service import assess_project_time
from app.engines.time.types import TimeMode
from app.evidence.adapters.compliance import compliance_result_to_evidence
from app.evidence.adapters.cost import cost_result_to_evidence
from app.evidence.adapters.overlap import overlap_result_to_evidence
from app.evidence.adapters.time import time_result_to_evidence
from app.models.project import Project
from app.pipeline.synthetic import DEFAULT_OUTPUT_CSV


@dataclass
class FusionEvaluationRow:
    dataset: str
    case_id: str
    project_id: int
    internal_project_id: str
    data_mode: str
    investigation_priority: int
    investigation_priority_0_100: float
    raw_risk: float
    evidence_confidence: int
    priority_band: str
    explanation_type: str
    recommended_action: str
    contributing_signals: list[str]
    unavailable_integrated: list[str]
    evidence_ids: list[str]
    available_weight: float
    available_signal_weight: float
    unavailable_signal_weight: float
    unused_weight: float
    evidence_coverage: float
    explanation: str
    recommendation: str
    held_out_scenario_type: str | None = None
    held_out_demo_case_id: str | None = None
    held_out_mixed_signals: str | None = None


def _require_no_label_leakage(project: Project) -> None:
    leaked = set(FORBIDDEN_MODEL_INPUT_COLUMNS).intersection(project.__dict__.keys())
    if leaked:
        raise RuntimeError(f"Project row unexpectedly contains label columns: {sorted(leaked)}")


def collect_evidence_objects(
    session: Session,
    project: Project,
    *,
    data_mode: DataMode,
    embedder: HashedTokenEmbedder,
):
    """Run frozen engines and adapt to Evidence Objects. Labels are not inputs."""
    _require_no_label_leakage(project)
    snapshot = project.snapshot
    cost_result = assess_project_cost(session, project.id, persist=False)
    objects = [cost_result_to_evidence(cost_result, project, snapshot=snapshot)]
    if data_mode == DataMode.HYBRID:
        time_mode = TimeMode.HYBRID_TEST
        overlap_mode = OverlapMode.HYBRID_TEST
        compliance_mode = ComplianceMode.HYBRID_TEST
    else:
        time_mode = TimeMode.REAL
        overlap_mode = OverlapMode.REAL
        compliance_mode = ComplianceMode.REAL
    time_result = assess_project_time(session, project.id, mode=time_mode, persist=False)
    objects.append(time_result_to_evidence(time_result, project, snapshot=snapshot))
    overlap_result = assess_project_overlap(
        session,
        project.id,
        mode=overlap_mode,
        persist=False,
        embedder=embedder,
    )
    objects.append(overlap_result_to_evidence(overlap_result, project, snapshot=snapshot))
    compliance_result = assess_project_compliance(
        session,
        project.id,
        mode=compliance_mode,
        persist=False,
    )
    objects.append(compliance_result_to_evidence(compliance_result, project, snapshot=snapshot))
    return objects


def fuse_project(
    session: Session,
    project: Project,
    *,
    data_mode: DataMode,
    embedder: HashedTokenEmbedder,
) -> FusionResult:
    objects = collect_evidence_objects(
        session, project, data_mode=data_mode, embedder=embedder
    )
    return fuse_evidence(
        objects,
        project_id=project.id,
        internal_project_id=project.internal_project_id,
        requested_data_mode=data_mode,
    )


def _row_from_result(
    *,
    dataset: str,
    case_id: str,
    result: FusionResult,
    held_out_scenario_type: str | None = None,
    held_out_demo_case_id: str | None = None,
    held_out_mixed_signals: str | None = None,
) -> FusionEvaluationRow:
    contributing = [
        f"{item.display_name}:{item.risk_score}"
        for item in result.contributing_signals
    ]
    unavailable = [
        item.display_name
        for item in result.unavailable_signals
        if item.signal_id in {"cost", "schedule", "overlap", "compliance"}
    ]
    return FusionEvaluationRow(
        dataset=dataset,
        case_id=case_id,
        project_id=result.project_id,
        internal_project_id=result.internal_project_id or "",
        data_mode=result.data_mode.value,
        investigation_priority=result.investigation_priority,
        investigation_priority_0_100=result.investigation_priority_0_100,
        raw_risk=result.raw_risk,
        evidence_confidence=result.evidence_confidence,
        priority_band=result.priority_band.value,
        explanation_type=result.explanation_type.value,
        recommended_action=result.recommended_action.value,
        contributing_signals=contributing,
        unavailable_integrated=unavailable,
        evidence_ids=list(result.evidence_ids),
        available_weight=result.available_weight,
        available_signal_weight=result.available_signal_weight,
        unavailable_signal_weight=result.unavailable_signal_weight,
        unused_weight=result.unused_weight,
        evidence_coverage=result.evidence_coverage,
        explanation=result.explanation,
        recommendation=result.recommendation,
        held_out_scenario_type=held_out_scenario_type,
        held_out_demo_case_id=held_out_demo_case_id,
        held_out_mixed_signals=held_out_mixed_signals,
    )


def run_risk_fusion_evaluation(
    *,
    session: Session | None = None,
    synthetic_csv: Path | None = None,
) -> list[FusionEvaluationRow]:
    own_session = session is None
    session = session or get_session_factory()()
    embedder = HashedTokenEmbedder()
    try:
        labels = load_held_out_overlap_labels(synthetic_csv)
        rows: list[FusionEvaluationRow] = []
        for case_id, project in select_real_overlap_projects(session):
            result = fuse_project(session, project, data_mode=DataMode.REAL, embedder=embedder)
            rows.append(
                _row_from_result(dataset="REAL", case_id=case_id, result=result)
            )
        for case_id, project in select_hybrid_overlap_projects(session, labels):
            result = fuse_project(session, project, data_mode=DataMode.HYBRID, embedder=embedder)
            held = labels.get(project.internal_project_id)
            rows.append(
                _row_from_result(
                    dataset="HYBRID",
                    case_id=case_id,
                    result=result,
                    held_out_scenario_type=held.scenario_type if held else None,
                    held_out_demo_case_id=held.demo_case_id if held else None,
                    held_out_mixed_signals=held.mixed_signals if held else None,
                )
            )
        return rows
    finally:
        if own_session:
            session.close()


def format_evaluation_rows(rows: Sequence[FusionEvaluationRow]) -> str:
    lines: list[str] = []
    for index, row in enumerate(rows, start=1):
        lines.append(f"[{index}] {row.dataset} / {row.case_id}")
        lines.append(f"    project_id={row.project_id}")
        lines.append(f"    internal_project_id={row.internal_project_id}")
        lines.append(f"    data_mode={row.data_mode}")
        lines.append(f"    investigation_priority={row.investigation_priority}")
        lines.append(f"    investigation_priority_0_100={row.investigation_priority_0_100}")
        lines.append(f"    raw_risk={row.raw_risk}")
        lines.append(f"    evidence_confidence={row.evidence_confidence}")
        lines.append(f"    priority_band={row.priority_band}")
        lines.append(f"    explanation_type={row.explanation_type}")
        lines.append(f"    recommended_action={row.recommended_action}")
        lines.append(f"    contributing_signals={', '.join(row.contributing_signals) or '(none)'}")
        lines.append(f"    unavailable_integrated={', '.join(row.unavailable_integrated) or '(none)'}")
        lines.append(f"    available_weight={row.available_weight}")
        lines.append(f"    available_signal_weight={row.available_signal_weight}")
        lines.append(f"    unavailable_signal_weight={row.unavailable_signal_weight}")
        lines.append(f"    unused_weight={row.unused_weight}")
        lines.append(f"    evidence_coverage={row.evidence_coverage}")
        if row.dataset == "HYBRID":
            lines.append(
                "    held_out_label="
                f"scenario_type={row.held_out_scenario_type} "
                f"demo_case_id={row.held_out_demo_case_id or '(none)'} "
                f"mixed_signals={row.held_out_mixed_signals or '(none)'}"
            )
        lines.append(f"    recommendation={row.recommendation}")
        lines.append(f"    explanation={row.explanation}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def evaluation_payload(rows: Sequence[FusionEvaluationRow]) -> list[dict[str, object]]:
    return [asdict(row) for row in rows]


def synthetic_csv_exists() -> bool:
    return DEFAULT_OUTPUT_CSV.exists()


def repo_root() -> Path:
    return REPO_ROOT
