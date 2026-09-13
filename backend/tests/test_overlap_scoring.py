from __future__ import annotations

from datetime import date

from app.engines.overlap.scoring import classify_pair, overall_from_weights, score_pair
from app.engines.overlap.text import combine_place_text, constituency_fields, embedding_text, rare_block_tokens
from app.engines.overlap.types import OverlapAssessmentOutcome, OverlapMode, OverlapRecord


def _record(
    project_id: int,
    *,
    work: str = "NA - Construction of water tanks",
    category: str = "Normal/Others",
    constituency: str = "KURNOOL",
    amount: int | None = 500_000,
    rec_date: date | None = date(2023, 6, 1),
    village: str = "",
    lat: float | None = None,
    lon: float | None = None,
) -> OverlapRecord:
    value, usable, kind, _reason = constituency_fields(constituency)
    return OverlapRecord(
        project_id=project_id,
        internal_project_id=f"internal:synthetic:overlap:{project_id}",
        source_work=work,
        work_description=work,
        embedding_text=embedding_text(work),
        category=category,
        constituency=value,
        constituency_usable=usable,
        constituency_kind=kind,
        state="Andhra Pradesh",
        allocation_amount=amount,
        recommended_date=rec_date,
        village=village,
        place_text=combine_place_text(village=village),
        rare_tokens=rare_block_tokens(work),
        latitude=lat,
        longitude=lon,
        gps_is_synthetic=lat is not None,
    )


def test_duplicate_text_with_supporting_signals_is_potential_duplicate() -> None:
    left = _record(1)
    right = _record(2, amount=510_000, rec_date=date(2023, 6, 10))
    signals = score_pair(left, right, 0.96)
    assert signals.outcome == OverlapAssessmentOutcome.POTENTIAL_DUPLICATE
    assert signals.constituency_match is True
    assert signals.category_match is True
    assert "constituency" in signals.supporting_signals
    assert "category" in signals.supporting_signals


def test_high_semantic_alone_is_potential_overlap_not_duplicate() -> None:
    left = _record(1, constituency="KURNOOL", category="Normal/Others", amount=200_000)
    right = _record(
        2,
        constituency="ELURU",
        category="Repair and Renovation",
        amount=5_000_000,
        rec_date=date(2023, 9, 1),
    )
    signals = score_pair(left, right, 0.93)
    assert signals.outcome == OverlapAssessmentOutcome.POTENTIAL_OVERLAP
    assert signals.supporting_count == 0 or signals.constituency_match is False
    assert classify_pair(
        semantic=0.93,
        overall=0.93,
        supporting=[],
        gps_distance_m=None,
        embedding_text_present=True,
    ) == OverlapAssessmentOutcome.POTENTIAL_OVERLAP


def test_same_category_different_work_types_not_linked() -> None:
    left = _record(1, work="NA - Construction of water tanks")
    right = _record(2, work="NA - Construction of roads, approach roads, link roads and pathways")
    signals = score_pair(left, right, 0.32)
    assert signals.outcome == OverlapAssessmentOutcome.NOT_LINKED
    assert signals.category_match is True


def test_same_amount_unrelated_projects_not_linked() -> None:
    left = _record(1, work="NA - Construction of water tanks", amount=500_000)
    right = _record(2, work="NA - Purchase of ambulance", amount=500_000)
    signals = score_pair(left, right, 0.18)
    assert signals.amount_similarity == 1.0
    assert signals.outcome == OverlapAssessmentOutcome.NOT_LINKED


def test_missing_fields_are_unavailable_not_zero() -> None:
    left = _record(1, amount=None, rec_date=None, village="")
    right = _record(2, amount=None, rec_date=None, village="")
    signals = score_pair(left, right, 0.80)
    assert signals.amount_similarity is None
    assert signals.date_proximity is None
    assert signals.location_similarity is None
    assert signals.gps_similarity is None
    assert "amount" in signals.unavailable_signals
    assert "date" in signals.unavailable_signals
    assert "location" in signals.unavailable_signals
    assert "gps" in signals.unavailable_signals


def test_missing_descriptions_are_insufficient() -> None:
    left = _record(1, work="")
    right = _record(2, work="")
    signals = score_pair(left, right, None)
    assert signals.outcome == OverlapAssessmentOutcome.INSUFFICIENT_EVIDENCE


def test_threshold_near_duplicate_requires_two_supports() -> None:
    outcome = classify_pair(
        semantic=0.95,
        overall=0.95,
        supporting=["category"],
        gps_distance_m=None,
        embedding_text_present=True,
    )
    assert outcome == OverlapAssessmentOutcome.POTENTIAL_OVERLAP
    duplicate = classify_pair(
        semantic=0.95,
        overall=0.95,
        supporting=["category", "constituency"],
        gps_distance_m=None,
        embedding_text_present=True,
    )
    assert duplicate == OverlapAssessmentOutcome.POTENTIAL_DUPLICATE


def test_overall_renormalises_when_gps_missing() -> None:
    with_gps = overall_from_weights(
        {
            "semantic": 0.9,
            "constituency": 1.0,
            "category": 1.0,
            "amount": 0.9,
            "date": 0.8,
            "location": None,
            "gps": 1.0,
        }
    )
    without_gps = overall_from_weights(
        {
            "semantic": 0.9,
            "constituency": 1.0,
            "category": 1.0,
            "amount": 0.9,
            "date": 0.8,
            "location": None,
            "gps": None,
        }
    )
    assert 0.0 < without_gps <= 1.0
    assert 0.0 < with_gps <= 1.0


def test_hybrid_gps_proximity_can_overlap_without_duplicate() -> None:
    left = _record(1, work="NA - Construction of water tanks", lat=15.8281, lon=78.0373)
    right = _record(2, work="NA - Construction of community halls", lat=15.8282, lon=78.0374)
    signals = score_pair(left, right, 0.25, mode=OverlapMode.HYBRID_TEST)
    assert signals.gps_distance_m is not None
    assert signals.gps_distance_m < 500
    assert signals.outcome == OverlapAssessmentOutcome.POTENTIAL_OVERLAP
    assert signals.outcome != OverlapAssessmentOutcome.POTENTIAL_DUPLICATE
    assert signals.evidence_confidence <= 70
