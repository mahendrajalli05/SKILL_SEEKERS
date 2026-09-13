"""Extract fusion slots from Evidence Objects.

Does not reimplement Cost, Time, Overlap, or Compliance scoring.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from app.domain.enums import (
    DataMode,
    EvidenceDisposition,
    EvidenceSeverity,
    RiskSignalState,
)
from app.domain.schemas.evidence import EvidenceObject
from app.engines.fusion.constants import (
    COMPLIANCE_EXTRA_RULE_CAP,
    COMPLIANCE_EXTRA_RULE_POINTS,
    COMPLIANCE_SEVERITY_SCORE,
    FORBIDDEN_MODEL_INPUT_COLUMNS,
    FUTURE_SIGNAL_WEIGHTS,
    FUTURE_UNAVAILABLE_REASON,
    INCONCLUSIVE_SIGNAL_REASON,
    INTEGRATED_WEIGHTS,
    MISSING_INTEGRATED_REASON,
    NOT_ASSESSABLE_REASON,
    OBJECT_CONFIDENCE_BLEND,
    PEER_QUALITY_BLEND,
    SIGNAL_DISPLAY_NAMES,
    SIGNAL_TYPE_TO_SLOT,
)
from app.engines.fusion.errors import FusionError
from app.engines.fusion.types import SignalContribution
from app.evidence.constants import FRAUD_CLAIM_PATTERN
from app.evidence.validate import reject_fraud_claims, reject_synthetic_label_inputs
from app.evidence.errors import EvidenceValidationError

_FRAUD_RE = re.compile(FRAUD_CLAIM_PATTERN, re.IGNORECASE)
_HELD_OUT_KEYS = frozenset(
    {
        "scenario_type",
        "demo_case_id",
        "mixed_signals",
        "anomaly_notes",
        "overlap_group_id",
        "coordinate_source",
    }
)


def _fact_map(obj: EvidenceObject) -> dict[str, object]:
    return {fact.key: fact.value for fact in obj.evidence_facts}


def _fact_int(obj: EvidenceObject, key: str) -> int | None:
    value = _fact_map(obj).get(key)
    if value is None or value == "":
        return None
    try:
        return int(float(value))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def reject_fusion_inputs(objects: Sequence[EvidenceObject]) -> None:
    """Held-out labels and fraud claims must not enter fusion."""
    for obj in objects:
        try:
            reject_synthetic_label_inputs(obj)
            reject_fraud_claims(obj)
        except EvidenceValidationError as exc:
            raise FusionError(str(exc)) from exc
        keys = {fact.key for fact in obj.evidence_facts}
        leaked = sorted((_HELD_OUT_KEYS | FORBIDDEN_MODEL_INPUT_COLUMNS).intersection(keys))
        if leaked:
            raise FusionError(
                "Synthetic scenario labels must not appear as fusion inputs: "
                + ", ".join(leaked)
            )
        blob = " ".join(
            [
                obj.finding,
                obj.explanation,
                *[str(fact.key) for fact in obj.evidence_facts],
            ]
        )
        if _FRAUD_RE.search(blob):
            raise FusionError(
                "Fusion must not consume evidence that claims fraud."
            )


def _support(obj: EvidenceObject) -> str:
    text = (obj.explanation or obj.finding or "").strip()
    if len(text) <= 280:
        return text
    return text[:277].rstrip() + "..."


def _quality(obj: EvidenceObject) -> float:
    confidence = max(0.0, min(1.0, float(obj.confidence)))
    peer_quality = _fact_int(obj, "peer_quality")
    if peer_quality is None:
        return confidence
    peer = max(0.0, min(100.0, float(peer_quality))) / 100.0
    return OBJECT_CONFIDENCE_BLEND * confidence + PEER_QUALITY_BLEND * peer


def _clip_score(value: float) -> int:
    if value <= 0:
        return 0
    if value >= 100:
        return 100
    return int(value + 0.5)


def compliance_signal_score(obj: EvidenceObject) -> int:
    """Map compliance Evidence Object fields. Does not re-run rules."""
    severity = obj.severity.value if isinstance(obj.severity, EvidenceSeverity) else str(obj.severity)
    base = COMPLIANCE_SEVERITY_SCORE.get(severity, 60)
    extra_count = max(0, len(obj.rule_ids) - 1)
    bonus = min(COMPLIANCE_EXTRA_RULE_CAP, extra_count * COMPLIANCE_EXTRA_RULE_POINTS)
    return _clip_score(base + bonus)


def _engine_score(obj: EvidenceObject) -> int | None:
    slot = SIGNAL_TYPE_TO_SLOT.get(obj.signal_type)
    if slot == "compliance":
        if obj.disposition == EvidenceDisposition.WHY_NOT_FLAGGED:
            return 0
        if obj.disposition == EvidenceDisposition.WHY_FLAGGED:
            return compliance_signal_score(obj)
        return None
    if obj.score is None:
        if obj.disposition == EvidenceDisposition.WHY_NOT_FLAGGED:
            return 0
        return None
    return _clip_score(float(obj.score))


def _slot_state(obj: EvidenceObject) -> tuple[RiskSignalState, str | None]:
    if obj.disposition == EvidenceDisposition.NOT_ASSESSABLE:
        return RiskSignalState.NOT_ASSESSABLE, NOT_ASSESSABLE_REASON
    if obj.disposition == EvidenceDisposition.INCONCLUSIVE:
        return RiskSignalState.NOT_ASSESSABLE, INCONCLUSIVE_SIGNAL_REASON
    if obj.disposition in {
        EvidenceDisposition.WHY_FLAGGED,
        EvidenceDisposition.WHY_NOT_FLAGGED,
    }:
        if _engine_score(obj) is None:
            return RiskSignalState.NOT_ASSESSABLE, NOT_ASSESSABLE_REASON
        return RiskSignalState.ASSESSABLE, None
    return RiskSignalState.UNAVAILABLE, MISSING_INTEGRATED_REASON


def contribution_from_evidence(obj: EvidenceObject) -> SignalContribution | None:
    slot = SIGNAL_TYPE_TO_SLOT.get(obj.signal_type)
    if slot is None:
        return None
    state, reason = _slot_state(obj)
    score = _engine_score(obj) if state == RiskSignalState.ASSESSABLE else None
    weight = INTEGRATED_WEIGHTS[slot]
    contribution = round(weight * float(score), 4) if score is not None else 0.0
    flagged = (
        state == RiskSignalState.ASSESSABLE
        and obj.disposition == EvidenceDisposition.WHY_FLAGGED
    )
    return SignalContribution(
        signal_id=slot,
        display_name=SIGNAL_DISPLAY_NAMES[slot],
        weight=weight,
        state=state,
        risk_score=score,
        contribution=contribution,
        evidence_confidence=_quality(obj),
        evidence_id=obj.evidence_id,
        disposition=obj.disposition.value,
        finding=obj.finding,
        support=_support(obj),
        unavailable_reason=reason,
        data_mode=obj.data_mode.value,
        flagged=flagged,
        peer_quality=_fact_int(obj, "peer_quality"),
    )


def _prefer_object(
    current: EvidenceObject | None,
    incoming: EvidenceObject,
    *,
    preferred_mode: DataMode | None,
) -> EvidenceObject:
    if current is None:
        return incoming
    if preferred_mode is not None:
        if incoming.data_mode == preferred_mode and current.data_mode != preferred_mode:
            return incoming
        if current.data_mode == preferred_mode and incoming.data_mode != preferred_mode:
            return current
    if incoming.evidence_id > current.evidence_id:
        return incoming
    return current


def select_unique_evidence(
    objects: Sequence[EvidenceObject],
    *,
    preferred_mode: DataMode | None = None,
) -> tuple[list[EvidenceObject], list[str]]:
    """One Evidence Object per fusion slot. Duplicate IDs are dropped."""
    seen_ids: set[str] = set()
    ignored: list[str] = []
    by_slot: dict[str, EvidenceObject] = {}
    for obj in objects:
        if obj.evidence_id in seen_ids:
            ignored.append(obj.evidence_id)
            continue
        seen_ids.add(obj.evidence_id)
        slot = SIGNAL_TYPE_TO_SLOT.get(obj.signal_type)
        if slot is None:
            continue
        previous = by_slot.get(slot)
        chosen = _prefer_object(previous, obj, preferred_mode=preferred_mode)
        if previous is not None:
            dropped = (
                previous.evidence_id
                if chosen.evidence_id != previous.evidence_id
                else obj.evidence_id
            )
            ignored.append(dropped)
        by_slot[slot] = chosen
    unique_ignored: list[str] = []
    seen_ignored: set[str] = set()
    for item in ignored:
        if item not in seen_ignored:
            unique_ignored.append(item)
            seen_ignored.add(item)
    ordered = [by_slot[slot] for slot in INTEGRATED_WEIGHTS if slot in by_slot]
    return ordered, unique_ignored


def _placeholder(
    signal_id: str,
    weight: float,
    state: RiskSignalState,
    reason: str,
) -> SignalContribution:
    return SignalContribution(
        signal_id=signal_id,
        display_name=SIGNAL_DISPLAY_NAMES[signal_id],
        weight=weight,
        state=state,
        risk_score=None,
        contribution=0.0,
        evidence_confidence=None,
        evidence_id=None,
        disposition=None,
        finding=None,
        support=None,
        unavailable_reason=reason,
        flagged=False,
    )


def build_signal_table(
    objects: Sequence[EvidenceObject],
    *,
    preferred_mode: DataMode | None = None,
) -> tuple[list[SignalContribution], list[str]]:
    """Full planned-weight table, including future unavailable slots."""
    reject_fusion_inputs(objects)
    unique, ignored = select_unique_evidence(objects, preferred_mode=preferred_mode)
    by_slot = {}
    for obj in unique:
        item = contribution_from_evidence(obj)
        if item is not None:
            by_slot[item.signal_id] = item

    signals: list[SignalContribution] = []
    for slot, weight in INTEGRATED_WEIGHTS.items():
        if slot in by_slot:
            signals.append(by_slot[slot])
        else:
            signals.append(
                _placeholder(
                    slot,
                    weight,
                    RiskSignalState.UNAVAILABLE,
                    MISSING_INTEGRATED_REASON,
                )
            )
    for slot, weight in FUTURE_SIGNAL_WEIGHTS.items():
        signals.append(
            _placeholder(
                slot,
                weight,
                RiskSignalState.NOT_YET_INTEGRATED,
                FUTURE_UNAVAILABLE_REASON,
            )
        )
    return signals, ignored
