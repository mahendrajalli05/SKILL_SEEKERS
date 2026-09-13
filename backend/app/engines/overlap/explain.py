"""Factual Overlap Intelligence explanations.

Supports WHY LINKED and WHY NOT LINKED / INSUFFICIENT EVIDENCE.
High semantic similarity alone is described as Potential Overlap, not a duplicate.
Never uses legal-fraud language.
"""

from __future__ import annotations

from app.engines.overlap.constants import (
    DATE_PROXIMATE_DAYS,
    GPS_UNAVAILABLE_NOTE,
    HYBRID_TEST_NOTE,
    REAL_LIMITATION_NOTE,
    SIGNAL_SEPARATION_NOTE,
)
from app.engines.overlap.types import (
    OverlapAssessmentOutcome,
    OverlapMatch,
    OverlapMode,
    PairSignals,
)


def _pct(value: float | None) -> str:
    if value is None:
        return "unavailable"
    return f"{int(round(value * 100))}%"


def _yes_no(value: bool | None) -> str:
    if value is None:
        return "unavailable"
    return "yes" if value else "no"


def _label(outcome: OverlapAssessmentOutcome) -> str:
    if outcome == OverlapAssessmentOutcome.POTENTIAL_DUPLICATE:
        return "Potential Duplicate"
    if outcome == OverlapAssessmentOutcome.POTENTIAL_OVERLAP:
        return "Potential Overlap"
    if outcome == OverlapAssessmentOutcome.INSUFFICIENT_EVIDENCE:
        return "insufficient evidence"
    return "not linked"


def _amount_phrase(signals: PairSignals) -> str:
    if signals.amount_similarity is None:
        return "allocation-amount comparison is unavailable"
    percent = int(round(signals.amount_similarity * 100))
    if signals.amount_similarity >= 0.80:
        return f"closely similar allocation amounts ({percent}% amount similarity)"
    return f"dissimilar allocation amounts ({percent}% amount similarity)"


def _date_phrase(signals: PairSignals) -> str:
    if signals.date_gap_days is None:
        return "recommendation-date proximity is unavailable"
    if signals.date_gap_days <= DATE_PROXIMATE_DAYS:
        return (
            f"within a {DATE_PROXIMATE_DAYS}-day recommendation window "
            f"({signals.date_gap_days} days apart)"
        )
    return f"recommendation dates {signals.date_gap_days} days apart"


def _geo_phrase(signals: PairSignals, *, mode: OverlapMode) -> str:
    if signals.gps_distance_m is not None:
        gps = f"GPS distance {signals.gps_distance_m:.1f} m"
        if mode == OverlapMode.HYBRID_TEST:
            return f"{gps} (HYBRID/TEST synthetic coordinates)"
        return gps
    if signals.location_similarity is not None:
        return f"place-text similarity {_pct(signals.location_similarity)}"
    return GPS_UNAVAILABLE_NOTE


def pair_reasons(signals: PairSignals, *, mode: OverlapMode) -> tuple[str, ...]:
    reasons: list[str] = []
    reasons.append(f"semantic similarity {_pct(signals.semantic_similarity)}")
    reasons.append(f"category match {_yes_no(signals.category_match)}")
    reasons.append(f"constituency match {_yes_no(signals.constituency_match)}")
    reasons.append(_amount_phrase(signals))
    reasons.append(_date_phrase(signals))
    reasons.append(_geo_phrase(signals, mode=mode))
    if signals.supporting_signals:
        reasons.append("supporting signals: " + ", ".join(signals.supporting_signals))
    if signals.unavailable_signals:
        reasons.append("unavailable: " + ", ".join(signals.unavailable_signals))
    return tuple(reasons)


def why_linked_text(signals: PairSignals, *, mode: OverlapMode) -> str:
    parts = [
        f"These works have {_pct(signals.semantic_similarity)} semantic similarity",
    ]
    same_bits: list[str] = []
    if signals.constituency_match:
        same_bits.append("constituency")
    if signals.category_match:
        same_bits.append("category")
    if same_bits:
        parts.append("belong to the same " + " and ".join(same_bits))
    parts.append("and have " + _amount_phrase(signals) + " " + _date_phrase(signals))
    sentence = ", ".join(parts[:-1]) + ", " + parts[-1] + "."
    if signals.outcome == OverlapAssessmentOutcome.POTENTIAL_DUPLICATE:
        label = (
            "Multiple supporting signals agree, so this is recorded as a "
            "Potential Duplicate for officer review, not as a legal finding."
        )
    else:
        label = (
            "This is recorded as Potential Overlap. High semantic similarity "
            "alone is not treated as a duplicate."
            if not signals.supporting_signals
            else "This is recorded as Potential Overlap, not a confirmed duplicate."
        )
    geo = _geo_phrase(signals, mode=mode)
    hybrid = f" {HYBRID_TEST_NOTE}" if mode == OverlapMode.HYBRID_TEST else ""
    return (
        f"{sentence} {label} {geo} Evidence Confidence is "
        f"{signals.evidence_confidence}. Overall overlap score is "
        f"{signals.overlap_score}. {SIGNAL_SEPARATION_NOTE}{hybrid}"
    )


def why_not_linked_text(signals: PairSignals | None, *, mode: OverlapMode, candidate_count: int) -> str:
    hybrid = f" {HYBRID_TEST_NOTE}" if mode == OverlapMode.HYBRID_TEST else ""
    if signals is None:
        return (
            "These works were not linked: no blocked candidates were generated "
            f"(candidates={candidate_count}). Insufficient evidence for Potential "
            f"Overlap. {GPS_UNAVAILABLE_NOTE if mode == OverlapMode.REAL else ''} "
            f"{SIGNAL_SEPARATION_NOTE} {REAL_LIMITATION_NOTE if mode == OverlapMode.REAL else ''}"
            f"{hybrid}"
        ).strip()
    if signals.outcome == OverlapAssessmentOutcome.INSUFFICIENT_EVIDENCE:
        return (
            "Insufficient evidence to link these works: work descriptions are "
            f"missing or unusable and GPS is unavailable. Evidence Confidence is "
            f"{signals.evidence_confidence}. {SIGNAL_SEPARATION_NOTE}{hybrid}"
        )
    semantic = _pct(signals.semantic_similarity)
    support = (
        ", ".join(signals.supporting_signals) if signals.supporting_signals else "none"
    )
    return (
        f"These works were not linked as a Potential Duplicate or Potential Overlap: "
        f"semantic similarity is {semantic}, supporting signals are {support}, and "
        f"overall overlap score is {signals.overlap_score}. "
        f"{_geo_phrase(signals, mode=mode)} Evidence Confidence is "
        f"{signals.evidence_confidence}. {SIGNAL_SEPARATION_NOTE}{hybrid}"
    )


def missing_description_explanation(*, mode: OverlapMode) -> str:
    hybrid = f" {HYBRID_TEST_NOTE}" if mode == OverlapMode.HYBRID_TEST else ""
    return (
        "Overlap Intelligence was not assessed: the work description is missing "
        "or empty after normalisation, so semantic similarity cannot be computed. "
        "Insufficient evidence. Investigation Priority is not assigned by this "
        f"engine. {SIGNAL_SEPARATION_NOTE} {REAL_LIMITATION_NOTE if mode == OverlapMode.REAL else ''}"
        f"{hybrid}"
    )


def project_explanation(
    *,
    outcome: OverlapAssessmentOutcome,
    matches: list[OverlapMatch],
    why_linked: str | None,
    why_not_linked: str | None,
    candidate_count: int,
    mode: OverlapMode,
    geographic_evidence_available: bool,
) -> str:
    geo = (
        "Geographic evidence is available for at least one compared pair."
        if geographic_evidence_available
        else GPS_UNAVAILABLE_NOTE
    )
    if outcome == OverlapAssessmentOutcome.INSUFFICIENT_EVIDENCE:
        return missing_description_explanation(mode=mode)
    if matches:
        top = matches[0]
        return (
            f"{_label(outcome)}: {len(matches)} linked work(s) after blocked candidate "
            f"generation ({candidate_count} candidates). Top linked internal_project_id "
            f"{top.linked_internal_project_id} has overall overlap score "
            f"{top.overall_overlap_score} and semantic similarity "
            f"{_pct(top.semantic_similarity)}. {why_linked or ''} {geo}"
        ).strip()
    return (
        f"Not linked: {candidate_count} blocked candidate(s) were scored and none "
        f"met Potential Overlap or Potential Duplicate thresholds. "
        f"{why_not_linked or ''} {geo}"
    ).strip()
