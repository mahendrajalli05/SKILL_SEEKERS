"""Persist and load canonical Evidence Objects using existing tables.

Does not write fusion_score. Does not invent government fields.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import (
    DataMode,
    EvidenceDisposition,
    EvidenceEngine,
    EvidenceFactKind,
    EvidenceSeverity,
    EvidenceStatus,
    SignalType,
    SourceType,
)
from app.domain.schemas.evidence import EvidenceFact, EvidenceObject, EvidenceProvenance
from app.evidence.constants import DISPOSITION_TO_STATUS
from app.evidence.errors import EvidenceValidationError
from app.evidence.facts import parse_fact_value, render_fact_value
from app.evidence.validate import validate_evidence
from app.models.evidence import EvidenceFactRow, EvidenceObjectRow


def _json_dump(value: object) -> str:
    return json.dumps(value, sort_keys=True, default=str)


def _json_load(value: str | None, default: object) -> object:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def _status_for(obj: EvidenceObject) -> EvidenceStatus:
    if obj.status:
        return obj.status
    return DISPOSITION_TO_STATUS[obj.disposition]


def delete_engine_evidence(
    session: Session,
    project_id: int,
    engine: str | EvidenceEngine,
) -> None:
    engine_value = engine.value if isinstance(engine, EvidenceEngine) else engine
    existing = session.scalars(
        select(EvidenceObjectRow).where(
            EvidenceObjectRow.project_id == project_id,
            EvidenceObjectRow.engine == engine_value,
        )
    ).all()
    for row in existing:
        for fact in list(row.facts):
            session.delete(fact)
        session.delete(row)
    session.flush()


def add_evidence_object(session: Session, obj: EvidenceObject) -> EvidenceObjectRow:
    """Validate and insert one Evidence Object without deleting sibling rows.

    Used for document/image attachment recording. Engine assessments still
    use ``persist_evidence_object``, which replaces that engine's rows.
    """
    checked = validate_evidence(obj)
    existing = session.scalars(
        select(EvidenceObjectRow).where(EvidenceObjectRow.evidence_id == checked.evidence_id)
    ).first()
    if existing is not None:
        for fact in list(existing.facts):
            session.delete(fact)
        session.delete(existing)
        session.flush()
    return _insert_evidence_row(session, checked)


def persist_evidence_object(
    session: Session,
    obj: EvidenceObject,
    *,
    replace_engine: str | EvidenceEngine | None = None,
) -> EvidenceObjectRow:
    """Validate and replace the current evidence row for this engine/project."""
    checked = validate_evidence(obj)
    engine_value = (
        replace_engine.value
        if isinstance(replace_engine, EvidenceEngine)
        else (replace_engine or checked.engine_name)
    )
    delete_engine_evidence(session, checked.project_id, engine_value)
    return _insert_evidence_row(session, checked, engine_value=str(engine_value))


def _insert_evidence_row(
    session: Session,
    checked: EvidenceObject,
    *,
    engine_value: str | None = None,
) -> EvidenceObjectRow:
    status = _status_for(checked)
    created_at = checked.created_at or datetime.now(timezone.utc)
    engine_name = str(checked.engine_name)
    row = EvidenceObjectRow(
        evidence_id=checked.evidence_id,
        project_id=checked.project_id,
        engine=engine_value or engine_name,
        engine_name=engine_name,
        engine_version=checked.engine_version,
        evidence_type=checked.signal_type.value
        if isinstance(checked.signal_type, SignalType)
        else str(checked.signal_type),
        signal_type=checked.signal_type.value
        if isinstance(checked.signal_type, SignalType)
        else str(checked.signal_type),
        status=status.value,
        disposition=checked.disposition.value,
        severity=checked.severity.value,
        finding=checked.finding,
        summary=checked.explanation,
        explanation=checked.explanation,
        score=None if checked.score is None else float(checked.score),
        confidence=checked.confidence,
        source_type=checked.source_type.value
        if isinstance(checked.source_type, SourceType)
        else str(checked.source_type),
        source_ids_json=_json_dump(checked.source_ids),
        data_mode=checked.data_mode.value,
        provenance_json=_json_dump(checked.provenance.model_dump(mode="json")),
        comparables_json=_json_dump(checked.comparables),
        rule_ids_json=_json_dump(checked.rule_ids),
        guideline_refs_json=_json_dump(checked.guideline_refs),
        created_at=created_at,
    )
    row.facts = [
        EvidenceFactRow(
            key=fact.key,
            value=render_fact_value(fact.value),
            source=fact.source,
            fact_kind=fact.kind.value,
            statement=fact.statement,
        )
        for fact in checked.evidence_facts
    ]
    session.add(row)
    session.flush()
    return row


def row_to_evidence(row: EvidenceObjectRow) -> EvidenceObject:
    if not row.evidence_id:
        raise EvidenceValidationError("Stored evidence row is missing evidence_id.")
    if not row.provenance_json:
        raise EvidenceValidationError("Stored evidence row is missing provenance.")
    provenance = EvidenceProvenance.model_validate(_json_load(row.provenance_json, {}))
    facts = [
        EvidenceFact(
            id=fact.id,
            key=fact.key,
            value=parse_fact_value(fact.value),
            source=fact.source,
            kind=EvidenceFactKind(fact.fact_kind or EvidenceFactKind.OBSERVATION.value),
            statement=fact.statement,
        )
        for fact in row.facts
    ]
    signal = row.signal_type or row.evidence_type
    data_mode = DataMode(row.data_mode) if row.data_mode else provenance.data_mode
    disposition = (
        EvidenceDisposition(row.disposition)
        if row.disposition
        else EvidenceDisposition.INCONCLUSIVE
    )
    source_ids = _json_load(row.source_ids_json, list(provenance.source_ids))
    return validate_evidence(
        EvidenceObject(
            evidence_id=row.evidence_id,
            project_id=row.project_id,
            signal_type=SignalType(signal),
            finding=row.finding or row.summary or row.explanation or "",
            severity=EvidenceSeverity(row.severity),
            score=row.score,
            confidence=row.confidence if row.confidence is not None else 0.0,
            source_type=SourceType(row.source_type or provenance.source_type),
            source_ids=list(source_ids) if isinstance(source_ids, list) else provenance.source_ids,
            evidence_facts=facts,
            explanation=row.explanation or row.summary or "",
            engine_name=row.engine_name or row.engine,
            engine_version=row.engine_version,
            created_at=row.created_at,
            data_mode=data_mode,
            provenance=provenance,
            disposition=disposition,
            status=EvidenceStatus(row.status) if row.status else EvidenceStatus.INCONCLUSIVE,
            comparables=list(_json_load(row.comparables_json, [])),
            rule_ids=list(_json_load(row.rule_ids_json, [])),
            guideline_refs=list(_json_load(row.guideline_refs_json, [])),
        )
    )


def list_project_evidence(
    session: Session,
    project_id: int,
    *,
    engine: str | None = None,
    data_mode: str | None = None,
    signal_type: str | None = None,
) -> list[EvidenceObject]:
    stmt = select(EvidenceObjectRow).where(EvidenceObjectRow.project_id == project_id)
    if engine:
        stmt = stmt.where(EvidenceObjectRow.engine == engine)
    if data_mode:
        stmt = stmt.where(EvidenceObjectRow.data_mode == data_mode)
    if signal_type:
        stmt = stmt.where(
            (EvidenceObjectRow.signal_type == signal_type)
            | (EvidenceObjectRow.evidence_type == signal_type)
        )
    stmt = stmt.order_by(EvidenceObjectRow.engine, EvidenceObjectRow.id)
    rows = session.scalars(stmt).all()
    return [row_to_evidence(row) for row in rows]
