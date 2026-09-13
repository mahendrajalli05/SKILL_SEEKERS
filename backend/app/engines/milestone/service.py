"""Milestone Advisor V1 orchestration.

Reuses Plan → Claim → Evidence, Evidence Object V1, and stored Cost / Time /
Overlap / Compliance / Geospatial / Image / Risk Fusion outputs.

Does not change those engines. Does not release funds or sanction payments.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from statistics import median
from typing import Any

from sqlalchemy.orm import Session

from app.domain.enums import (
    DataMode,
    EvidenceDisposition,
    MilestoneOfficerAction,
    MilestoneStatus,
    SignalType,
)
from app.engines.milestone.amounts import (
    amount_view,
    cumulative_for,
    expenditure_inconsistent,
    progress_inconsistent,
    remaining_for,
    total_planned_amount,
)
from app.engines.milestone.assess import HOLD, INCONCLUSIVE, INSPECT, PROCEED, assess
from app.engines.milestone.constants import (
    AUDIT_ASSESS,
    AUDIT_CREATE,
    AUDIT_DECISION,
    COMPLETION_SLOT,
    DECISION_ENTITY_TYPE,
    DEFAULT_MILESTONE_NAMES,
    ENGINE_NAME,
    ENGINE_VERSION,
    ENTITY_TYPE,
    FORBIDDEN_OUTPUT_TERMS,
    GOVERNANCE_NOTE,
    HYBRID_NOTICE,
    NO_PAYMENT_NOTE,
    SCORES_UNCHANGED_NOTE,
    SYNTHETIC_VALUE_NOTE,
    TIMELINE_SLOTS,
)
from app.engines.milestone.errors import MilestoneError
from app.engines.milestone.explain import build_why
from app.engines.milestone.repository import (
    add_decision,
    add_milestone,
    assessment_of,
    document_ids_of,
    evidence_ids_of,
    get_milestone,
    iso,
    list_decisions,
    list_milestones,
    now_utc,
    photo_ids_of,
    provenance_of,
    save_assessment,
    visible_mode,
)
from app.engines.milestone.types import (
    AssessmentInputs,
    IntelligenceSignal,
    MilestoneRecord,
    OfficerDecisionView,
    ProgressView,
    ProjectMilestones,
    TimelineNode,
)
from app.engines.pce.compare import (
    collect_missing,
    compare_plan_claim_evidence,
    overall_result,
)
from app.engines.pce.service import (
    assembled_claim_from_row,
    assembled_evidence,
    empty_claim,
    get_project_plan,
)
from app.engines.pce.types import AssembledClaim, AssembledEvidenceItem, ConsistencyStatus
from app.evidence.adapters.milestone import assessment_to_evidence
from app.evidence.constants import FRAUD_CLAIM_PATTERN
from app.evidence.provenance import build_provenance, build_source_ids
from app.evidence.repository import add_evidence_object, list_project_evidence
from app.models.artifacts import Claim, Document, Photo
from app.models.audit import AuditEvent
from app.models.fusion import FusionScore
from app.models.milestone import Milestone
from app.models.project import Project
from app.models.snapshot import DatasetSnapshot
from app.search.enrichment_display import enrichment_for

_FRAUD_RE = re.compile(FRAUD_CLAIM_PATTERN, re.IGNORECASE)
_DATE_ONLY = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_data_mode(value: str | DataMode | None, project: Project | None = None) -> DataMode:
    if project is not None and project.is_synthetic:
        return DataMode.SYNTHETIC
    if isinstance(value, DataMode):
        return value
    text = str(value or "").strip().upper().replace("-", "_")
    if text in {"HYBRID", "HYBRID_TEST", "HYBRIDTEST", "HYBRID_DEMO"}:
        return DataMode.HYBRID
    if text in {"SYNTHETIC"}:
        return DataMode.SYNTHETIC
    if text in {"REAL", "REAL_DATA"}:
        return DataMode.REAL
    return DataMode.REAL


def reject_forbidden_text(*values: object) -> None:
    blob = "\n".join("" if item is None else str(item) for item in values).casefold()
    if _FRAUD_RE.search(blob):
        raise MilestoneError(
            "Milestone Advisor must not claim fraud or use fraud language.",
            code="fraud_language_forbidden",
            status_code=422,
        )
    for term in FORBIDDEN_OUTPUT_TERMS:
        if term in blob:
            raise MilestoneError(
                "Milestone Advisor must not output fraud conclusions or payment-release language.",
                code="forbidden_output_term",
                status_code=422,
            )


def _parse_date(value: str | date | None) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError as exc:
        raise MilestoneError("Dates must be ISO YYYY-MM-DD.", code="invalid_date", status_code=422) from exc


def _source_type(data_mode: DataMode):
    from app.domain.enums import SourceType

    if data_mode == DataMode.SYNTHETIC:
        return SourceType.SYNTHETIC_TEST_RECORD
    if data_mode == DataMode.HYBRID:
        return SourceType.HYBRID_ENRICHMENT
    return SourceType.MILESTONE_CLAIM


def _snapshot(session: Session, project: Project) -> DatasetSnapshot | None:
    if project.snapshot_id:
        return session.get(DatasetSnapshot, project.snapshot_id)
    return project.snapshot


def _fusion_snapshot(session: Session, project_id: int) -> dict[str, Any]:
    from sqlalchemy import select

    row = session.scalars(select(FusionScore).where(FusionScore.project_id == project_id)).first()
    if row is None:
        return {
            "investigation_priority": None,
            "evidence_confidence": None,
            "recommended_action": None,
        }
    return {
        "investigation_priority": row.investigation_priority,
        "evidence_confidence": row.evidence_confidence,
        "recommended_action": row.recommended_action,
    }


def _audit(session: Session, *, actor_role: str, action: str, entity_type: str, entity_id: str, payload: dict[str, Any]) -> None:
    session.add(
        AuditEvent(
            actor_role=actor_role,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=json.dumps(payload, sort_keys=True, default=str),
        )
    )


def _filter_mode(data_mode: DataMode, item_mode: str | None) -> bool:
    return visible_mode(data_mode, item_mode)


def _ordered_amount_pairs(rows: list[Milestone]) -> list[tuple[int | None, float | None]]:
    return [(row.milestone_number, row.planned_amount) for row in rows]


def _default_status(*, completion_claimed: bool | None, claimed_progress: float | None) -> str:
    if completion_claimed or (claimed_progress is not None and claimed_progress > 0):
        return MilestoneStatus.CLAIMED.value
    return MilestoneStatus.PLANNED.value


def _current_milestone(rows: list[Milestone]) -> Milestone | None:
    if not rows:
        return None
    open_states = {
        MilestoneStatus.PLANNED.value,
        MilestoneStatus.CLAIMED.value,
        MilestoneStatus.UNDER_REVIEW.value,
        MilestoneStatus.HOLD.value,
        MilestoneStatus.INSPECT.value,
    }
    for row in rows:
        if row.status not in {MilestoneStatus.PROCEED.value, MilestoneStatus.COMPLETED.value}:
            if row.status in open_states or row.status:
                return row
    return rows[-1]


def _planned_progress(number: int | None, rows: list[Milestone]) -> float | None:
    numbers = [row.milestone_number for row in rows if row.milestone_number is not None]
    if number is None or not numbers:
        return None
    maximum = max(numbers)
    if maximum <= 0:
        return None
    return round(100.0 * float(number) / float(maximum), 2)


def _evidence_supported_progress(
    plan_quantity: float | None,
    evidence_items: list[AssembledEvidenceItem],
) -> float | None:
    quantities = [
        float(item.observed_quantity)
        for item in evidence_items
        if item.observed_quantity is not None
    ]
    if plan_quantity is None or not quantities or float(plan_quantity) == 0:
        return None
    observed = float(median(quantities))
    return round(100.0 * observed / float(plan_quantity), 2)


def _select_claim(
    session: Session,
    project: Project,
    row: Milestone,
    data_mode: DataMode,
) -> AssembledClaim:
    from app.engines.pce.repository import list_claims

    claims = [
        item
        for item in list_claims(session, project.id)
        if _filter_mode(data_mode, item.data_mode)
    ]
    chosen: Claim | None = None
    if row.claim_id:
        chosen = next((item for item in claims if item.id == row.claim_id), None)
    if chosen is None and row.milestone_name:
        chosen = next(
            (
                item
                for item in claims
                if (item.milestone_label or "").strip().casefold()
                == (row.milestone_name or "").strip().casefold()
            ),
            None,
        )
    if chosen is None and claims:
        chosen = claims[0]
    if chosen is None:
        return empty_claim(project, data_mode)
    return assembled_claim_from_row(project, chosen)


def _milestone_evidence(
    project: Project,
    row: Milestone,
    documents: list[Document],
    photos: list[Photo],
    data_mode: DataMode,
) -> list[AssembledEvidenceItem]:
    all_items = assembled_evidence(project, documents, photos, data_mode)
    linked_docs = set(document_ids_of(row))
    linked_photos = set(photo_ids_of(row))
    if not linked_docs and not linked_photos:
        return all_items
    selected: list[AssembledEvidenceItem] = []
    for item in all_items:
        if item.document_id is not None and item.document_id in linked_docs:
            selected.append(item)
        elif item.photo_id is not None and item.photo_id in linked_photos:
            selected.append(item)
    return selected or all_items


def _signals_from_evidence(items: list[Any], data_mode: DataMode) -> list[IntelligenceSignal]:
    selected = []
    for item in items:
        mode = item.data_mode.value if hasattr(item.data_mode, "value") else str(item.data_mode)
        if data_mode == DataMode.REAL and mode != DataMode.REAL.value:
            continue
        signal = item.signal_type.value if hasattr(item.signal_type, "value") else str(item.signal_type)
        disposition = item.disposition.value if hasattr(item.disposition, "value") else str(item.disposition or "")
        flagged = disposition == EvidenceDisposition.WHY_FLAGGED.value
        selected.append(
            IntelligenceSignal(
                engine=str(item.engine_name),
                signal_type=signal,
                disposition=disposition,
                finding=item.finding,
                score=item.score,
                flagged=flagged,
                data_mode=mode,
            )
        )
    return selected


def _flagged(signals: list[IntelligenceSignal], engine: str, signal_type: str | None = None) -> bool:
    for item in signals:
        if item.engine != engine:
            continue
        if signal_type and item.signal_type != signal_type:
            continue
        if item.flagged:
            return True
    return False


def _geo_mismatch(signals: list[IntelligenceSignal]) -> bool:
    for item in signals:
        if item.signal_type in {
            SignalType.GEOSPATIAL_LOCATION_MISMATCH.value,
            "GEOSPATIAL_LOCATION_MISMATCH",
        }:
            return True
        if item.engine == "geo" and item.flagged:
            return True
    return False


def _image_reuse(signals: list[IntelligenceSignal]) -> tuple[bool, bool]:
    reuse = False
    exact = False
    for item in signals:
        if item.signal_type in {
            SignalType.IMAGE_POTENTIAL_REUSE.value,
            "IMAGE_POTENTIAL_REUSE",
        }:
            reuse = True
        if item.signal_type in {
            SignalType.IMAGE_EXACT_DUPLICATE.value,
            "IMAGE_EXACT_DUPLICATE",
        }:
            exact = True
    return reuse, exact


def _claimed_expenditure(
    row: Milestone,
    claim: AssembledClaim,
    data_mode: DataMode,
    project: Project,
) -> tuple[float | None, bool]:
    if row.claimed_expenditure is not None:
        return float(row.claimed_expenditure), bool(row.synthetic)
    if claim.claimed_expenditure is not None:
        return float(claim.claimed_expenditure), data_mode != DataMode.REAL and claim.data_mode != DataMode.REAL
    if data_mode == DataMode.REAL:
        return None, False
    enrichment = enrichment_for(project.internal_project_id)
    if enrichment is not None and enrichment.expenditure_amount is not None:
        return float(enrichment.expenditure_amount), True
    return None, False


def _evidence_expenditure(items: list[AssembledEvidenceItem]) -> float | None:
    values = [float(item.observed_expenditure) for item in items if item.observed_expenditure is not None]
    if not values:
        return None
    return float(median(values))


def build_timeline(rows: list[Milestone]) -> list[TimelineNode]:
    by_number: dict[int, Milestone] = {
        row.milestone_number: row for row in rows if row.milestone_number is not None
    }
    nodes: list[TimelineNode] = []
    for index, slot in enumerate(TIMELINE_SLOTS, start=1):
        row = by_number.get(index)
        if row is None:
            nodes.append(
                TimelineNode(
                    slot=slot,
                    milestone_id=None,
                    milestone_number=index,
                    milestone_name=DEFAULT_MILESTONE_NAMES.get(index, slot),
                    status=None,
                    planned_date=None,
                    claim=None,
                    evidence="not recorded",
                    result=None,
                    officer_action=None,
                    recorded=False,
                )
            )
            continue
        assessment = assessment_of(row)
        evidence_status = None if assessment is None else assessment.get("evidence_status")
        claim_label = None
        if row.completion_claimed:
            claim_label = "completion claimed"
        elif row.claimed_progress is not None:
            claim_label = f"claimed {row.claimed_progress}%"
        nodes.append(
            TimelineNode(
                slot=slot,
                milestone_id=row.id,
                milestone_number=row.milestone_number,
                milestone_name=row.milestone_name or slot,
                status=row.status,
                planned_date=iso(row.target_date),
                claim=claim_label,
                evidence=evidence_status or ("linked" if document_ids_of(row) or photo_ids_of(row) else "none"),
                result=row.recommendation,
                officer_action=row.officer_action,
                recorded=True,
            )
        )
    last = rows[-1] if rows else None
    completion_action = last.officer_action if last and last.status == MilestoneStatus.COMPLETED.value else None
    nodes.append(
        TimelineNode(
            slot=COMPLETION_SLOT,
            milestone_id=None,
            milestone_number=None,
            milestone_name="COMPLETION",
            status=last.status if last and last.status == MilestoneStatus.COMPLETED.value else None,
            planned_date=iso(last.target_date) if last else None,
            claim=None,
            evidence=None,
            result=last.recommendation if last and last.status == MilestoneStatus.COMPLETED.value else None,
            officer_action=completion_action,
            recorded=bool(last and last.status == MilestoneStatus.COMPLETED.value),
        )
    )
    return nodes


def _decision_view(row) -> OfficerDecisionView:
    return OfficerDecisionView(
        id=row.id,
        milestone_id=row.milestone_id,
        project_id=row.project_id,
        action=row.action,
        reason=row.reason,
        actor_role=row.actor_role,
        created_at=iso(row.created_at),
        investigation_priority_snapshot=row.investigation_priority_snapshot,
        evidence_confidence_snapshot=row.evidence_confidence_snapshot,
        recommended_action_snapshot=row.recommended_action_snapshot,
        scores_unchanged=bool(row.scores_unchanged),
        funds_released=False,
        payment_executed=False,
    )


def to_record(
    session: Session,
    project: Project,
    row: Milestone,
    data_mode: DataMode,
    *,
    siblings: list[Milestone] | None = None,
) -> MilestoneRecord:
    siblings = siblings if siblings is not None else [
        item for item in list_milestones(session, project.id) if visible_mode(data_mode, item.data_mode)
    ]
    pairs = _ordered_amount_pairs(siblings)
    cumulative = cumulative_for(
        milestone_number=row.milestone_number,
        planned_amount=row.planned_amount,
        ordered=pairs,
    )
    total = total_planned_amount(pairs)
    remaining = remaining_for(cumulative_amount=cumulative, total_planned=total)
    assessment = assessment_of(row)
    fusion = _fusion_snapshot(session, project.id)
    hybrid = data_mode in {DataMode.HYBRID, DataMode.SYNTHETIC}
    claimed_exp, claimed_synth = _claimed_expenditure(
        row, empty_claim(project, data_mode), data_mode, project
    )
    if row.claimed_expenditure is not None:
        claimed_exp = float(row.claimed_expenditure)
        claimed_synth = bool(row.synthetic)
    amounts = amount_view(
        planned_amount=row.planned_amount,
        cumulative_amount=cumulative,
        claimed_expenditure=claimed_exp if claimed_exp is not None else row.claimed_expenditure,
        remaining_planned_amount=remaining,
        claimed_expenditure_synthetic=claimed_synth,
        data_mode=data_mode.value,
    )
    progress = ProgressView(
        claimed_progress=row.claimed_progress,
        evidence_supported_progress=(assessment or {}).get("evidence_supported_progress"),
        planned_progress=_planned_progress(row.milestone_number, siblings),
        schedule_mismatch=bool((assessment or {}).get("schedule_mismatch")),
        schedule_note=(assessment or {}).get("schedule_note"),
        claimed_progress_available=row.claimed_progress is not None,
        evidence_supported_available=(assessment or {}).get("evidence_supported_progress") is not None,
        planned_progress_available=_planned_progress(row.milestone_number, siblings) is not None,
    )
    return MilestoneRecord(
        milestone_id=row.id,
        project_id=project.id,
        internal_project_id=project.internal_project_id,
        milestone_number=row.milestone_number,
        milestone_name=row.milestone_name,
        description=row.description,
        planned_amount=row.planned_amount,
        cumulative_amount=cumulative,
        remaining_planned_amount=remaining,
        target_date=iso(row.target_date),
        completion_claimed=row.completion_claimed,
        claimed_progress=row.claimed_progress,
        claimed_expenditure=amounts.claimed_expenditure,
        status=row.status,
        data_mode=row.data_mode,
        synthetic=bool(row.synthetic),
        provenance=provenance_of(row),
        claim_id=row.claim_id,
        document_ids=document_ids_of(row),
        photo_ids=photo_ids_of(row),
        evidence_ids=evidence_ids_of(row),
        recommendation=row.recommendation,
        evidence_status=None if assessment is None else assessment.get("evidence_status"),
        amounts=amounts,
        progress=progress,
        assessment=assessment,
        officer_action=row.officer_action,
        officer_reason=row.officer_reason,
        officer_actor_role=row.officer_actor_role,
        officer_acted_at=iso(row.officer_acted_at),
        decisions=[_decision_view(item) for item in list_decisions(session, row.id)],
        work_description=project.work_description,
        investigation_priority=fusion["investigation_priority"],
        evidence_confidence=fusion["evidence_confidence"],
        hybrid_notice=HYBRID_NOTICE if hybrid else None,
        enrichment_used=hybrid and (row.synthetic or data_mode != DataMode.REAL),
        engine_version=ENGINE_VERSION,
        engine_name=ENGINE_NAME,
        governance_note=GOVERNANCE_NOTE,
    )


def create_milestone(
    session: Session,
    project: Project,
    payload: dict[str, Any],
    data_mode: DataMode,
) -> MilestoneRecord:
    reject_forbidden_text(*payload.values())
    if data_mode == DataMode.REAL and project.is_synthetic:
        raise MilestoneError(
            "SYNTHETIC test projects cannot be recorded as REAL.",
            code="mode_conflict",
            status_code=422,
        )
    number = payload.get("milestone_number")
    if number is not None:
        try:
            number = int(number)
        except (TypeError, ValueError) as exc:
            raise MilestoneError("milestone_number must be an integer.", code="invalid_number", status_code=422) from exc
        if number < 1:
            raise MilestoneError("milestone_number must be >= 1.", code="invalid_number", status_code=422)
    existing = [
        item
        for item in list_milestones(session, project.id)
        if visible_mode(data_mode, item.data_mode) and item.milestone_number == number and number is not None
    ]
    if existing:
        raise MilestoneError(
            "A milestone with this number already exists for this project and data mode.",
            code="duplicate_milestone_number",
            status_code=422,
        )
    synthetic = bool(payload.get("synthetic"))
    if data_mode == DataMode.REAL:
        synthetic = False
    if data_mode == DataMode.HYBRID and payload.get("planned_amount") is not None and payload.get("synthetic") is None:
        synthetic = True if payload.get("from_enrichment") else synthetic
    snapshot = _snapshot(session, project)
    source_type = _source_type(data_mode)
    extra_ids = [f"milestone:{number}"] if number is not None else []
    provenance_obj = build_provenance(
        project,
        data_mode=data_mode,
        source_type=source_type,
        source_ids=build_source_ids(project.internal_project_id, extra_ids),
        snapshot=snapshot,
        extra_notes=(
            "Officer-recorded milestone. SARVSAKSHI workflow only; not an official MPLADS status. "
            + (SYNTHETIC_VALUE_NOTE if synthetic or data_mode != DataMode.REAL else GOVERNANCE_NOTE)
        ),
    )
    completion_claimed = payload.get("completion_claimed")
    claimed_progress = payload.get("claimed_progress")
    status = str(payload.get("status") or _default_status(completion_claimed=completion_claimed, claimed_progress=claimed_progress))
    allowed_status = {item.value for item in MilestoneStatus}
    if status not in allowed_status:
        raise MilestoneError("Unsupported milestone status.", code="invalid_status", status_code=422)
    name = payload.get("milestone_name") or (DEFAULT_MILESTONE_NAMES.get(number) if number else None)
    row = add_milestone(
        session,
        project.id,
        milestone_number=number,
        milestone_name=name,
        description=payload.get("description"),
        planned_amount=payload.get("planned_amount"),
        cumulative_amount=None,
        target_date=_parse_date(payload.get("target_date")),
        completion_claimed=completion_claimed,
        claimed_progress=claimed_progress,
        claimed_expenditure=payload.get("claimed_expenditure") if data_mode != DataMode.REAL or payload.get("claimed_expenditure") is not None else payload.get("claimed_expenditure"),
        status=status,
        data_mode=data_mode,
        provenance=provenance_obj.model_dump(mode="json"),
        claim_id=payload.get("claim_id"),
        document_ids=list(payload.get("document_ids") or []),
        photo_ids=list(payload.get("photo_ids") or []),
        synthetic=synthetic,
    )
    siblings = [item for item in list_milestones(session, project.id) if visible_mode(data_mode, item.data_mode)]
    cumulative = cumulative_for(
        milestone_number=row.milestone_number,
        planned_amount=row.planned_amount,
        ordered=_ordered_amount_pairs(siblings),
    )
    row.cumulative_amount = cumulative
    session.flush()
    _audit(
        session,
        actor_role=str(payload.get("actor_role") or "officer"),
        action=AUDIT_CREATE,
        entity_type=ENTITY_TYPE,
        entity_id=str(row.id),
        payload={
            "project_id": project.id,
            "milestone_id": row.id,
            "data_mode": data_mode.value,
            "funds_released": False,
            "payment_executed": False,
        },
    )
    return to_record(session, project, row, data_mode, siblings=siblings)


def list_project_milestones(session: Session, project: Project, data_mode: DataMode) -> ProjectMilestones:
    rows = [item for item in list_milestones(session, project.id) if visible_mode(data_mode, item.data_mode)]
    records = [to_record(session, project, row, data_mode, siblings=rows) for row in rows]
    current = _current_milestone(rows)
    fusion = _fusion_snapshot(session, project.id)
    hybrid = data_mode in {DataMode.HYBRID, DataMode.SYNTHETIC}
    return ProjectMilestones(
        project_id=project.id,
        internal_project_id=project.internal_project_id,
        work_description=project.work_description,
        data_mode=data_mode.value,
        current_milestone_id=None if current is None else current.id,
        current_milestone_name=None if current is None else current.milestone_name,
        current_recommendation=None if current is None else current.recommendation,
        items=records,
        timeline=build_timeline(rows),
        investigation_priority=fusion["investigation_priority"],
        evidence_confidence=fusion["evidence_confidence"],
        hybrid_notice=HYBRID_NOTICE if hybrid else None,
        enrichment_used=hybrid,
        engine_version=ENGINE_VERSION,
        engine_name=ENGINE_NAME,
        governance_note=GOVERNANCE_NOTE,
    )


def get_milestone_record(session: Session, milestone_id: int, data_mode: DataMode | None = None) -> MilestoneRecord:
    row = get_milestone(session, milestone_id)
    if row is None:
        raise MilestoneError("Milestone not found.", code="not_found", status_code=404)
    project = session.get(Project, row.project_id)
    if project is None:
        raise MilestoneError("Project not found.", code="not_found", status_code=404)
    mode = parse_data_mode(data_mode or row.data_mode, project)
    if not visible_mode(mode, row.data_mode):
        raise MilestoneError("Milestone not found.", code="not_found", status_code=404)
    return to_record(session, project, row, mode)


def assess_milestone(
    session: Session,
    milestone_id: int,
    data_mode: DataMode,
    *,
    persist: bool = True,
) -> MilestoneRecord:
    row = get_milestone(session, milestone_id)
    if row is None:
        raise MilestoneError("Milestone not found.", code="not_found", status_code=404)
    project = session.get(Project, row.project_id)
    if project is None:
        raise MilestoneError("Project not found.", code="not_found", status_code=404)
    mode = parse_data_mode(data_mode, project)
    from app.engines.pce.repository import list_claims, list_documents, list_photos

    plan = get_project_plan(session, project, mode)
    claim = _select_claim(session, project, row, mode)
    if row.claimed_progress is not None and claim.claimed_progress_percent is None:
        claim.claimed_progress_percent = row.claimed_progress
    if row.completion_claimed and not claim.claimed_completion_state:
        claim.claimed_completion_state = "completion claimed"
        claim.recorded = True
    if row.claimed_progress is not None or row.completion_claimed or row.claimed_expenditure is not None:
        claim.recorded = True
    documents = list_documents(session, project.id)
    photos = list_photos(session, project.id)
    evidence_items = _milestone_evidence(project, row, documents, photos, mode)
    comparisons = compare_plan_claim_evidence(plan, claim, evidence_items)
    pce_overall = overall_result(comparisons, has_claim=claim.recorded, has_evidence=bool(evidence_items))
    missing = collect_missing(comparisons, plan, claim)
    stored_evidence = list_project_evidence(session, project.id)
    signals = _signals_from_evidence(stored_evidence, mode)
    reuse, exact = _image_reuse(signals)
    claimed_exp, claimed_synth = _claimed_expenditure(row, claim, mode, project)
    if row.claimed_expenditure is not None:
        claimed_exp = float(row.claimed_expenditure)
        claimed_synth = bool(row.synthetic)
    evidence_exp = _evidence_expenditure(evidence_items)
    evidence_progress = _evidence_supported_progress(plan.dimensions_value, evidence_items)
    claimed_progress = row.claimed_progress if row.claimed_progress is not None else claim.claimed_progress_percent
    schedule_mismatch = _flagged(signals, "time")
    pce_mismatch = pce_overall == ConsistencyStatus.MISMATCH
    inputs = AssessmentInputs(
        has_claim=bool(claim.recorded or row.completion_claimed or claimed_progress is not None),
        has_required_evidence=bool(evidence_items),
        pce_result=pce_overall.value,
        geo_mismatch=_geo_mismatch(signals),
        image_reuse=reuse,
        exact_duplicate=exact,
        expenditure_inconsistency=(
            False
            if pce_mismatch
            else expenditure_inconsistent(claimed_exp, row.planned_amount or plan.milestone_amount, evidence_exp)
        ),
        progress_inconsistency=(
            False if pce_mismatch else progress_inconsistent(claimed_progress, evidence_progress)
        ),
        schedule_mismatch=schedule_mismatch,
        cost_flagged=_flagged(signals, "cost"),
        compliance_flagged=_flagged(signals, "compliance"),
        overlap_flagged=_flagged(signals, "overlap"),
    )
    result = assess(inputs, data_mode=mode.value)
    supporting = []
    if claim.recorded:
        supporting.append("Milestone claim is recorded.")
    if evidence_items:
        kinds = sorted({item.evidence_kind for item in evidence_items})
        supporting.append("Supporting attachments present: " + ", ".join(kinds) + ".")
    if pce_overall == ConsistencyStatus.CONSISTENT:
        supporting.append("Plan → Claim → Evidence is CONSISTENT.")
    intel_notes = [
        f"{item.engine}: {item.finding}"
        for item in signals
        if item.engine in {"cost", "time", "overlap", "compliance", "geo", "image"}
        and item.finding
    ]
    result = build_why(inputs, result, supporting=supporting, missing=missing, signals=intelligence_notes(intel_notes, signals))
    reject_forbidden_text(result.explanation, result.recommendation, *result.independent_concerns)
    payload = result.as_dict()
    payload["evidence_supported_progress"] = evidence_progress
    payload["schedule_mismatch"] = schedule_mismatch
    payload["schedule_note"] = (
        "Time Intelligence reported a schedule mismatch. Time scoring was not recalculated."
        if schedule_mismatch
        else "Time Intelligence reused as a stored input. Duration is not fabricated in REAL mode."
    )
    payload["claimed_expenditure_synthetic"] = claimed_synth
    payload["pce_missing_information"] = missing
    payload["comparison_statuses"] = {item.comparison_id: item.status.value for item in comparisons}
    next_status = row.status
    if row.status in {MilestoneStatus.PLANNED.value, MilestoneStatus.CLAIMED.value}:
        next_status = MilestoneStatus.UNDER_REVIEW.value
    if persist:
        snapshot = _snapshot(session, project)
        obj = assessment_to_evidence(project, row, result, data_mode=mode, snapshot=snapshot)
        stored = add_evidence_object(session, obj)
        ids = [stored.evidence_id] if stored.evidence_id else []
        ids.extend(evidence_ids_of(row))
        save_assessment(
            session,
            row,
            recommendation=result.recommendation,
            assessment=payload,
            evidence_ids=ids,
            cumulative_amount=cumulative_for(
                milestone_number=row.milestone_number,
                planned_amount=row.planned_amount,
                ordered=_ordered_amount_pairs(
                    [item for item in list_milestones(session, project.id) if visible_mode(mode, item.data_mode)]
                ),
            ),
            status=next_status,
        )
        _audit(
            session,
            actor_role="system",
            action=AUDIT_ASSESS,
            entity_type=ENTITY_TYPE,
            entity_id=str(row.id),
            payload={
                "project_id": project.id,
                "milestone_id": row.id,
                "recommendation": result.recommendation,
                "funds_released": False,
                "payment_executed": False,
                "automatic_sanction": False,
            },
        )
    record = to_record(session, project, row, mode)
    reject_forbidden_text(record.recommendation, (record.assessment or {}).get("explanation"))
    return record


def intelligence_notes(findings: list[str], signals: list[IntelligenceSignal]) -> list[str]:
    notes = list(findings)
    if not notes:
        for item in signals:
            if item.finding:
                notes.append(f"{item.engine}: {item.finding}")
    return notes[:12]


def record_officer_action(
    session: Session,
    milestone_id: int,
    *,
    action: str,
    reason: str | None,
    actor_role: str | None,
    data_mode: DataMode,
) -> MilestoneRecord:
    reject_forbidden_text(action, reason)
    value = str(action or "").strip().upper().replace(" ", "_")
    if value in {"NEED_MORE_INFO", "NEED_MORE_INFORMATION"}:
        value = MilestoneOfficerAction.NEED_MORE_INFORMATION.value
    allowed = {item.value for item in MilestoneOfficerAction}
    if value not in allowed:
        raise MilestoneError(
            "Unsupported officer action. Use PROCEED, HOLD, INSPECT, or NEED_MORE_INFORMATION.",
            code="invalid_decision",
            status_code=422,
        )
    row = get_milestone(session, milestone_id)
    if row is None:
        raise MilestoneError("Milestone not found.", code="not_found", status_code=404)
    project = session.get(Project, row.project_id)
    if project is None:
        raise MilestoneError("Project not found.", code="not_found", status_code=404)
    mode = parse_data_mode(data_mode, project)
    before = _fusion_snapshot(session, project.id)
    snapshot = _snapshot(session, project)
    provenance_obj = build_provenance(
        project,
        data_mode=mode,
        source_type=_source_type(mode),
        source_ids=build_source_ids(project.internal_project_id, [f"milestone:{row.id}"]),
        snapshot=snapshot,
        extra_notes=f"{SCORES_UNCHANGED_NOTE} {NO_PAYMENT_NOTE}",
    )
    decision = add_decision(
        session,
        milestone_id=row.id,
        project_id=project.id,
        action=value,
        reason=reason,
        actor_role=(actor_role or "officer").strip() or "officer",
        data_mode=mode,
        investigation_priority_snapshot=before["investigation_priority"],
        evidence_confidence_snapshot=before["evidence_confidence"],
        recommended_action_snapshot=before["recommended_action"],
        provenance=provenance_obj.model_dump(mode="json"),
    )
    row.officer_action = value
    row.officer_reason = reason
    row.officer_actor_role = decision.actor_role
    row.officer_acted_at = now_utc()
    if value == MilestoneOfficerAction.NEED_MORE_INFORMATION.value:
        row.status = MilestoneStatus.UNDER_REVIEW.value
    elif value == MilestoneOfficerAction.PROCEED.value:
        siblings = [item for item in list_milestones(session, project.id) if visible_mode(mode, item.data_mode)]
        last_number = max((item.milestone_number or 0) for item in siblings) if siblings else None
        if row.completion_claimed and last_number and row.milestone_number == last_number:
            row.status = MilestoneStatus.COMPLETED.value
        else:
            row.status = MilestoneStatus.PROCEED.value
    elif value == MilestoneOfficerAction.HOLD.value:
        row.status = MilestoneStatus.HOLD.value
    elif value == MilestoneOfficerAction.INSPECT.value:
        row.status = MilestoneStatus.INSPECT.value
    session.flush()
    after = _fusion_snapshot(session, project.id)
    if (
        after["investigation_priority"] != before["investigation_priority"]
        or after["evidence_confidence"] != before["evidence_confidence"]
        or after["recommended_action"] != before["recommended_action"]
    ):
        raise MilestoneError(
            "Officer decision must not change stored intelligence scores.",
            code="score_mutation_forbidden",
            status_code=500,
        )
    _audit(
        session,
        actor_role=decision.actor_role or "officer",
        action=AUDIT_DECISION,
        entity_type=DECISION_ENTITY_TYPE,
        entity_id=str(decision.id),
        payload={
            "project_id": project.id,
            "milestone_id": row.id,
            "decision_id": decision.id,
            "action": value,
            "investigation_priority_snapshot": before["investigation_priority"],
            "evidence_confidence_snapshot": before["evidence_confidence"],
            "scores_unchanged": True,
            "funds_released": False,
            "payment_executed": False,
            "automatic_sanction": False,
            "note": SCORES_UNCHANGED_NOTE,
        },
    )
    record = to_record(session, project, row, mode)
    reject_forbidden_text(record.officer_action, record.officer_reason)
    return record
