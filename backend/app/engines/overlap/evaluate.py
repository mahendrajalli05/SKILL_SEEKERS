"""Held-out Overlap Intelligence evaluation on real works and HYBRID GPS.

The SQLite ``project`` table supplies observed fields.
HYBRID coordinates come from the synthetic CSV.
HYBRID ``scenario_type`` / ``overlap_group_id`` are attached AFTER scoring.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import REPO_ROOT
from app.db import get_session_factory
from app.engines.cost.evaluate import DEMO_INTERNAL_IDS
from app.engines.overlap.constants import FORBIDDEN_MODEL_INPUT_COLUMNS
from app.engines.overlap.embeddings import HashedTokenEmbedder
from app.engines.overlap.enrichment import HeldOutOverlapLabel, load_held_out_overlap_labels, load_hybrid_gps
from app.engines.overlap.service import assess_project_overlap
from app.engines.overlap.types import OverlapIntelligenceResult, OverlapMode
from app.models.project import Project
from app.pipeline.synthetic import DEFAULT_OUTPUT_CSV


@dataclass
class OverlapEvaluationRow:
    dataset: str
    case_id: str
    project_id: int
    internal_project_id: str
    overlap_mode: str
    constituency: str
    category: str
    candidate_count: int
    match_count: int
    top_linked_internal_project_id: str | None
    top_semantic_similarity: float | None
    top_category_match: bool | None
    top_constituency_match: bool | None
    top_amount_similarity: float | None
    top_date_gap_days: int | None
    top_location_similarity: float | None
    top_gps_distance_m: float | None
    overlap_score: int | None
    evidence_confidence: int
    flagged: bool
    outcome: str
    geographic_evidence_available: bool
    embedding_backend: str
    explanation: str
    held_out_scenario_type: str | None = None
    held_out_demo_case_id: str | None = None
    held_out_overlap_group_id: str | None = None


def _first(session: Session, stmt) -> Project | None:
    return session.scalars(stmt.limit(1)).first()


def _require(row: Project | None, label: str) -> Project:
    if row is None:
        raise LookupError(f"Evaluation case {label} was not found in SQLite.")
    return row


def select_real_overlap_projects(session: Session) -> list[tuple[str, Project]]:
    tanks = _require(
        _first(
            session,
            select(Project).where(
                Project.state == "Andhra Pradesh",
                Project.work_description.like("%water tank%"),
                Project.is_synthetic == False,  # noqa: E712
            ).order_by(Project.id.asc()),
        ),
        "real_ap_water_tanks",
    )
    roads = _require(
        _first(
            session,
            select(Project).where(
                Project.state == "Andhra Pradesh",
                Project.work_description.like("%roads%"),
                Project.is_synthetic == False,  # noqa: E712
            ).order_by(Project.id.asc()),
        ),
        "real_ap_roads",
    )
    with_place = _require(
        _first(
            session,
            select(Project).where(
                Project.state == "Andhra Pradesh",
                Project.village != "",
                Project.village.is_not(None),
                Project.is_synthetic == False,  # noqa: E712
            ).order_by(Project.id.asc()),
        ),
        "real_ap_with_place",
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
    kurnool = _require(
        _first(
            session,
            select(Project).where(
                Project.state == "Andhra Pradesh",
                Project.constituency == "KURNOOL",
                Project.is_synthetic == False,  # noqa: E712
            ).order_by(Project.id.asc()),
        ),
        "real_kurnool",
    )
    eluru = _require(
        _first(
            session,
            select(Project).where(
                Project.state == "Andhra Pradesh",
                Project.constituency == "ELURU",
                Project.allocation_amount > 1_000_000,
                Project.is_synthetic == False,  # noqa: E712
            ).order_by(Project.id.asc()),
        ),
        "real_eluru_high_amount",
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
    rooms = _first(
        session,
        select(Project).where(
            Project.state == "Andhra Pradesh",
            Project.work_description.like("%school%"),
            Project.is_synthetic == False,  # noqa: E712
        ).order_by(Project.id.asc()),
    )
    if rooms is None:
        rooms = _require(
            _first(
                session,
                select(Project).where(
                    Project.state == "Andhra Pradesh",
                    Project.work_description.like("%hall%"),
                    Project.is_synthetic == False,  # noqa: E712
                ).order_by(Project.id.asc()),
            ),
            "real_ap_class_rooms",
        )
        rooms_label = "real_ap_halls"
    else:
        rooms_label = "real_ap_school"
    chosen = [
        ("real_ap_water_tanks", tanks),
        ("real_ap_roads", roads),
        ("real_ap_with_place", with_place),
        ("real_ap_sitting_rs", sitting),
        ("real_ap_repair", repair),
        ("real_kurnool", kurnool),
        ("real_eluru_high_amount", eluru),
        ("real_ap_completed", completed),
        ("real_ap_ongoing", ongoing),
        (rooms_label, rooms),
    ]
    seen: set[int] = set()
    unique: list[tuple[str, Project]] = []
    for case_id, row in chosen:
        if row.id in seen:
            continue
        seen.add(row.id)
        unique.append((case_id, row))
    if len(unique) < 10:
        extras = session.scalars(
            select(Project)
            .where(
                Project.state == "Andhra Pradesh",
                Project.is_synthetic == False,  # noqa: E712
            )
            .order_by(Project.id.asc())
        ).all()
        for row in extras:
            if row.id in seen:
                continue
            unique.append((f"real_ap_extra_{row.id}", row))
            seen.add(row.id)
            if len(unique) >= 10:
                break
    return unique[:10]


def select_hybrid_overlap_projects(
    session: Session,
    labels: dict[str, HeldOutOverlapLabel],
) -> list[tuple[str, Project]]:
    chosen: list[tuple[str, Project]] = []
    used: set[str] = set()

    groups: dict[str, list[str]] = defaultdict(list)
    for internal_id, label in labels.items():
        if label.overlap_group_id:
            groups[label.overlap_group_id].append(internal_id)
    overlap_pair: list[str] = []
    for members in groups.values():
        if len(members) >= 2:
            overlap_pair = sorted(members)[:2]
            break

    def add(case_id: str, internal_id: str) -> None:
        if internal_id in used:
            return
        row = session.scalars(
            select(Project).where(Project.internal_project_id == internal_id)
        ).first()
        if row is None:
            return
        chosen.append((case_id, row))
        used.add(internal_id)

    if overlap_pair:
        add("hybrid_clear_overlap_a", overlap_pair[0])
        add("hybrid_clear_overlap_b", overlap_pair[1])
    add("hybrid_demo_clean", DEMO_INTERNAL_IDS["CLEAN"])
    add("hybrid_demo_overbill", DEMO_INTERNAL_IDS["OVERBILL"])
    add("hybrid_demo_stuck", DEMO_INTERNAL_IDS["STUCK"])
    add("hybrid_demo_ghost", DEMO_INTERNAL_IDS["GHOST"])

    for case_id, scenario in (
        ("hybrid_normal", "NORMAL"),
        ("hybrid_overlap_only", "OVERLAP"),
        ("hybrid_mixed_overlap", "MIXED"),
        ("hybrid_cost_anomaly", "COST_ANOMALY"),
    ):
        for internal_id, label in labels.items():
            if internal_id in used:
                continue
            if case_id == "hybrid_mixed_overlap":
                if "OVERLAP" in (label.mixed_signals or "") and label.scenario_type == "MIXED":
                    add(case_id, internal_id)
                    break
            elif label.scenario_type == scenario:
                add(case_id, internal_id)
                break

    if len(chosen) < 10:
        for internal_id in sorted(labels):
            if len(chosen) >= 10:
                break
            add(f"hybrid_extra_{len(chosen)}", internal_id)
    return chosen[:10]


def _row_from_result(
    *,
    dataset: str,
    case_id: str,
    result: OverlapIntelligenceResult,
    constituency: str,
    category: str,
    held_out: HeldOutOverlapLabel | None,
) -> OverlapEvaluationRow:
    top = result.matches[0] if result.matches else None
    return OverlapEvaluationRow(
        dataset=dataset,
        case_id=case_id,
        project_id=result.project_id,
        internal_project_id=result.internal_project_id,
        overlap_mode=result.overlap_mode.value,
        constituency=constituency,
        category=category,
        candidate_count=result.candidate_count,
        match_count=result.match_count,
        top_linked_internal_project_id=top.linked_internal_project_id if top else None,
        top_semantic_similarity=top.semantic_similarity if top else None,
        top_category_match=top.category_match if top else None,
        top_constituency_match=top.constituency_match if top else None,
        top_amount_similarity=top.amount_similarity if top else None,
        top_date_gap_days=top.date_gap_days if top else None,
        top_location_similarity=top.location_similarity if top else None,
        top_gps_distance_m=top.gps_distance_m if top else None,
        overlap_score=result.overlap_score,
        evidence_confidence=result.evidence_confidence,
        flagged=result.flagged,
        outcome=result.outcome.value,
        geographic_evidence_available=result.geographic_evidence_available,
        embedding_backend=result.embedding_backend,
        explanation=result.explanation,
        held_out_scenario_type=held_out.scenario_type if held_out else None,
        held_out_demo_case_id=held_out.demo_case_id if held_out else None,
        held_out_overlap_group_id=held_out.overlap_group_id if held_out else None,
    )


def assess_without_label_leakage(
    session: Session,
    project: Project,
    *,
    mode: OverlapMode,
    embedder: HashedTokenEmbedder | None = None,
) -> OverlapIntelligenceResult:
    leaked = set(FORBIDDEN_MODEL_INPUT_COLUMNS).intersection(project.__dict__.keys())
    if leaked:
        raise RuntimeError(f"Project row unexpectedly contains label columns: {sorted(leaked)}")
    return assess_project_overlap(
        session,
        project.id,
        mode=mode,
        persist=False,
        embedder=embedder or HashedTokenEmbedder(),
    )


def run_overlap_intelligence_evaluation(
    *,
    session: Session | None = None,
    synthetic_csv: Path | None = None,
) -> list[OverlapEvaluationRow]:
    own_session = session is None
    session = session or get_session_factory()()
    embedder = HashedTokenEmbedder()
    try:
        labels = load_held_out_overlap_labels(synthetic_csv)
        load_hybrid_gps(synthetic_csv)
        rows: list[OverlapEvaluationRow] = []
        for case_id, project in select_real_overlap_projects(session):
            result = assess_without_label_leakage(
                session, project, mode=OverlapMode.REAL, embedder=embedder
            )
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
        for case_id, project in select_hybrid_overlap_projects(session, labels):
            result = assess_without_label_leakage(
                session, project, mode=OverlapMode.HYBRID_TEST, embedder=embedder
            )
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


def format_evaluation_rows(rows: Sequence[OverlapEvaluationRow]) -> str:
    lines: list[str] = []
    for index, row in enumerate(rows, start=1):
        lines.append(f"[{index}] {row.dataset} / {row.case_id}")
        lines.append(f"    project_id={row.project_id}")
        lines.append(f"    internal_project_id={row.internal_project_id}")
        lines.append(f"    overlap_mode={row.overlap_mode}")
        lines.append(f"    constituency={row.constituency} category={row.category}")
        lines.append(f"    candidate_count={row.candidate_count} match_count={row.match_count}")
        lines.append(f"    top_linked={row.top_linked_internal_project_id}")
        lines.append(f"    semantic_similarity={row.top_semantic_similarity}")
        lines.append(f"    category_match={row.top_category_match}")
        lines.append(f"    constituency_match={row.top_constituency_match}")
        lines.append(f"    amount_similarity={row.top_amount_similarity}")
        lines.append(f"    date_gap_days={row.top_date_gap_days}")
        lines.append(f"    location_similarity={row.top_location_similarity}")
        lines.append(f"    gps_distance_m={row.top_gps_distance_m}")
        lines.append(f"    overlap_score={row.overlap_score}")
        lines.append(f"    evidence_confidence={row.evidence_confidence}")
        lines.append(f"    flagged={row.flagged} outcome={row.outcome}")
        lines.append(f"    geographic_evidence_available={row.geographic_evidence_available}")
        lines.append(f"    embedding_backend={row.embedding_backend}")
        if row.dataset == "HYBRID":
            lines.append(
                "    held_out_label="
                f"scenario_type={row.held_out_scenario_type} "
                f"demo_case_id={row.held_out_demo_case_id or '(none)'} "
                f"overlap_group_id={row.held_out_overlap_group_id or '(none)'}"
            )
        lines.append(f"    explanation={row.explanation}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def evaluation_payload(rows: Sequence[OverlapEvaluationRow]) -> list[dict[str, object]]:
    return [asdict(row) for row in rows]


def synthetic_csv_exists() -> bool:
    return DEFAULT_OUTPUT_CSV.exists()


def repo_root() -> Path:
    return REPO_ROOT
