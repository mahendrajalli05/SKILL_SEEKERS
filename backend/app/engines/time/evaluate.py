"""Held-out Time Intelligence evaluation on real works and HYBRID-TEST schedules.

The 56,138-row SQLite ``project`` table supplies observed fields.
HYBRID dates/progress come from the synthetic CSV.
HYBRID ``scenario_type`` / ``demo_case_id`` are attached AFTER scoring.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import REPO_ROOT
from app.db import get_session_factory
from app.engines.cost.evaluate import DEMO_INTERNAL_IDS
from app.engines.time.constants import FORBIDDEN_MODEL_INPUT_COLUMNS
from app.engines.time.enrichment import HeldOutTimeLabel, load_held_out_time_labels, load_hybrid_schedules
from app.engines.time.service import assess_project_time
from app.engines.time.types import TimeIntelligenceResult, TimeMode
from app.models.project import Project
from app.pipeline.synthetic import DEFAULT_OUTPUT_CSV


@dataclass
class TimeEvaluationRow:
    dataset: str
    case_id: str
    project_id: int
    internal_project_id: str
    status: str
    time_mode: str
    peer_scope: str | None
    peer_count: int
    planned_duration_days: int | None
    actual_duration_days: int | None
    elapsed_duration_days: int | None
    slippage_days: int | None
    physical_progress_percent: int | None
    time_anomaly_score: int | None
    evidence_confidence: int
    flagged: bool
    outcome: str
    explanation: str
    held_out_scenario_type: str | None = None
    held_out_demo_case_id: str | None = None


def _first(session: Session, stmt) -> Project | None:
    return session.scalars(stmt.limit(1)).first()


def _require(row: Project | None, label: str) -> Project:
    if row is None:
        raise LookupError(f"Evaluation case {label} was not found in SQLite.")
    return row


def select_real_time_projects(session: Session) -> list[tuple[str, Project]]:
    unsanctioned = _require(
        _first(
            session,
            select(Project).where(
                Project.state == "Andhra Pradesh",
                Project.status == "Unsanctioned",
                Project.is_synthetic == False,  # noqa: E712
            ).order_by(Project.id.asc()),
        ),
        "real_ap_unsanctioned",
    )
    sanctioned = _require(
        _first(
            session,
            select(Project).where(
                Project.state == "Andhra Pradesh",
                Project.status == "Sanctioned",
                Project.is_synthetic == False,  # noqa: E712
            ).order_by(Project.id.asc()),
        ),
        "real_ap_sanctioned",
    )
    ongoing = _require(
        _first(
            session,
            select(Project).where(
                Project.state == "Andhra Pradesh",
                Project.status == "Ongoing",
                Project.is_synthetic == False,  # noqa: E712
            ).order_by(Project.id.asc()),
        ),
        "real_ap_ongoing",
    )
    completed = _require(
        _first(
            session,
            select(Project).where(
                Project.state == "Andhra Pradesh",
                Project.status == "Completed",
                Project.is_synthetic == False,  # noqa: E712
            ).order_by(Project.id.asc()),
        ),
        "real_ap_completed",
    )
    sitting = _require(
        _first(
            session,
            select(Project).where(
                Project.state == "Andhra Pradesh",
                Project.constituency == "Sitting Rajya Sabha",
                Project.is_synthetic == False,  # noqa: E712
            ).order_by(Project.id.asc()),
        ),
        "real_ap_sitting_rs",
    )
    return [
        ("real_ap_unsanctioned", unsanctioned),
        ("real_ap_sanctioned", sanctioned),
        ("real_ap_ongoing", ongoing),
        ("real_ap_completed", completed),
        ("real_ap_sitting_rs", sitting),
    ]


def select_hybrid_time_projects(
    session: Session,
    labels: dict[str, HeldOutTimeLabel],
) -> list[tuple[str, Project]]:
    chosen: list[tuple[str, Project]] = []
    for demo_id in ("STUCK", "CLEAN", "OVERBILL", "GHOST"):
        internal_id = DEMO_INTERNAL_IDS[demo_id]
        row = session.scalars(
            select(Project).where(Project.internal_project_id == internal_id)
        ).first()
        chosen.append((f"hybrid_demo_{demo_id.lower()}", _require(row, f"hybrid_demo_{demo_id}")))

    used = {item.internal_project_id for _label, item in chosen}
    time_ids = {
        internal_id
        for internal_id, label in labels.items()
        if label.scenario_type == "TIME_ANOMALY" and internal_id not in used
    }
    time_row = None
    ap_candidates = session.scalars(
        select(Project)
        .where(
            Project.state == "Andhra Pradesh",
            Project.is_synthetic == False,  # noqa: E712
        )
        .order_by(Project.id.asc())
    ).all()
    for candidate in ap_candidates:
        if candidate.internal_project_id in time_ids:
            time_row = candidate
            break
    if time_row is None:
        for internal_id in sorted(time_ids):
            time_row = session.scalars(
                select(Project).where(Project.internal_project_id == internal_id)
            ).first()
            if time_row is not None:
                break
    chosen.append(("hybrid_time_anomaly_held_out", _require(time_row, "hybrid_time_anomaly")))
    return chosen


def _row_from_result(
    *,
    dataset: str,
    case_id: str,
    result: TimeIntelligenceResult,
    status: str,
    held_out: HeldOutTimeLabel | None,
) -> TimeEvaluationRow:
    return TimeEvaluationRow(
        dataset=dataset,
        case_id=case_id,
        project_id=result.project_id,
        internal_project_id=result.internal_project_id,
        status=status,
        time_mode=result.time_mode.value,
        peer_scope=result.peer_scope,
        peer_count=result.peer_count,
        planned_duration_days=result.planned_duration_days,
        actual_duration_days=result.actual_duration_days,
        elapsed_duration_days=result.elapsed_duration_days,
        slippage_days=result.slippage_days,
        physical_progress_percent=result.physical_progress_percent,
        time_anomaly_score=result.time_anomaly_score,
        evidence_confidence=result.evidence_confidence,
        flagged=result.flagged,
        outcome=result.outcome.value,
        explanation=result.explanation,
        held_out_scenario_type=held_out.scenario_type if held_out else None,
        held_out_demo_case_id=held_out.demo_case_id if held_out else None,
    )


def assess_time_without_label_leakage(
    session: Session,
    project: Project,
    *,
    mode: TimeMode,
) -> TimeIntelligenceResult:
    leaked = set(FORBIDDEN_MODEL_INPUT_COLUMNS).intersection(project.__dict__.keys())
    if leaked:
        raise RuntimeError(f"Project row unexpectedly contains label columns: {sorted(leaked)}")
    return assess_project_time(session, project.id, mode=mode, persist=False)


def run_time_intelligence_evaluation(
    *,
    session: Session | None = None,
    synthetic_csv: Path | None = None,
) -> list[TimeEvaluationRow]:
    own_session = session is None
    session = session or get_session_factory()()
    try:
        csv_path = synthetic_csv or DEFAULT_OUTPUT_CSV
        labels = load_held_out_time_labels(csv_path)
        load_hybrid_schedules(csv_path)
        rows: list[TimeEvaluationRow] = []
        for case_id, project in select_real_time_projects(session):
            result = assess_time_without_label_leakage(session, project, mode=TimeMode.REAL)
            rows.append(
                _row_from_result(
                    dataset="REAL",
                    case_id=case_id,
                    result=result,
                    status=project.status or "",
                    held_out=None,
                )
            )
        for case_id, project in select_hybrid_time_projects(session, labels):
            result = assess_time_without_label_leakage(
                session,
                project,
                mode=TimeMode.HYBRID_TEST,
            )
            rows.append(
                _row_from_result(
                    dataset="HYBRID",
                    case_id=case_id,
                    result=result,
                    status=project.status or "",
                    held_out=labels.get(project.internal_project_id),
                )
            )
        return rows
    finally:
        if own_session:
            session.close()


def format_evaluation_rows(rows: Sequence[TimeEvaluationRow]) -> str:
    lines: list[str] = []
    for index, row in enumerate(rows, start=1):
        lines.append(f"[{index}] {row.dataset} / {row.case_id}")
        lines.append(f"    project_id={row.project_id}")
        lines.append(f"    internal_project_id={row.internal_project_id}")
        lines.append(f"    status={row.status}")
        lines.append(f"    time_mode={row.time_mode}")
        lines.append(f"    peer_scope={row.peer_scope}")
        lines.append(f"    peer_count={row.peer_count}")
        lines.append(f"    planned_duration_days={row.planned_duration_days}")
        lines.append(f"    actual_duration_days={row.actual_duration_days}")
        lines.append(f"    elapsed_duration_days={row.elapsed_duration_days}")
        lines.append(f"    slippage_days={row.slippage_days}")
        lines.append(f"    physical_progress_percent={row.physical_progress_percent}")
        lines.append(f"    time_anomaly_score={row.time_anomaly_score}")
        lines.append(f"    evidence_confidence={row.evidence_confidence}")
        lines.append(f"    flagged={row.flagged} outcome={row.outcome}")
        if row.dataset == "HYBRID":
            lines.append(
                "    held_out_label="
                f"scenario_type={row.held_out_scenario_type} "
                f"demo_case_id={row.held_out_demo_case_id or '(none)'}"
            )
        lines.append(f"    explanation={row.explanation}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def evaluation_payload(rows: Sequence[TimeEvaluationRow]) -> list[dict[str, object]]:
    return [asdict(row) for row in rows]


def synthetic_csv_exists() -> bool:
    return DEFAULT_OUTPUT_CSV.exists()


def repo_root() -> Path:
    return REPO_ROOT
