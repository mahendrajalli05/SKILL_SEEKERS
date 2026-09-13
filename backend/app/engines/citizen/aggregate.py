"""Multi-citizen aggregation with sample-size safeguards.

A single report cannot dominate a project conclusion.
"""

from __future__ import annotations

from collections import Counter
from statistics import mean

from app.engines.citizen.constants import (
    AGGREGATE_COMMUNITY_CONCERN,
    AGGREGATE_INCONCLUSIVE,
    AGGREGATE_NONE,
    COMMUNITY_SIGNAL_MIN,
    HYBRID_CONFIDENCE_CAP,
    INSUFFICIENT_SAMPLE_MAX,
    ISSUE_LABELS,
    LOCATION_REJECTED,
    LOCATION_VERIFIED,
    MIN_REPORTS_FOR_CONCERN,
    REAL_CONFIDENCE_CAP,
    SAMPLE_COMMUNITY,
    SAMPLE_INSUFFICIENT,
    SAMPLE_LIMITED,
    STATUS_INCONCLUSIVE,
    STATUS_REJECTED,
    SYNTHETIC_CONFIDENCE_CAP,
)
from app.engines.citizen.types import CitizenSummary
from app.models.citizen import CitizenReport


def _mode_cap(data_mode: str) -> float:
    if data_mode == "SYNTHETIC":
        return SYNTHETIC_CONFIDENCE_CAP
    if data_mode == "HYBRID":
        return HYBRID_CONFIDENCE_CAP
    return REAL_CONFIDENCE_CAP


def sample_size_status(
    total: int,
    *,
    insufficient_max: int = INSUFFICIENT_SAMPLE_MAX,
    community_min: int = COMMUNITY_SIGNAL_MIN,
) -> str:
    if total <= insufficient_max:
        return SAMPLE_INSUFFICIENT
    if total >= community_min:
        return SAMPLE_COMMUNITY
    return SAMPLE_LIMITED


def aggregate_finding_for(
    *,
    verified_count: int,
    recurring: list[tuple[str, int]],
    min_for_concern: int = MIN_REPORTS_FOR_CONCERN,
) -> str:
    if verified_count < min_for_concern:
        return AGGREGATE_NONE if verified_count == 0 else AGGREGATE_INCONCLUSIVE
    if not recurring:
        return AGGREGATE_INCONCLUSIVE
    top_category, top_count = recurring[0]
    if top_count >= min_for_concern and top_category in {
        "incomplete_work",
        "work_quality",
        "delayed_work",
        "safety",
        "location_concern",
    }:
        return AGGREGATE_COMMUNITY_CONCERN
    return AGGREGATE_INCONCLUSIVE


def aggregate_reports(
    rows: list[CitizenReport],
    *,
    project_id: int,
    internal_project_id: str,
    scheme_id: str | None,
    data_mode: str,
    provenance: dict,
    evidence_ids: list[str],
    insufficient_max: int = INSUFFICIENT_SAMPLE_MAX,
    community_min: int = COMMUNITY_SIGNAL_MIN,
    min_for_concern: int = MIN_REPORTS_FOR_CONCERN,
    synthetic_badge: str | None,
    governance_note: str,
    privacy_note: str,
    limitations: list[str],
    engine_version: str,
    engine_name: str,
) -> CitizenSummary:
    total = len(rows)
    verified = [row for row in rows if row.verification_result == LOCATION_VERIFIED]
    rejected = [row for row in rows if row.submission_status == STATUS_REJECTED or row.verification_result == LOCATION_REJECTED]
    inconclusive = [row for row in rows if row.submission_status == STATUS_INCONCLUSIVE]
    ratings = [int(row.satisfaction_rating) for row in rows if row.satisfaction_rating is not None]
    distribution = {str(score): 0 for score in range(1, 6)}
    for rating in ratings:
        distribution[str(rating)] = distribution.get(str(rating), 0) + 1
    categories = [
        str(row.issue_category)
        for row in verified + [item for item in rows if item not in verified]
        if row.issue_category
    ]
    counts = Counter(categories)
    recurring = counts.most_common()
    recurring_payload = [
        {
            "category": category,
            "label": ISSUE_LABELS.get(category, category),
            "count": count,
        }
        for category, count in recurring
        if count >= 2
    ]
    themes = [
        ISSUE_LABELS.get(category, category)
        for category, count in recurring
        if count >= 2
    ]
    sample = sample_size_status(total, insufficient_max=insufficient_max, community_min=community_min)
    finding = aggregate_finding_for(
        verified_count=len(verified),
        recurring=recurring,
        min_for_concern=min_for_concern,
    )
    cap = _mode_cap(data_mode)
    if total == 0:
        confidence = 0.0
        explanation = "No citizen submissions are recorded for this project and data mode."
        finding = AGGREGATE_NONE
    elif total == 1:
        confidence = min(cap, 0.18)
        explanation = (
            "One citizen report is recorded. A single report does not dominate the "
            "project conclusion and is not treated as truth."
        )
        finding = AGGREGATE_INCONCLUSIVE
    else:
        verified_share = len(verified) / total
        confidence = min(cap, 0.16 + 0.04 * min(total, 8) + 0.08 * verified_share)
        if sample == SAMPLE_INSUFFICIENT:
            explanation = (
                f"{SAMPLE_INSUFFICIENT}. {total} submissions are recorded. "
                "This is not a project conclusion."
            )
        elif finding == AGGREGATE_COMMUNITY_CONCERN:
            explanation = (
                "Potential community concern: multiple independent citizen reports "
                "share a recurring issue category. This is supporting evidence for review, "
                "not a finding of project failure."
            )
        elif sample == SAMPLE_COMMUNITY:
            explanation = (
                f"{SAMPLE_COMMUNITY}. Aggregate citizen feedback is available for officer review."
            )
        else:
            explanation = (
                f"{SAMPLE_LIMITED}. Multiple reports are present but the sample is still small."
            )
        if finding == AGGREGATE_COMMUNITY_CONCERN and sample == SAMPLE_INSUFFICIENT:
            explanation = (
                f"{explanation} Recurring incomplete/quality reports were observed, but the "
                "sample remains insufficient for a community-level conclusion."
            )
    average = round(mean(ratings), 2) if ratings else None
    return CitizenSummary(
        project_id=project_id,
        internal_project_id=internal_project_id,
        scheme_id=scheme_id,
        data_mode=data_mode,
        total_submissions=total,
        verified_location_submissions=len(verified),
        rejected_submissions=len(rejected),
        inconclusive_submissions=len(inconclusive),
        average_satisfaction=average,
        satisfaction_distribution=distribution,
        recurring_issue_categories=recurring_payload,
        repeated_complaint_themes=themes,
        citizen_evidence_confidence=round(confidence, 4),
        sample_size_status=sample,
        aggregate_finding=finding,
        explanation=explanation,
        provenance=provenance,
        synthetic_badge=synthetic_badge,
        investigation_priority_unchanged=True,
        evidence_ids=evidence_ids,
        engine_version=engine_version,
        engine_name=engine_name,
        governance_note=governance_note,
        privacy_note=privacy_note,
        limitations=list(limitations),
    )
