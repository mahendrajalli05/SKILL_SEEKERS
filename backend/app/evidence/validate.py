"""Validate canonical Evidence Objects.

Rejects incomplete objects, missing provenance, REAL/SYNTHETIC mix-ups,
held-out synthetic labels, and fraud claims.
"""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import ValidationError

from app.domain.enums import DataMode, SourceType
from app.domain.schemas.evidence import EvidenceObject
from app.evidence.constants import FORBIDDEN_EVIDENCE_INPUT_COLUMNS, FRAUD_CLAIM_PATTERN
from app.evidence.errors import EvidenceValidationError

_FRAUD_RE = re.compile(FRAUD_CLAIM_PATTERN, re.IGNORECASE)


def _walk_text(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (int, float, bool)):
        return [str(value)]
    if isinstance(value, dict):
        texts: list[str] = []
        for key, item in value.items():
            texts.append(str(key))
            texts.extend(_walk_text(item))
        return texts
    if isinstance(value, (list, tuple, set)):
        texts: list[str] = []
        for item in value:
            texts.extend(_walk_text(item))
        return texts
    return [str(value)]


def collect_evidence_text(obj: EvidenceObject) -> str:
    payload = obj.model_dump(mode="json")
    return "\n".join(_walk_text(payload))


def reject_fraud_claims(obj: EvidenceObject) -> None:
    blob = collect_evidence_text(obj)
    if _FRAUD_RE.search(blob):
        raise EvidenceValidationError(
            "Evidence objects must not claim fraud or use fraud language."
        )


def reject_synthetic_label_inputs(obj: EvidenceObject) -> None:
    fact_keys = {fact.key for fact in obj.evidence_facts}
    leaked = sorted(FORBIDDEN_EVIDENCE_INPUT_COLUMNS.intersection(fact_keys))
    if leaked:
        raise EvidenceValidationError(
            "Synthetic scenario labels must not appear as evidence inputs: "
            + ", ".join(leaked)
        )
    blob = collect_evidence_text(obj).casefold()
    forbidden_mentions = []
    for column in sorted(FORBIDDEN_EVIDENCE_INPUT_COLUMNS):
        if column in {"record_mode", "enrichment_source"}:
            continue
        token = column.casefold()
        if token in blob and token in {
            "scenario_type",
            "demo_case_id",
            "mixed_signals",
            "anomaly_notes",
            "overlap_group_id",
            "coordinate_source",
            "synthetic_record_id",
        }:
            forbidden_mentions.append(column)
    if forbidden_mentions:
        raise EvidenceValidationError(
            "Synthetic scenario labels must not appear as evidence inputs: "
            + ", ".join(forbidden_mentions)
        )


def reject_mode_conflicts(obj: EvidenceObject) -> None:
    if obj.data_mode == DataMode.REAL:
        if obj.source_type == SourceType.SYNTHETIC_TEST_RECORD:
            raise EvidenceValidationError("REAL evidence must never be marked SYNTHETIC.")
        if obj.provenance.enrichment_used:
            raise EvidenceValidationError(
                "REAL evidence must not use synthetic enrichment as an input."
            )
        if obj.source_type == SourceType.HYBRID_ENRICHMENT:
            raise EvidenceValidationError(
                "REAL evidence must remain distinguishable from HYBRID enrichment."
            )
    if obj.data_mode == DataMode.HYBRID:
        if obj.source_type == SourceType.SYNTHETIC_TEST_RECORD:
            raise EvidenceValidationError(
                "HYBRID evidence is linked to a real work and must not be labelled "
                "as a fully SYNTHETIC test record."
            )
        if not obj.provenance.enrichment_used:
            raise EvidenceValidationError(
                "HYBRID evidence must record that synthetic enrichment was used."
            )
    if obj.data_mode == DataMode.SYNTHETIC:
        if obj.source_type == SourceType.MPLADS_PROJECT_RECORD:
            raise EvidenceValidationError(
                "SYNTHETIC test evidence must not be labelled as a real MPLADS record."
            )
        note = obj.provenance.notes.upper()
        if "SYNTHETIC" not in note:
            raise EvidenceValidationError(
                "SYNTHETIC evidence provenance must state that the record is SYNTHETIC."
            )


def reject_missing_provenance(obj: EvidenceObject) -> None:
    if not obj.provenance.source_ids:
        raise EvidenceValidationError("Evidence provenance source_ids must not be empty.")
    if not obj.source_ids:
        raise EvidenceValidationError("Evidence source_ids must not be empty.")
    if obj.provenance.internal_project_id not in obj.source_ids:
        raise EvidenceValidationError(
            "source_ids must preserve the subject internal_project_id."
        )
    if not obj.provenance.notes.strip():
        raise EvidenceValidationError("Evidence provenance notes are required.")
    if obj.data_mode == DataMode.REAL:
        if not (obj.provenance.source_dataset or obj.provenance.source_url):
            raise EvidenceValidationError(
                "REAL evidence must cite a source dataset or source URL."
            )


def reject_fact_source_loss(obj: EvidenceObject) -> None:
    for fact in obj.evidence_facts:
        if not fact.source.strip():
            raise EvidenceValidationError(
                f"Evidence fact '{fact.key}' is missing source provenance."
            )


def validate_evidence(obj: EvidenceObject) -> EvidenceObject:
    """Return the object if valid. Raise EvidenceValidationError otherwise."""
    try:
        checked = EvidenceObject.model_validate(obj.model_dump())
    except ValidationError as exc:
        raise EvidenceValidationError(str(exc)) from exc
    reject_missing_provenance(checked)
    reject_mode_conflicts(checked)
    reject_synthetic_label_inputs(checked)
    reject_fraud_claims(checked)
    reject_fact_source_loss(checked)
    return checked


def parse_and_validate(payload: dict[str, Any]) -> EvidenceObject:
    try:
        obj = EvidenceObject.model_validate(payload)
    except ValidationError as exc:
        raise EvidenceValidationError(str(exc)) from exc
    return validate_evidence(obj)


def dump_json(obj: EvidenceObject) -> str:
    return json.dumps(obj.model_dump(mode="json"), sort_keys=True, default=str)
