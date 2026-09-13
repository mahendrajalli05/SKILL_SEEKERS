"""Officer-facing Risk Fusion V2 explanations. Never claims fraud."""

from __future__ import annotations

from app.domain.enums import (
    DataMode,
    FusionExplanationType,
    InvestigationPriorityBand,
    RecommendedAction,
)
from app.engines.fusion_v2.constants import (
    GOVERNANCE_NOTE,
    HYBRID_DISCLOSURE,
    NO_SANCTION_NOTE,
    SYNTHETIC_DISCLOSURE,
    WEIGHT_NOTE,
)
from app.engines.fusion_v2.scoring import is_scored_state
from app.engines.fusion_v2.types import (
    ConflictRecord,
    GroupContribution,
    V2EvidenceState,
)


_ACTION_TEXT = {
    RecommendedAction.MONITOR: (
        "Monitor the work using the available records. No fused evidence group "
        "currently warrants a higher review queue on its own. This uses the "
        "displayed Investigation Priority and Evidence Confidence; it is not a "
        "legal conclusion."
    ),
    RecommendedAction.REVIEW: (
        "Review comparable works and inspect supporting evidence before taking "
        "further action. This uses the displayed Investigation Priority and "
        "Evidence Confidence; it is not a legal conclusion."
    ),
    RecommendedAction.INSPECT: (
        "Inspect supporting documents, comparables, and field evidence before "
        "taking further action. This is a review recommendation based on "
        "Investigation Priority and Evidence Confidence, not a legal finding."
    ),
    RecommendedAction.INVESTIGATE: (
        "Inspect the contributing evidence in detail. This is a recommended "
        "investigation action based on Investigation Priority and Evidence "
        "Confidence, not a legal or administrative decision."
    ),
    RecommendedAction.NEED_MORE_INFORMATION: (
        "Need more information before treating this as a high-certainty review "
        "conclusion. High Investigation Priority with low Evidence Confidence, "
        "missing evidence, or conflicting evidence is not a highly certain "
        "finding. Authorized officers decide."
    ),
}


def explanation_type(
    groups: list[GroupContribution],
    *,
    priority: int,
    band: InvestigationPriorityBand,
    conflicts: list[ConflictRecord],
) -> FusionExplanationType:
    if conflicts:
        return FusionExplanationType.CONFLICTING_EVIDENCE
    scored = [item for item in groups if is_scored_state(item.state)]
    flagged = [item for item in scored if item.flagged]
    if not scored:
        return FusionExplanationType.INSUFFICIENT_EVIDENCE
    if flagged and band != InvestigationPriorityBand.LOW:
        return FusionExplanationType.WHY_FLAGGED
    if flagged and band == InvestigationPriorityBand.LOW:
        return FusionExplanationType.INCONCLUSIVE
    if len(scored) >= 2 and not flagged and band == InvestigationPriorityBand.LOW:
        return FusionExplanationType.WHY_NOT_FLAGGED
    return FusionExplanationType.INCONCLUSIVE


def _band_word(band: InvestigationPriorityBand) -> str:
    return band.value.lower()


def build_explanation(
    groups: list[GroupContribution],
    *,
    priority: int,
    confidence: int,
    band: InvestigationPriorityBand,
    data_mode: DataMode,
    kind: FusionExplanationType,
    raw_risk: float,
    conflicts: list[ConflictRecord],
    synthetic_disclosure: str | None,
) -> str:
    scored = [item for item in groups if is_scored_state(item.state)]
    flagged = [item for item in scored if item.flagged]
    independent = [
        item
        for item in scored
        if item.independent and item.effective_contribution > 0
    ]
    correlated = [
        item
        for item in groups
        if item.correlation_factor < 1.0 and item.correlation_reason
    ]
    unavailable = [
        item
        for item in groups
        if item.state == V2EvidenceState.UNAVAILABLE
    ]
    not_assessable = [
        item
        for item in groups
        if item.state in {V2EvidenceState.NOT_ASSESSABLE, V2EvidenceState.INCONCLUSIVE}
    ]
    parts: list[str] = [
        f"Investigation Priority: {priority}/100.",
        f"Evidence Confidence: {confidence}/100.",
        f"Priority band is {_band_word(band)}.",
    ]
    if kind == FusionExplanationType.CONFLICTING_EVIDENCE:
        parts.append(
            "CONFLICTING_EVIDENCE: sources disagree. No single conclusion is forced."
        )
        parts.append(
            "Disagreeing groups: "
            + "; ".join(item.summary for item in conflicts)
            + "."
        )
    elif kind == FusionExplanationType.INSUFFICIENT_EVIDENCE:
        parts.append(
            "Investigation Priority is low because no assessable evidence groups "
            "were available to fuse (inconclusive)."
        )
    elif kind == FusionExplanationType.WHY_FLAGGED:
        names = ", ".join(item.display_name for item in flagged) or "available groups"
        parts.append(
            f"{len(scored)} assessable evidence group(s) were fused and {names} "
            "indicated elevated review need."
        )
    elif kind == FusionExplanationType.WHY_NOT_FLAGGED:
        parts.append(
            f"{len(scored)} assessable groups were within their engine review "
            "flags, so Investigation Priority remains low."
        )
    else:
        parts.append(
            f"{len(scored)} assessable evidence group(s) were fused. Evidence is "
            "not sufficient for a stronger conclusion."
        )

    parts.append(
        "Evidence Confidence is calculated separately from Investigation Priority "
        "and is not the average of source scores. A high priority with low "
        "confidence is not a highly certain conclusion."
    )

    top = sorted(
        scored,
        key=lambda item: (-item.effective_contribution, item.group_id),
    )[:3]
    if top:
        parts.append(
            "Top contributing evidence groups: "
            + "; ".join(
                f"{item.display_name} (raw {item.raw_evidence_score}, "
                f"effective {item.effective_contribution:.2f})"
                for item in top
            )
            + "."
        )
    if independent:
        parts.append(
            "Independent evidence: "
            + ", ".join(item.display_name for item in independent)
            + "."
        )
    if correlated:
        parts.append(
            "Correlated evidence discounted: "
            + "; ".join(
                f"{item.display_name} (keep {item.correlation_factor:.2f}: "
                f"{item.correlation_reason})"
                for item in correlated
            )
        )
    else:
        parts.append("Correlated evidence discounted: none.")

    if unavailable:
        parts.append(
            "Unavailable: "
            + "; ".join(item.display_name for item in unavailable)
            + ". Unavailable is not treated as zero-risk evidence and is not treated as suspicious."
        )
    if not_assessable:
        parts.append(
            "Not assessable / inconclusive: "
            + "; ".join(
                f"{item.display_name} ({item.state.value.lower()})"
                for item in not_assessable
            )
            + "."
        )
    parts.append(
        f"Raw Risk {raw_risk} is the un-renormalized sum of effective contributions. "
        "Missing group weights were not redistributed. "
        f"{WEIGHT_NOTE}"
    )
    if data_mode == DataMode.HYBRID:
        parts.append(
            "Data mode is HYBRID: observed MPLADS fields plus synthetic enrichment. "
            "Synthetic fields are not official MPLADS values."
        )
    elif data_mode == DataMode.SYNTHETIC:
        parts.append(
            "Data mode is SYNTHETIC: this is a test record, not a government project."
        )
    else:
        parts.append("Data mode is REAL: fusion used observed MPLADS evidence only.")
    if synthetic_disclosure:
        parts.append(synthetic_disclosure)
    parts.append(
        f"Recommendation uses Investigation Priority together with Evidence "
        f"Confidence. {GOVERNANCE_NOTE} {NO_SANCTION_NOTE}"
    )
    return " ".join(parts)


def build_recommendation(action: RecommendedAction) -> str:
    return _ACTION_TEXT[action]


def explanation_type_list(kind: FusionExplanationType) -> list[str]:
    return [kind.value]


def synthetic_disclosure_text(
    groups: list[GroupContribution],
    *,
    data_mode: DataMode,
    major_points: float,
) -> str | None:
    major = [
        item
        for item in groups
        if is_scored_state(item.state)
        and item.effective_contribution >= major_points
        and item.data_mode in {DataMode.SYNTHETIC.value, DataMode.HYBRID.value}
    ]
    if any(item.data_mode == DataMode.SYNTHETIC.value for item in major):
        return SYNTHETIC_DISCLOSURE
    if data_mode == DataMode.SYNTHETIC:
        return SYNTHETIC_DISCLOSURE
    if any(item.data_mode == DataMode.HYBRID.value for item in major):
        return HYBRID_DISCLOSURE
    if data_mode == DataMode.HYBRID:
        return HYBRID_DISCLOSURE
    return None
