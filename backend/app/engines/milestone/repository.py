"""Persist and load Milestone Advisor V1 rows."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import DataMode
from app.models.milestone import Milestone, MilestoneDecision


def _dump(value: object) -> str:
    return json.dumps(value, sort_keys=True, default=str)


def _load_list(raw: str | None) -> list[int]:
    if not raw:
        return []
    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(loaded, list):
        return []
    out: list[int] = []
    for item in loaded:
        try:
            out.append(int(item))
        except (TypeError, ValueError):
            continue
    return out


def _load_str_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(loaded, list):
        return []
    return [str(item) for item in loaded if str(item).strip()]


def _load_obj(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def visible_mode(data_mode: DataMode, item_mode: str | None) -> bool:
    if data_mode == DataMode.REAL:
        return (item_mode or DataMode.REAL.value) == DataMode.REAL.value
    return True


def list_milestones(session: Session, project_id: int) -> list[Milestone]:
    rows = list(session.scalars(select(Milestone).where(Milestone.project_id == project_id)).all())
    rows.sort(key=lambda item: (item.milestone_number is None, item.milestone_number or 0, item.id))
    return rows


def get_milestone(session: Session, milestone_id: int) -> Milestone | None:
    return session.get(Milestone, milestone_id)


def add_milestone(
    session: Session,
    project_id: int,
    *,
    milestone_number: int | None,
    milestone_name: str | None,
    description: str | None,
    planned_amount: float | None,
    cumulative_amount: float | None,
    target_date: date | None,
    completion_claimed: bool | None,
    claimed_progress: float | None,
    claimed_expenditure: float | None,
    status: str,
    data_mode: DataMode,
    provenance: dict[str, Any],
    claim_id: int | None,
    document_ids: list[int],
    photo_ids: list[int],
    synthetic: bool,
) -> Milestone:
    row = Milestone(
        project_id=project_id,
        milestone_number=milestone_number,
        milestone_name=milestone_name,
        description=description,
        planned_amount=planned_amount,
        cumulative_amount=cumulative_amount,
        target_date=target_date,
        completion_claimed=completion_claimed,
        claimed_progress=claimed_progress,
        claimed_expenditure=claimed_expenditure,
        status=status,
        data_mode=data_mode.value if isinstance(data_mode, DataMode) else str(data_mode),
        provenance_json=_dump(provenance),
        claim_id=claim_id,
        document_ids_json=_dump(document_ids),
        photo_ids_json=_dump(photo_ids),
        evidence_ids_json=_dump([]),
        synthetic=bool(synthetic),
    )
    session.add(row)
    session.flush()
    return row


def save_assessment(
    session: Session,
    row: Milestone,
    *,
    recommendation: str,
    assessment: dict[str, Any],
    evidence_ids: list[str],
    cumulative_amount: float | None,
    status: str,
) -> None:
    row.recommendation = recommendation
    row.assessment_json = _dump(assessment)
    row.evidence_ids_json = _dump(evidence_ids)
    row.cumulative_amount = cumulative_amount
    row.status = status
    session.flush()


def add_decision(
    session: Session,
    *,
    milestone_id: int,
    project_id: int,
    action: str,
    reason: str | None,
    actor_role: str,
    data_mode: DataMode,
    investigation_priority_snapshot: int | None,
    evidence_confidence_snapshot: int | None,
    recommended_action_snapshot: str | None,
    provenance: dict[str, Any],
) -> MilestoneDecision:
    row = MilestoneDecision(
        milestone_id=milestone_id,
        project_id=project_id,
        action=action,
        reason=reason,
        actor_role=actor_role,
        data_mode=data_mode.value if isinstance(data_mode, DataMode) else str(data_mode),
        investigation_priority_snapshot=investigation_priority_snapshot,
        evidence_confidence_snapshot=evidence_confidence_snapshot,
        recommended_action_snapshot=recommended_action_snapshot,
        scores_unchanged=True,
        provenance_json=_dump(provenance),
    )
    session.add(row)
    session.flush()
    return row


def list_decisions(session: Session, milestone_id: int) -> list[MilestoneDecision]:
    return list(
        session.scalars(
            select(MilestoneDecision)
            .where(MilestoneDecision.milestone_id == milestone_id)
            .order_by(MilestoneDecision.created_at.desc(), MilestoneDecision.id.desc())
        ).all()
    )


def document_ids_of(row: Milestone) -> list[int]:
    return _load_list(row.document_ids_json)


def photo_ids_of(row: Milestone) -> list[int]:
    return _load_list(row.photo_ids_json)


def evidence_ids_of(row: Milestone) -> list[str]:
    return _load_str_list(row.evidence_ids_json)


def provenance_of(row: Milestone) -> dict[str, Any]:
    return _load_obj(row.provenance_json)


def assessment_of(row: Milestone) -> dict[str, Any] | None:
    loaded = _load_obj(row.assessment_json)
    return loaded or None


def iso(value: datetime | date | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
