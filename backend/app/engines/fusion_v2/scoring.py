"""Investigation Priority formula for Risk Fusion V2.

Unavailable weights are not redistributed. Engine scores are not modified.
Displayed Investigation Priority remains 0–100.

  adjusted_score = raw_score * (0.55 + 0.45 * group_confidence)
  contribution   = weight * adjusted_score * correlation_factor
  Raw Risk       = sum(contribution) over assessable groups
  IP             = clip(round(Raw Risk), 0, 100)

A single group at 100 cannot become 100/100. Missing evidence is a
coverage gap, not a suspicious signal and not a zero-risk finding.
"""

from __future__ import annotations

from app.domain.enums import InvestigationPriorityBand, RecommendedAction
from app.engines.fusion_v2.constants import (
    CONFIDENCE_FLOOR,
    CONFIDENCE_SPAN,
    GROUP_NEED,
    GROUP_WEIGHTS,
    LOW_CONFIDENCE_RECOMMEND,
    LOW_PRIORITY_MAX,
    MEDIUM_PRIORITY_MAX,
    PLANNED_WEIGHT_SUM,
    VERY_LOW_CONFIDENCE,
)
from app.engines.fusion_v2.types import GroupContribution, V2EvidenceState


def bounded_score(value: float) -> int:
    if value != value:  # NaN
        return 0
    if value <= 0:
        return 0
    if value >= 100:
        return 100
    return int(value + 0.5)


def is_scored_state(state: V2EvidenceState) -> bool:
    return state in {V2EvidenceState.ASSESSABLE, V2EvidenceState.LOW_CONFIDENCE}


def apply_confidence_and_contribution(groups: list[GroupContribution]) -> list[GroupContribution]:
    for item in groups:
        if item.group_id == GROUP_NEED:
            item.confidence_adjusted_score = None
            item.effective_contribution = 0.0
            continue
        if not is_scored_state(item.state) or item.raw_evidence_score is None:
            item.confidence_adjusted_score = None
            item.effective_contribution = 0.0
            continue
        confidence = 0.0 if item.confidence is None else max(0.0, min(1.0, item.confidence))
        adjusted = float(item.raw_evidence_score) * (CONFIDENCE_FLOOR + CONFIDENCE_SPAN * confidence)
        item.confidence_adjusted_score = round(min(100.0, max(0.0, adjusted)), 4)
        contribution = (
            item.weight * item.confidence_adjusted_score * float(item.correlation_factor)
        )
        item.effective_contribution = round(contribution, 4)
    return groups


def raw_risk(groups: list[GroupContribution]) -> float:
    total = 0.0
    for item in groups:
        if item.group_id == GROUP_NEED:
            continue
        if not is_scored_state(item.state):
            continue
        total += item.effective_contribution
    return round(total, 4)


def investigation_priority_0_100(groups: list[GroupContribution]) -> float:
    value = raw_risk(groups)
    if value != value:
        return 0.0
    return round(min(100.0, max(0.0, value)), 1)


def investigation_priority(groups: list[GroupContribution]) -> int:
    return bounded_score(raw_risk(groups))


def available_weight(groups: list[GroupContribution]) -> float:
    return round(
        sum(
            item.weight
            for item in groups
            if item.group_id != GROUP_NEED and is_scored_state(item.state)
        ),
        4,
    )


def unavailable_weight(groups: list[GroupContribution]) -> float:
    return round(PLANNED_WEIGHT_SUM - available_weight(groups), 4)


def evidence_coverage(groups: list[GroupContribution]) -> float:
    planned = sum(weight for group, weight in GROUP_WEIGHTS.items() if group != GROUP_NEED)
    if planned <= 0:
        return 0.0
    return round(available_weight(groups) / planned, 4)


def priority_band(priority: int) -> InvestigationPriorityBand:
    if priority <= LOW_PRIORITY_MAX:
        return InvestigationPriorityBand.LOW
    if priority <= MEDIUM_PRIORITY_MAX:
        return InvestigationPriorityBand.MEDIUM
    return InvestigationPriorityBand.HIGH


def recommended_action(
    priority: int,
    *,
    confidence: int,
    assessable_count: int,
    conflicting: bool,
) -> RecommendedAction:
    """Prototype mapping. Not a legal or administrative decision.

    High Investigation Priority with low Evidence Confidence is conservative:
    NEED MORE INFORMATION rather than a highly certain conclusion.
    """
    if assessable_count <= 0:
        return RecommendedAction.NEED_MORE_INFORMATION
    if confidence < VERY_LOW_CONFIDENCE:
        return RecommendedAction.NEED_MORE_INFORMATION
    if priority >= 45 and confidence < LOW_CONFIDENCE_RECOMMEND:
        return RecommendedAction.NEED_MORE_INFORMATION
    if conflicting and confidence < LOW_CONFIDENCE_RECOMMEND:
        return RecommendedAction.NEED_MORE_INFORMATION
    if priority <= LOW_PRIORITY_MAX:
        return RecommendedAction.MONITOR
    if priority <= MEDIUM_PRIORITY_MAX:
        return RecommendedAction.REVIEW
    return RecommendedAction.INSPECT
