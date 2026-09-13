"""Held-out Cost Intelligence evaluation on real works and HYBRID labels.

The 56,138-row SQLite ``project`` table is the only peer baseline.
HYBRID ``scenario_type`` / ``demo_case_id`` are attached AFTER scoring and
are never passed into peer selection or the anomaly score.
"""

from __future__ import annotations

import csv
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import REPO_ROOT
from app.db import get_session_factory
from app.engines.cost.constants import FORBIDDEN_MODEL_INPUT_COLUMNS
from app.engines.cost.service import assess_project_cost
from app.engines.cost.types import CostIntelligenceResult
from app.models.project import Project
from app.pipeline.synthetic import DEFAULT_OUTPUT_CSV

DEMO_INTERNAL_IDS = {
    "OVERBILL": "internal:eab396eafd121f6c8426cb285be2078aa7cfc6fe718050d6eb7340208318e762",
    "CLEAN": "internal:e714d635eb46ac65589489b3972d8cf896f9c2b7baaaeb753bf3e312929fc3b9",
    "STUCK": "internal:639b82094c0b023fa8fd1047f88e87a608a92f59442a74bf086ab25d4a2274c5",
    "GHOST": "internal:464569d6e0e8fa677cd826b350df9c2c0bd680a7665587cadd63e93e2b357d29",
}


@dataclass(frozen=True)
class HeldOutLabel:
    scenario_type: str
    demo_case_id: str
    mixed_signals: str


@dataclass
class EvaluationRow:
    dataset: str
    case_id: str
    project_id: int
    internal_project_id: str
    constituency: str
    category: str
    peer_scope: str | None
    peer_count: int
    peer_quality: int
    similarity_rationale: str
    expected_cost: float | None
    expected_range_low: float | None
    expected_range_high: float | None
    actual_allocation: int | None
    deviation_percentage: float | None
    cost_anomaly_score: int | None
    evidence_confidence: int
    flagged: bool
    outcome: str
    explanation: str
    held_out_scenario_type: str | None = None
    held_out_demo_case_id: str | None = None


def load_held_out_labels(path: Path | None = None) -> dict[str, HeldOutLabel]:
    """Load HYBRID labels for post-hoc evaluation only."""
    csv_path = path or DEFAULT_OUTPUT_CSV
    labels: dict[str, HeldOutLabel] = {}
    with csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            internal_id = (row.get("internal_project_id") or "").strip()
            if not internal_id:
                continue
            labels[internal_id] = HeldOutLabel(
                scenario_type=(row.get("scenario_type") or "").strip(),
                demo_case_id=(row.get("demo_case_id") or "").strip(),
                mixed_signals=(row.get("mixed_signals") or "").strip(),
            )
    return labels


def _first(session: Session, stmt) -> Project | None:
    return session.scalars(stmt.limit(1)).first()


def _require(row: Project | None, label: str) -> Project:
    if row is None:
        raise LookupError(f"Evaluation case {label} was not found in SQLite.")
    return row


def select_real_evaluation_projects(session: Session) -> list[tuple[str, Project]]:
    highest_ap = _require(
        _first(
            session,
            select(Project)
            .where(Project.state == "Andhra Pradesh", Project.is_synthetic == False)
            .order_by(Project.allocation_amount.desc(), Project.id.asc()),
        ),
        "real_high_ap_allocation",
    )
    kurnool = _require(
        _first(
            session,
            select(Project)
            .where(
                Project.state == "Andhra Pradesh",
                Project.constituency == "KURNOOL",
                Project.category == "Normal/Others",
                Project.allocation_amount > 0,
                Project.is_synthetic == False,
            )
            .order_by(Project.id.asc()),
        ),
        "real_kurnool_typical",
    )
    zero_ap = _require(
        _first(
            session,
            select(Project)
            .where(
                Project.state == "Andhra Pradesh",
                Project.allocation_amount == 0,
                Project.is_synthetic == False,
            )
            .order_by(Project.id.asc()),
        ),
        "real_ap_zero_allocation",
    )
    repair = _require(
        _first(
            session,
            select(Project)
            .where(
                Project.state == "Andhra Pradesh",
                Project.category == "Repair and Renovation",
                Project.allocation_amount > 0,
                Project.is_synthetic == False,
            )
            .order_by(Project.id.asc()),
        ),
        "real_ap_repair_renovation",
    )
    eluru = _require(
        _first(
            session,
            select(Project)
            .where(
                Project.state == "Andhra Pradesh",
                Project.constituency == "ELURU",
                Project.work_description == "NA - Construction of water tanks",
                Project.allocation_amount > 0,
                Project.is_synthetic == False,
            )
            .order_by(Project.allocation_amount.desc(), Project.id.asc()),
        ),
        "real_eluru_water_tanks",
    )
    return [
        ("real_high_ap_allocation", highest_ap),
        ("real_kurnool_typical", kurnool),
        ("real_ap_zero_allocation", zero_ap),
        ("real_ap_repair_renovation", repair),
        ("real_eluru_water_tanks", eluru),
    ]


def select_hybrid_evaluation_projects(
    session: Session,
    labels: dict[str, HeldOutLabel],
) -> list[tuple[str, Project]]:
    chosen: list[tuple[str, Project]] = []
    for demo_id in ("OVERBILL", "CLEAN", "STUCK", "GHOST"):
        internal_id = DEMO_INTERNAL_IDS[demo_id]
        row = session.scalars(
            select(Project).where(Project.internal_project_id == internal_id)
        ).first()
        chosen.append((f"hybrid_demo_{demo_id.lower()}", _require(row, f"hybrid_demo_{demo_id}")))

    used_ids = {item.internal_project_id for _label, item in chosen}
    cost_ids = {
        internal_id
        for internal_id, label in labels.items()
        if label.scenario_type == "COST_ANOMALY" and internal_id not in used_ids
    }
    cost_row = None
    ap_candidates = session.scalars(
        select(Project)
        .where(
            Project.state == "Andhra Pradesh",
            Project.allocation_amount > 0,
            Project.is_synthetic == False,
        )
        .order_by(Project.id.asc())
    ).all()
    for candidate in ap_candidates:
        if candidate.internal_project_id in cost_ids:
            cost_row = candidate
            break
    if cost_row is None:
        for internal_id in sorted(cost_ids):
            cost_row = session.scalars(
                select(Project).where(Project.internal_project_id == internal_id)
            ).first()
            if cost_row is not None:
                break
    chosen.append(("hybrid_cost_anomaly_held_out", _require(cost_row, "hybrid_cost_anomaly")))
    return chosen


def _row_from_result(
    *,
    dataset: str,
    case_id: str,
    result: CostIntelligenceResult,
    constituency: str,
    category: str,
    held_out: HeldOutLabel | None,
) -> EvaluationRow:
    return EvaluationRow(
        dataset=dataset,
        case_id=case_id,
        project_id=result.project_id,
        internal_project_id=result.internal_project_id,
        constituency=constituency,
        category=category,
        peer_scope=result.peer_scope,
        peer_count=result.peer_count,
        peer_quality=result.peer_quality,
        similarity_rationale=result.similarity_rationale,
        expected_cost=result.baseline,
        expected_range_low=result.expected_range_low,
        expected_range_high=result.expected_range_high,
        actual_allocation=result.actual_amount,
        deviation_percentage=result.deviation_percentage,
        cost_anomaly_score=result.cost_anomaly_score,
        evidence_confidence=result.evidence_confidence,
        flagged=result.flagged,
        outcome=result.outcome.value,
        explanation=result.explanation,
        held_out_scenario_type=held_out.scenario_type if held_out else None,
        held_out_demo_case_id=held_out.demo_case_id if held_out else None,
    )


def assess_without_label_leakage(
    session: Session,
    project: Project,
) -> CostIntelligenceResult:
    """Score using observed project fields only. persist=False keeps project rows unchanged."""
    leaked = set(FORBIDDEN_MODEL_INPUT_COLUMNS).intersection(project.__dict__.keys())
    if leaked:
        raise RuntimeError(f"Project row unexpectedly contains label columns: {sorted(leaked)}")
    return assess_project_cost(session, project.id, persist=False)


def run_cost_intelligence_evaluation(
    *,
    session: Session | None = None,
    synthetic_csv: Path | None = None,
) -> list[EvaluationRow]:
    own_session = session is None
    session = session or get_session_factory()()
    try:
        labels = load_held_out_labels(synthetic_csv)
        rows: list[EvaluationRow] = []
        for case_id, project in select_real_evaluation_projects(session):
            result = assess_without_label_leakage(session, project)
            rows.append(
                _row_from_result(
                    dataset="REAL",
                    case_id=case_id,
                    result=result,
                    constituency=project.constituency or "",
                    category=project.category or "",
                    held_out=None,
                )
            )
        for case_id, project in select_hybrid_evaluation_projects(session, labels):
            result = assess_without_label_leakage(session, project)
            rows.append(
                _row_from_result(
                    dataset="HYBRID",
                    case_id=case_id,
                    result=result,
                    constituency=project.constituency or "",
                    category=project.category or "",
                    held_out=labels.get(project.internal_project_id),
                )
            )
        return rows
    finally:
        if own_session:
            session.close()


def format_evaluation_rows(rows: Sequence[EvaluationRow]) -> str:
    lines: list[str] = []
    for index, row in enumerate(rows, start=1):
        lines.append(f"[{index}] {row.dataset} / {row.case_id}")
        lines.append(f"    project_id={row.project_id}")
        lines.append(f"    internal_project_id={row.internal_project_id}")
        lines.append(f"    constituency={row.constituency} category={row.category}")
        lines.append(f"    peer_scope={row.peer_scope}")
        lines.append(f"    peer_count={row.peer_count}")
        lines.append(f"    peer_quality={row.peer_quality}")
        lines.append(f"    similarity_rationale={row.similarity_rationale}")
        lines.append(f"    expected_cost={row.expected_cost}")
        lines.append(
            f"    expected_range={row.expected_range_low}-{row.expected_range_high}"
        )
        lines.append(f"    actual_allocation={row.actual_allocation}")
        lines.append(f"    deviation_percentage={row.deviation_percentage}")
        lines.append(f"    cost_anomaly_score={row.cost_anomaly_score}")
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


def evaluation_payload(rows: Sequence[EvaluationRow]) -> list[dict[str, object]]:
    return [asdict(row) for row in rows]


def synthetic_csv_exists() -> bool:
    return DEFAULT_OUTPUT_CSV.exists()


def repo_root() -> Path:
    return REPO_ROOT
