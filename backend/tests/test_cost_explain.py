from __future__ import annotations

from app.engines.cost.explain import explanation_for
from app.engines.cost.types import CostAssessmentOutcome


def test_why_flagged_uses_factual_calculation_and_required_terms() -> None:
    text, why_flagged, why_not = explanation_for(
        CostAssessmentOutcome.COST_ANOMALY,
        deviation_percentage=41.2,
        peer_count=28,
        peer_scope_label="same constituency and category",
        baseline=500_000,
        actual_amount=706_000,
        score=72,
        evidence_confidence=70,
        peer_quality=88,
        similarity_rationale="median work-title token Jaccard 0.80.",
        percentile_25=400_000,
        percentile_75=600_000,
    )
    assert why_flagged is not None
    assert why_not is None
    assert (
        "Allocation is 41.2% above the median of 28 comparable works "
        "in the same constituency and category."
    ) in why_flagged
    assert "Allocation Cost Anomaly" in why_flagged
    assert "Investigation Priority" in why_flagged
    assert "Evidence Confidence is 70" in why_flagged
    assert "Peer quality is 88/100" in why_flagged
    assert "not an expenditure anomaly" in why_flagged
    assert "fraud" not in why_flagged.casefold()
    assert text == why_flagged


def test_why_not_flagged_explains_within_peer_range() -> None:
    text, why_flagged, why_not = explanation_for(
        CostAssessmentOutcome.WITHIN_PEER_RANGE,
        deviation_percentage=4.2,
        peer_count=24,
        peer_scope_label="same geographic constituency, same category, and similar work title",
        baseline=500_000,
        actual_amount=521_000,
        score=12,
        percentile_25=250_000,
        percentile_75=700_000,
        evidence_confidence=80,
        peer_quality=92,
        similarity_rationale="median work-title token Jaccard 1.00.",
    )
    assert why_flagged is None
    assert why_not is not None
    assert "4.2% above" in why_not
    assert "median of 24 comparable works" in why_not
    assert "Not flagged as an Allocation Cost Anomaly" in why_not
    assert "Evidence Confidence is 80" in why_not
    assert "Peer quality is 92/100" in why_not
    assert "Investigation Priority" in why_not
    assert "fraud" not in why_not.casefold()
    assert text == why_not


def test_insufficient_evidence_explains_non_geographic_constituency() -> None:
    text, _why_flagged, why_not = explanation_for(
        CostAssessmentOutcome.INSUFFICIENT_EVIDENCE,
        peer_count=2,
        attempted_scopes=("state_category_work_type",),
        evidence_confidence=6,
        constituency_exclusion_reason=(
            "'Sitting Rajya Sabha' is a parliamentary house/chamber label in the extract, "
            "not a geographic parliamentary constituency. It is excluded from "
            "constituency-level geography."
        ),
    )
    assert "was not assessed" in text
    assert "Insufficient evidence" in text
    assert "Sitting Rajya Sabha" in text
    assert "Evidence Confidence is 6" in text
    assert why_not == text
    assert "fraud" not in text.casefold()


def test_invalid_amount_explanation() -> None:
    text, _why_flagged, why_not = explanation_for(
        CostAssessmentOutcome.INVALID_AMOUNT,
        evidence_confidence=0,
    )
    assert "missing, zero" in text
    assert "unit is unspecified" in text
    assert "Evidence Confidence is 0" in text
    assert "Allocation Cost Anomaly" in text
    assert why_not == text
    assert "fraud" not in text.casefold()
