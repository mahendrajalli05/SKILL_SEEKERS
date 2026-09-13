"""Map Evidence Objects into V2 catalog groups.

Does not reimplement Cost, Time, Overlap, Compliance, Graph, Image,
Forensics, Geo, Satellite, Document, PCE, Milestone, Citizen, or Need scoring.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from app.domain.enums import (
    DataMode,
    EvidenceDisposition,
    EvidenceSeverity,
    SignalType,
)
from app.domain.schemas.evidence import EvidenceObject
from app.engines.fusion_v2.constants import (
    CITIZEN_MULTI_CAP,
    CITIZEN_MULTI_MIN_REPORTS,
    CITIZEN_SINGLE_CAP,
    COMPLIANCE_EXTRA_RULE_CAP,
    COMPLIANCE_EXTRA_RULE_POINTS,
    COMPLIANCE_SEVERITY_SCORE,
    ENGINE_FLAG_THRESHOLD,
    FORBIDDEN_MODEL_INPUT_COLUMNS,
    FORENSICS_AI_CAP,
    GROUP_CITIZEN,
    GROUP_COMPLIANCE,
    GROUP_DISPLAY_NAMES,
    GROUP_NEED,
    GROUP_ORDER,
    GROUP_WEIGHTS,
    INCONCLUSIVE_REASON,
    LOW_CONFIDENCE_THRESHOLD,
    MAPPED_FLAGGED_SCORES,
    NEED_NOT_INVESTIGATION_REASON,
    NOT_ASSESSABLE_REASON,
    SIGNAL_TYPE_TO_GROUP,
    UNAVAILABLE_REASON,
)
from app.engines.fusion_v2.errors import FusionV2Error
from app.engines.fusion_v2.types import (
    EvidenceItemContribution,
    GroupContribution,
    V2EvidenceState,
    V2SignalPolarity,
)
from app.evidence.constants import FRAUD_CLAIM_PATTERN
from app.evidence.errors import EvidenceValidationError
from app.evidence.validate import reject_fraud_claims, reject_synthetic_label_inputs

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


def signal_value(obj: EvidenceObject) -> str:
    value = obj.signal_type
    return value.value if isinstance(value, SignalType) else str(value)


def group_for_signal(signal: str) -> str | None:
    return SIGNAL_TYPE_TO_GROUP.get(signal)


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


def _fact_text(obj: EvidenceObject, key: str) -> str:
    value = _fact_map(obj).get(key)
    if value is None:
        return ""
    return str(value)


def reject_fusion_v2_inputs(objects: Sequence[EvidenceObject]) -> None:
    for obj in objects:
        try:
            reject_synthetic_label_inputs(obj)
            reject_fraud_claims(obj)
        except EvidenceValidationError as exc:
            raise FusionV2Error(str(exc)) from exc
        keys = {fact.key for fact in obj.evidence_facts}
        leaked = sorted((_HELD_OUT_KEYS | FORBIDDEN_MODEL_INPUT_COLUMNS).intersection(keys))
        if leaked:
            raise FusionV2Error(
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
            raise FusionV2Error("Fusion V2 must not consume evidence that claims fraud.")


def clip_score(value: float) -> int:
    if value != value:  # NaN
        return 0
    if value <= 0:
        return 0
    if value >= 100:
        return 100
    return int(value + 0.5)


def compliance_mapped_score(obj: EvidenceObject) -> int | None:
    """Map compliance Evidence Object fields. Does not re-run rules."""
    if obj.disposition == EvidenceDisposition.WHY_NOT_FLAGGED:
        return 0
    if obj.disposition != EvidenceDisposition.WHY_FLAGGED:
        return None
    severity = obj.severity.value if isinstance(obj.severity, EvidenceSeverity) else str(obj.severity)
    base = COMPLIANCE_SEVERITY_SCORE.get(severity, 60)
    extra_count = max(0, len(obj.rule_ids) - 1)
    bonus = min(COMPLIANCE_EXTRA_RULE_CAP, extra_count * COMPLIANCE_EXTRA_RULE_POINTS)
    return clip_score(base + bonus)


def _citizen_cap(obj: EvidenceObject) -> int:
    n = _fact_int(obj, "accepted_report_count")
    if n is None:
        n = _fact_int(obj, "report_count")
    if n is None:
        n = _fact_int(obj, "independent_report_count")
    if n is not None and n >= CITIZEN_MULTI_MIN_REPORTS:
        return CITIZEN_MULTI_CAP
    return CITIZEN_SINGLE_CAP


def mapped_score(obj: EvidenceObject) -> int | None:
    """0–100 investigation signal, or None when not assessable."""
    group = group_for_signal(signal_value(obj))
    if group == GROUP_NEED:
        return None
    if obj.disposition == EvidenceDisposition.NOT_ASSESSABLE:
        return None
    if obj.disposition == EvidenceDisposition.INCONCLUSIVE:
        return None
    if group == GROUP_COMPLIANCE:
        return compliance_mapped_score(obj)
    signal = signal_value(obj)
    if signal == SignalType.SATELLITE_AVAILABILITY.value:
        return None
    if signal == SignalType.IMAGE_FORENSIC_INCONCLUSIVE.value:
        return None
    if signal == SignalType.GEOSPATIAL_INCONCLUSIVE.value:
        return None
    if signal == SignalType.SATELLITE_INCONCLUSIVE.value:
        return None
    if obj.disposition == EvidenceDisposition.WHY_NOT_FLAGGED:
        if obj.score is None:
            return 0
        return clip_score(float(obj.score))
    if obj.disposition != EvidenceDisposition.WHY_FLAGGED:
        return None
    if obj.score is not None:
        score = clip_score(float(obj.score))
        if signal == SignalType.IMAGE_FORENSIC_AI_GENERATION.value:
            return min(score, FORENSICS_AI_CAP)
        if group == GROUP_CITIZEN:
            return min(score, _citizen_cap(obj))
        return score
    fallback = MAPPED_FLAGGED_SCORES.get(signal)
    if fallback is None:
        return None
    if group == GROUP_CITIZEN:
        return min(fallback, _citizen_cap(obj))
    return fallback


def _support(obj: EvidenceObject) -> str:
    text = (obj.explanation or obj.finding or "").strip()
    if len(text) <= 280:
        return text
    return text[:277].rstrip() + "..."


def _object_state(obj: EvidenceObject, score: int | None) -> V2EvidenceState:
    if obj.disposition == EvidenceDisposition.NOT_ASSESSABLE:
        return V2EvidenceState.NOT_ASSESSABLE
    if obj.disposition == EvidenceDisposition.INCONCLUSIVE:
        return V2EvidenceState.INCONCLUSIVE
    if score is None:
        return V2EvidenceState.NOT_ASSESSABLE
    confidence = max(0.0, min(1.0, float(obj.confidence)))
    if confidence < LOW_CONFIDENCE_THRESHOLD:
        return V2EvidenceState.LOW_CONFIDENCE
    return V2EvidenceState.ASSESSABLE


def _polarity(obj: EvidenceObject, score: int | None, state: V2EvidenceState) -> V2SignalPolarity:
    if state in {
        V2EvidenceState.NOT_ASSESSABLE,
        V2EvidenceState.INCONCLUSIVE,
        V2EvidenceState.UNAVAILABLE,
        V2EvidenceState.NOT_USED_FOR_INVESTIGATION,
    }:
        return V2SignalPolarity.UNKNOWN
    if obj.disposition == EvidenceDisposition.WHY_FLAGGED:
        return V2SignalPolarity.NEGATIVE
    if obj.disposition == EvidenceDisposition.WHY_NOT_FLAGGED:
        return V2SignalPolarity.POSITIVE
    if score is not None and score >= ENGINE_FLAG_THRESHOLD:
        return V2SignalPolarity.NEGATIVE
    if score is not None:
        return V2SignalPolarity.POSITIVE
    return V2SignalPolarity.UNKNOWN


def item_from_object(obj: EvidenceObject) -> EvidenceItemContribution:
    score = mapped_score(obj)
    engine = obj.engine_name.value if hasattr(obj.engine_name, "value") else str(obj.engine_name)
    source_ids = [str(item) for item in (obj.source_ids or [])]
    return EvidenceItemContribution(
        evidence_id=obj.evidence_id,
        signal_type=signal_value(obj),
        engine_name=engine,
        raw_evidence_score=None if obj.score is None else clip_score(float(obj.score)),
        mapped_score=score,
        confidence=max(0.0, min(1.0, float(obj.confidence))),
        disposition=obj.disposition.value,
        data_mode=obj.data_mode.value,
        source_ids=source_ids,
        finding=obj.finding,
    )


def select_unique_objects(
    objects: Sequence[EvidenceObject],
    *,
    preferred_mode: DataMode | None = None,
) -> tuple[list[EvidenceObject], list[str]]:
    """Drop duplicate evidence_ids. Keep one object per evidence_id."""
    seen: set[str] = set()
    ignored: list[str] = []
    unique: list[EvidenceObject] = []
    preferred: list[EvidenceObject] = []
    others: list[EvidenceObject] = []
    for obj in objects:
        if obj.evidence_id in seen:
            ignored.append(obj.evidence_id)
            continue
        seen.add(obj.evidence_id)
        if preferred_mode is not None and obj.data_mode == preferred_mode:
            preferred.append(obj)
        else:
            others.append(obj)
    unique.extend(preferred)
    unique.extend(others)
    return unique, ignored


def _placeholder(group_id: str, reason: str, state: V2EvidenceState) -> GroupContribution:
    return GroupContribution(
        group_id=group_id,
        display_name=GROUP_DISPLAY_NAMES[group_id],
        weight=GROUP_WEIGHTS[group_id],
        state=state,
        polarity=V2SignalPolarity.UNKNOWN,
        raw_evidence_score=None,
        confidence=None,
        confidence_adjusted_score=None,
        correlation_factor=1.0,
        correlation_reason=None,
        effective_contribution=0.0,
        evidence_ids=[],
        source_ids=[],
        items=[],
        finding=None,
        support=None,
        unavailable_reason=reason,
        independent=True,
    )


def _choose_representative(
    objects: list[EvidenceObject],
) -> tuple[EvidenceObject, int | None, V2EvidenceState]:
    scored: list[tuple[EvidenceObject, int, V2EvidenceState]] = []
    unresolved: list[tuple[EvidenceObject, V2EvidenceState]] = []
    for obj in objects:
        score = mapped_score(obj)
        state = _object_state(obj, score)
        if score is None:
            unresolved.append((obj, state))
            continue
        scored.append((obj, score, state))
    if scored:
        scored.sort(key=lambda item: (-item[1], -item[0].confidence, item[0].evidence_id))
        chosen, score, state = scored[0]
        return chosen, score, state
    unresolved.sort(key=lambda item: item[0].evidence_id)
    obj, state = unresolved[0]
    return obj, None, state


def graph_is_overlap_derived(obj: EvidenceObject) -> bool:
    strongest = _fact_text(obj, "strongest_relationship").upper()
    similar_count = _fact_int(obj, "similar_project_count") or 0
    if "SIMILAR" in strongest or similar_count > 0:
        return True
    independent = _fact_map(obj).get("independent_signals")
    if isinstance(independent, list) and any(
        "overlap" in str(item).lower() or "similar" in str(item).lower()
        for item in independent
    ):
        return True
    if obj.comparables:
        return True
    return False


def graph_has_independent_non_overlap(obj: EvidenceObject) -> bool:
    count = _fact_int(obj, "independent_signal_count") or 0
    if count < 2:
        return False
    independent = _fact_map(obj).get("independent_signals")
    if not isinstance(independent, list):
        return count >= 2 and not graph_is_overlap_derived(obj)
    labels = [str(item).lower() for item in independent]
    return any(
        "ida" in item or "agency" in item or "cluster" in item or "concentration" in item
        for item in labels
    )


def citizen_is_location_driven(obj: EvidenceObject) -> bool:
    signal = signal_value(obj)
    if signal == SignalType.CITIZEN_LOCATION.value:
        return True
    finding = f"{obj.finding} {obj.explanation}".lower()
    return "location" in finding and "feedback" not in finding


def build_group_table(
    objects: Sequence[EvidenceObject],
    *,
    preferred_mode: DataMode | None = None,
) -> tuple[list[GroupContribution], list[str], dict[str, EvidenceObject]]:
    """Full catalog table. Missing groups stay UNAVAILABLE (not zero risk)."""
    reject_fusion_v2_inputs(objects)
    unique, ignored = select_unique_objects(objects, preferred_mode=preferred_mode)
    by_group: dict[str, list[EvidenceObject]] = {group: [] for group in GROUP_ORDER}
    for obj in unique:
        group = group_for_signal(signal_value(obj))
        if group is None:
            continue
        by_group[group].append(obj)

    groups: list[GroupContribution] = []
    representatives: dict[str, EvidenceObject] = {}
    for group_id in GROUP_ORDER:
        weight = GROUP_WEIGHTS[group_id]
        members = by_group[group_id]
        if group_id == GROUP_NEED:
            reason = NEED_NOT_INVESTIGATION_REASON
            if not members:
                groups.append(
                    _placeholder(group_id, reason, V2EvidenceState.NOT_USED_FOR_INVESTIGATION)
                )
                continue
            items = [item_from_object(obj) for obj in members]
            evidence_ids = [item.evidence_id for item in items]
            source_ids: list[str] = []
            for item in items:
                for source in item.source_ids:
                    if source not in source_ids:
                        source_ids.append(source)
            groups.append(
                GroupContribution(
                    group_id=group_id,
                    display_name=GROUP_DISPLAY_NAMES[group_id],
                    weight=weight,
                    state=V2EvidenceState.NOT_USED_FOR_INVESTIGATION,
                    polarity=V2SignalPolarity.UNKNOWN,
                    raw_evidence_score=None,
                    confidence=None,
                    confidence_adjusted_score=None,
                    correlation_factor=1.0,
                    correlation_reason=None,
                    effective_contribution=0.0,
                    evidence_ids=evidence_ids,
                    source_ids=source_ids,
                    items=items,
                    finding=members[0].finding,
                    support=_support(members[0]),
                    unavailable_reason=reason,
                    data_mode=members[0].data_mode.value,
                    independent=True,
                )
            )
            representatives[group_id] = members[0]
            continue
        if not members:
            groups.append(
                _placeholder(group_id, UNAVAILABLE_REASON, V2EvidenceState.UNAVAILABLE)
            )
            continue
        chosen, score, state = _choose_representative(members)
        representatives[group_id] = chosen
        if state == V2EvidenceState.NOT_ASSESSABLE:
            reason = NOT_ASSESSABLE_REASON
        elif state == V2EvidenceState.INCONCLUSIVE:
            reason = INCONCLUSIVE_REASON
        else:
            reason = None
        items = [item_from_object(obj) for obj in members]
        evidence_ids = [item.evidence_id for item in items]
        source_ids = []
        for item in items:
            for source in item.source_ids:
                if source not in source_ids:
                    source_ids.append(source)
        confidence = max(0.0, min(1.0, float(chosen.confidence)))
        polarity = _polarity(chosen, score, state)
        flagged = polarity == V2SignalPolarity.NEGATIVE
        groups.append(
            GroupContribution(
                group_id=group_id,
                display_name=GROUP_DISPLAY_NAMES[group_id],
                weight=weight,
                state=state,
                polarity=polarity,
                raw_evidence_score=score,
                confidence=confidence if score is not None else None,
                confidence_adjusted_score=None,
                correlation_factor=1.0,
                correlation_reason=None,
                effective_contribution=0.0,
                evidence_ids=evidence_ids,
                source_ids=source_ids,
                items=items,
                finding=chosen.finding,
                support=_support(chosen),
                unavailable_reason=reason,
                data_mode=chosen.data_mode.value,
                flagged=flagged,
                peer_quality=_fact_int(chosen, "peer_quality"),
                independent=True,
            )
        )
    return groups, ignored, representatives
