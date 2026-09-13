"""Risk Fusion V2 core.

Consumes Evidence Objects and produces Investigation Priority and
Evidence Confidence. Does not determine fraud, sanction a project, or
release funds. Frozen V1/V1.1 engines are not modified.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence

from app.domain.enums import DataMode
from app.domain.schemas.evidence import EvidenceObject
from app.engines.fusion_v2.confidence import evidence_confidence
from app.engines.fusion_v2.conflict import detect_conflicts
from app.engines.fusion_v2.constants import (
    COST_INCLUDED_IN_HYBRID_NOTE,
    ENGINE_VERSION,
    GOVERNANCE_NOTE,
    GROUP_COST,
    MAJOR_CONTRIBUTION_POINTS,
    WEIGHT_NOTE,
)
from app.engines.fusion_v2.correlation import apply_correlation
from app.engines.fusion_v2.explain import (
    build_explanation,
    build_recommendation,
    explanation_type,
    explanation_type_list,
    synthetic_disclosure_text,
)
from app.engines.fusion_v2.ingest import build_group_table
from app.engines.fusion_v2.scoring import (
    apply_confidence_and_contribution,
    available_weight,
    evidence_coverage,
    investigation_priority,
    investigation_priority_0_100,
    is_scored_state,
    priority_band,
    raw_risk,
    recommended_action,
    unavailable_weight,
)
from app.engines.fusion_v2.types import FusionV2Result, GroupContribution, V2EvidenceState


def evidence_fingerprint(objects: Sequence[EvidenceObject]) -> str:
    payload = []
    for obj in sorted(objects, key=lambda item: item.evidence_id):
        score = obj.score
        payload.append(
            {
                "evidence_id": obj.evidence_id,
                "signal_type": obj.signal_type.value if hasattr(obj.signal_type, "value") else str(obj.signal_type),
                "disposition": obj.disposition.value,
                "score": None if score is None else float(score),
                "confidence": float(obj.confidence),
                "data_mode": obj.data_mode.value,
            }
        )
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def resolve_fusion_data_mode(
    objects: Sequence[EvidenceObject],
    *,
    requested: DataMode | None = None,
) -> DataMode:
    modes = {obj.data_mode for obj in objects}
    if requested == DataMode.REAL:
        return DataMode.REAL
    if DataMode.HYBRID in modes:
        return DataMode.HYBRID
    if DataMode.SYNTHETIC in modes:
        return DataMode.SYNTHETIC
    if DataMode.REAL in modes:
        return DataMode.REAL
    return requested or DataMode.REAL


def _contributing(groups: list[GroupContribution]) -> list[GroupContribution]:
    items = [
        item
        for item in groups
        if is_scored_state(item.state) and item.effective_contribution > 0
    ]
    return sorted(items, key=lambda item: (-item.effective_contribution, item.group_id))


def _independent(groups: list[GroupContribution]) -> list[GroupContribution]:
    return [
        item
        for item in _contributing(groups)
        if item.independent
    ]


def _correlated(groups: list[GroupContribution]) -> list[GroupContribution]:
    return [
        item
        for item in groups
        if item.correlation_factor < 1.0 and item.correlation_reason
    ]


def _unavailable(groups: list[GroupContribution]) -> list[GroupContribution]:
    return [item for item in groups if item.state == V2EvidenceState.UNAVAILABLE]


def _not_assessable(groups: list[GroupContribution]) -> list[GroupContribution]:
    return [
        item
        for item in groups
        if item.state
        in {
            V2EvidenceState.NOT_ASSESSABLE,
            V2EvidenceState.INCONCLUSIVE,
            V2EvidenceState.NOT_USED_FOR_INVESTIGATION,
        }
    ]


def fuse_evidence_v2(
    objects: Sequence[EvidenceObject],
    *,
    project_id: int,
    internal_project_id: str | None = None,
    requested_data_mode: DataMode | None = None,
) -> FusionV2Result:
    """Deterministic V2 fusion from the current evidence set."""
    data_mode = resolve_fusion_data_mode(objects, requested=requested_data_mode)
    groups, ignored, representatives = build_group_table(
        objects, preferred_mode=requested_data_mode
    )
    apply_confidence_and_contribution(groups)
    apply_correlation(groups, representatives)
    apply_confidence_and_contribution(groups)
    raw = raw_risk(groups)
    display_ip = investigation_priority_0_100(groups)
    priority = investigation_priority(groups)
    conflicts = detect_conflicts(groups)
    confidence = evidence_confidence(groups, data_mode=data_mode, conflicts=conflicts)
    band = priority_band(priority)
    kind = explanation_type(groups, priority=priority, band=band, conflicts=conflicts)
    scored_n = sum(1 for item in groups if is_scored_state(item.state))
    action = recommended_action(
        priority,
        confidence=confidence,
        assessable_count=scored_n,
        conflicting=bool(conflicts),
    )
    disclosure = synthetic_disclosure_text(
        groups, data_mode=data_mode, major_points=MAJOR_CONTRIBUTION_POINTS
    )
    explanation = build_explanation(
        groups,
        priority=priority,
        confidence=confidence,
        band=band,
        data_mode=data_mode,
        kind=kind,
        raw_risk=raw,
        conflicts=conflicts,
        synthetic_disclosure=disclosure,
    )
    if data_mode == DataMode.HYBRID and any(
        item.group_id == GROUP_COST and item.data_mode == DataMode.REAL.value for item in groups
    ):
        explanation = f"{explanation} {COST_INCLUDED_IN_HYBRID_NOTE}"
    evidence_ids: list[str] = []
    for item in groups:
        for evidence_id in item.evidence_ids:
            if evidence_id not in evidence_ids:
                evidence_ids.append(evidence_id)
    return FusionV2Result(
        project_id=project_id,
        internal_project_id=internal_project_id,
        investigation_priority=priority,
        investigation_priority_0_100=display_ip,
        raw_risk=raw,
        evidence_confidence=confidence,
        risk_class=band,
        explanation_type=kind,
        recommended_action=action,
        data_mode=data_mode,
        contributing_evidence_groups=_contributing(groups),
        independent_evidence_groups=_independent(groups),
        discounted_correlated_evidence=_correlated(groups),
        unavailable_evidence=_unavailable(groups),
        not_assessable_evidence=_not_assessable(groups),
        conflicting_evidence=conflicts,
        all_groups=groups,
        evidence_ids=evidence_ids,
        ignored_duplicate_evidence_ids=ignored,
        explanation=explanation,
        recommendation=build_recommendation(action),
        available_weight=available_weight(groups),
        unavailable_weight=unavailable_weight(groups),
        evidence_coverage=evidence_coverage(groups),
        weight_note=WEIGHT_NOTE,
        governance_note=GOVERNANCE_NOTE,
        synthetic_disclosure=disclosure,
        evidence_fingerprint=evidence_fingerprint(objects),
        engine_version=ENGINE_VERSION,
        explanation_types=explanation_type_list(kind),
    )
