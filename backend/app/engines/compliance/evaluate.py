"""Held-out Compliance Engine evaluation on real works and HYBRID execution fields.

The SQLite ``project`` table supplies observed fields.
HYBRID dates/amounts come from the synthetic CSV.
HYBRID ``scenario_type`` / ``demo_case_id`` are attached AFTER scoring.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.engines.cost.evaluate import DEMO_INTERNAL_IDS
from app.engines.compliance.constants import FORBIDDEN_MODEL_INPUT_COLUMNS
from app.engines.compliance.enrichment import (
    HeldOutComplianceLabel,
    load_held_out_compliance_labels,
    load_hybrid_compliance_fields,
)
from app.engines.compliance.service import assess_project_compliance
from app.engines.compliance.types import ComplianceIntelligenceResult, ComplianceMode
from app.db import get_session_factory
from app.models.project import Project
from app.pipeline.synthetic import DEFAULT_OUTPUT_CSV


@dataclass
class ComplianceEvaluationRow:
    dataset: str
    case_id: str
    project_id: int
    internal_project_id: str
    compliance_mode: str
    constituency: str
    category: str
    status: str
    compliance_status: str
    flagged: bool
    severity: str
    triggered_rule_ids: list[str]
    non_triggered_rule_ids: list[str]
    not_assessable_rule_ids: list[str]
    explanation: str
    sample_rule_id: str
    sample_rule_status: str
    sample_rule_explanation: str
    held_out_scenario_type: str | None = None
    held_out_demo_case_id: str | None = None


def _first(session: Session, stmt) -> Project | None:
    return session.scalars(stmt.limit(1)).first()


def _require(row: Project | None, label: str) -> Project:
    if row is None:
        raise LookupError(f"Evaluation case {label} was not found in SQLite.")
    return row


def select_real_compliance_projects(session: Session) -> list[tuple[str, Project]]:
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
    repair = _require(
        _first(
            session,
            select(Project).where(
                Project.state == "Andhra Pradesh",
                Project.category == "Repair and Renovation",
                Project.is_synthetic == False,  # noqa: E712
            ).order_by(Project.id.asc()),
        ),
        "real_ap_repair",
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
        ("real_ap_completed", completed),
        ("real_ap_repair", repair),
        ("real_ap_sitting_rs", sitting),
    ]


def select_hybrid_compliance_projects(
    session: Session,
    labels: dict[str, HeldOutComplianceLabel],
) -> list[tuple[str, Project]]:
    selected: list[tuple[str, Project]] = []
    for demo_id, internal_id in (
        ("CLEAN", DEMO_INTERNAL_IDS["CLEAN"]),
        ("OVERBILL", DEMO_INTERNAL_IDS["OVERBILL"]),
        ("STUCK", DEMO_INTERNAL_IDS["STUCK"]),
        ("GHOST", DEMO_INTERNAL_IDS["GHOST"]),
    ):
        row = _require(
            _first(
                session,
                select(Project).where(Project.internal_project_id == internal_id),
            ),
            f"hybrid_demo_{demo_id.lower()}",
        )
        selected.append((f"hybrid_demo_{demo_id.lower()}", row))
    cost = None
    for internal_id, label in labels.items():
        if label.scenario_type == "COST_ANOMALY" and not label.demo_case_id:
            cost = _first(
                session,
                select(Project).where(Project.internal_project_id == internal_id),
            )
            if cost is not None:
                selected.append(("hybrid_cost_anomaly", cost))
                break
    if cost is None:
        raise LookupError("Evaluation case hybrid_cost_anomaly was not found.")
    return selected


def _sample_rule(result: ComplianceIntelligenceResult) -> tuple[str, str, str]:
    if result.triggered_rules:
        item = result.triggered_rules[0]
    elif result.not_assessable_rules:
        item = result.not_assessable_rules[0]
    elif result.non_triggered_rules:
        item = result.non_triggered_rules[0]
    else:
        return "", "", ""
    return item.rule_id, item.status.value, item.explanation


def _row_from_result(
    *,
    dataset: str,
    case_id: str,
    result: ComplianceIntelligenceResult,
    constituency: str,
    category: str,
    status: str,
    held_out: HeldOutComplianceLabel | None,
) -> ComplianceEvaluationRow:
    sample_id, sample_status, sample_explanation = _sample_rule(result)
    return ComplianceEvaluationRow(
        dataset=dataset,
        case_id=case_id,
        project_id=result.project_id,
        internal_project_id=result.internal_project_id,
        compliance_mode=result.compliance_mode.value,
        constituency=constituency,
        category=category,
        status=status,
        compliance_status=result.compliance_status.value,
        flagged=result.flagged,
        severity=result.severity.value,
        triggered_rule_ids=list(result.triggered_rule_ids),
        non_triggered_rule_ids=[item.rule_id for item in result.non_triggered_rules],
        not_assessable_rule_ids=list(result.not_assessable_rule_ids),
        explanation=result.explanation,
        sample_rule_id=sample_id,
        sample_rule_status=sample_status,
        sample_rule_explanation=sample_explanation,
        held_out_scenario_type=held_out.scenario_type if held_out else None,
        held_out_demo_case_id=held_out.demo_case_id if held_out else None,
    )


def assess_without_label_leakage(
    session: Session,
    project: Project,
    *,
    mode: ComplianceMode,
) -> ComplianceIntelligenceResult:
    leaked = set(FORBIDDEN_MODEL_INPUT_COLUMNS).intersection(project.__dict__.keys())
    if leaked:
        raise RuntimeError(f"Project row unexpectedly contains label columns: {sorted(leaked)}")
    return assess_project_compliance(session, project.id, mode=mode, persist=False)


def run_compliance_intelligence_evaluation(
    *,
    session: Session | None = None,
    synthetic_csv: Path | None = None,
) -> list[ComplianceEvaluationRow]:
    own_session = session is None
    session = session or get_session_factory()()
    try:
        labels = load_held_out_compliance_labels(synthetic_csv)
        load_hybrid_compliance_fields(synthetic_csv)
        rows: list[ComplianceEvaluationRow] = []
        for case_id, project in select_real_compliance_projects(session):
            result = assess_without_label_leakage(session, project, mode=ComplianceMode.REAL)
            rows.append(
                _row_from_result(
                    dataset="REAL",
                    case_id=case_id,
                    result=result,
                    constituency=project.constituency or "",
                    category=project.category or "",
                    status=project.status or "",
                    held_out=None,
                )
            )
        for case_id, project in select_hybrid_compliance_projects(session, labels):
            result = assess_without_label_leakage(
                session, project, mode=ComplianceMode.HYBRID_TEST
            )
            rows.append(
                _row_from_result(
                    dataset="HYBRID",
                    case_id=case_id,
                    result=result,
                    constituency=project.constituency or "",
                    category=project.category or "",
                    status=project.status or "",
                    held_out=labels.get(project.internal_project_id),
                )
            )
        return rows
    finally:
        if own_session:
            session.close()


def format_evaluation_rows(rows: Sequence[ComplianceEvaluationRow]) -> str:
    lines: list[str] = []
    for index, row in enumerate(rows, start=1):
        lines.append(f"[{index}] {row.dataset} / {row.case_id}")
        lines.append(f"    project_id={row.project_id}")
        lines.append(f"    internal_project_id={row.internal_project_id}")
        lines.append(f"    compliance_mode={row.compliance_mode}")
        lines.append(f"    constituency={row.constituency} category={row.category}")
        lines.append(f"    status={row.status}")
        lines.append(f"    compliance_status={row.compliance_status} flagged={row.flagged}")
        lines.append(f"    severity={row.severity}")
        lines.append(f"    triggered={','.join(row.triggered_rule_ids) or 'none'}")
        lines.append(f"    not_triggered={','.join(row.non_triggered_rule_ids) or 'none'}")
        lines.append(f"    not_assessable={','.join(row.not_assessable_rule_ids) or 'none'}")
        if row.dataset == "HYBRID":
            lines.append(
                "    held_out_label="
                f"scenario_type={row.held_out_scenario_type} "
                f"demo_case_id={row.held_out_demo_case_id or '(none)'}"
            )
        lines.append(
            f"    sample={row.sample_rule_id} {row.sample_rule_status}: "
            f"{row.sample_rule_explanation}"
        )
        lines.append(f"    explanation={row.explanation}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def evaluation_payload(rows: Sequence[ComplianceEvaluationRow]) -> list[dict[str, object]]:
    return [asdict(row) for row in rows]
