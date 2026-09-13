"""Explanations for Relationship Graph V1.

Never claims fraud. Distinguishes normal connectivity from a potential
pattern of interest.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.engines.graph.constants import (
    CLOSE_DATE_DAYS,
    GOVERNANCE_NOTE,
    HYBRID_TEST_NOTE,
    REAL_LIMITATION_NOTE,
    SIGNAL_SEPARATION_NOTE,
)
from app.engines.graph.types import (
    GraphFindingKind,
    GraphMode,
    GraphRecord,
    GraphStats,
    SimilarRelation,
)


def pattern_sentence(stats: GraphStats) -> str:
    similar = stats.similar_project_count
    if similar <= 0:
        return (
            f"Project has no highly similar works under Overlap Intelligence. "
            f"{stats.connected_project_count} connected project(s) share entity "
            "nodes such as constituency, category, or IDA."
        )
    loc = ""
    if stats.same_constituency_similar:
        loc = " in the same constituency"
    extras: list[str] = []
    if stats.same_ida_similar:
        extras.append(f"{stats.same_ida_similar} sharing the same IDA")
    if stats.close_dates_similar:
        extras.append(
            f"{stats.close_dates_similar} recommended within {CLOSE_DATE_DAYS} days"
        )
    head = f"Project has {similar} highly similar work(s){loc}"
    if extras:
        return head + ", with " + " and ".join(extras) + "."
    return head + "."


def finding_summary(kind: GraphFindingKind) -> str:
    if kind == GraphFindingKind.POTENTIAL_PATTERN_OF_INTEREST:
        return "Potential Pattern of Interest"
    if kind == GraphFindingKind.HIGH_CONNECTIVITY:
        return "High Connectivity"
    if kind == GraphFindingKind.INSUFFICIENT_EVIDENCE:
        return "Insufficient Evidence"
    return "Normal Connectivity"


def why_flagged_text(kind: GraphFindingKind, stats: GraphStats) -> str | None:
    if kind != GraphFindingKind.POTENTIAL_PATTERN_OF_INTEREST:
        return None
    signals = ", ".join(stats.independent_signals) or "multiple relationship signals"
    return (
        f"{pattern_sentence(stats)} Independent relationship signals: {signals}. "
        "This is a Potential Pattern of Interest for officer review, not a legal finding."
    )


def why_not_flagged_text(
    kind: GraphFindingKind,
    stats: GraphStats,
    subject: GraphRecord,
) -> str | None:
    if kind == GraphFindingKind.POTENTIAL_PATTERN_OF_INTEREST:
        return None
    if kind == GraphFindingKind.INSUFFICIENT_EVIDENCE:
        missing: list[str] = []
        if not (subject.constituency_usable and subject.constituency.strip()):
            missing.append("geographic constituency")
        if not subject.ida.strip():
            missing.append("IDA")
        if not subject.mp_name.strip():
            missing.append("MP name")
        detail = ", ".join(missing) if missing else "key observed fields"
        return (
            f"Insufficient evidence to describe a relationship pattern: {detail} "
            "are missing or unusable, and no similar works were linked."
        )
    if kind == GraphFindingKind.HIGH_CONNECTIVITY:
        return (
            f"{pattern_sentence(stats)} High connectivity reflects volume of similar "
            "or clustered works. A large number of connections is not automatically "
            "a pattern of interest."
        )
    if stats.similar_project_count == 0:
        return (
            "Why not flagged: observed entity links (MP, constituency, category, "
            "IDA, state) are expected MPLADS structure. No Overlap Intelligence "
            "SIMILAR_TO matches met the Potential Overlap / Potential Duplicate "
            "threshold, so this is Normal Connectivity."
        )
    return (
        f"{pattern_sentence(stats)} Similar works are present but do not combine "
        "same constituency, same IDA, and close recommendation dates at the "
        "Potential Pattern of Interest threshold. This is Normal Connectivity."
    )


def project_explanation(
    *,
    kind: GraphFindingKind,
    stats: GraphStats,
    subject: GraphRecord,
    similar: Sequence[SimilarRelation],
    mode: GraphMode,
    cluster_peers: int,
) -> str:
    lines = [
        f"Graph finding: {finding_summary(kind)}.",
        pattern_sentence(stats),
        (
            f"Connected projects in the ego neighborhood: {stats.connected_project_count}. "
            f"Same constituency: {stats.same_constituency_count}. "
            f"Same category: {stats.same_category_count}. "
            f"Same IDA: {stats.same_ida_count}. "
            f"Similar projects: {stats.similar_project_count}."
        ),
        (
            f"IDA {subject.ida or '(blank)'} is associated with "
            f"{stats.ida_associated_project_count} project(s) in the corpus. "
            "Agency volume alone is not a pattern of interest."
        ),
        (
            f"Constituency/category/IDA cluster size: {stats.cluster_size} "
            f"(ego cluster peers included: {cluster_peers}). "
            f"Repeated combination count: {stats.repeated_combo_count}."
        ),
    ]
    if stats.cluster_density is not None:
        lines.append(
            f"Similar-edge density among cluster members: {stats.cluster_density:.2f}."
        )
    if stats.independent_signals:
        lines.append(
            "Independent relationship signals: "
            + ", ".join(stats.independent_signals)
            + f" ({stats.independent_signal_count})."
        )
    if stats.strongest_relationship:
        lines.append(
            f"Strongest relationship: {stats.strongest_relationship} "
            f"(strength {stats.strongest_strength})."
        )
    flagged = why_flagged_text(kind, stats)
    not_flagged = why_not_flagged_text(kind, stats, subject)
    if flagged:
        lines.append(flagged)
    if not_flagged:
        lines.append(not_flagged)
    if similar:
        top = similar[0]
        lines.append(
            f"Top SIMILAR_TO: project {top.linked_project_id} "
            f"overlap_score={int(top.similarity_score)} "
            f"outcome={top.overlap_outcome}."
        )
    lines.append(SIGNAL_SEPARATION_NOTE)
    lines.append(REAL_LIMITATION_NOTE if mode == GraphMode.REAL else HYBRID_TEST_NOTE)
    lines.append(GOVERNANCE_NOTE)
    return " ".join(lines)
