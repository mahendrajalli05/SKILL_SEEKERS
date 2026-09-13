"""Multi-signal overlap scoring for Overlap Intelligence V1.

High semantic similarity alone is Potential Overlap, never Potential Duplicate.
Scenario labels are not inputs.
"""

from __future__ import annotations

from app.engines.overlap.constants import (
    AMOUNT_SIMILAR_MIN,
    DATE_PROXIMATE_DAYS,
    FLAG_SCORE_THRESHOLD,
    GPS_PROXIMITY_M,
    HYBRID_GPS_CONFIDENCE_CAP,
    LOCATION_SIMILAR_MIN,
    MIN_SUPPORTING_FOR_DUPLICATE,
    MISSING_DESCRIPTION_CONFIDENCE,
    OVERALL_OVERLAP_MIN,
    REAL_CONFIDENCE_CAP,
    SEMANTIC_HIGH,
    SEMANTIC_NEAR_DUPLICATE,
    SEMANTIC_OVERLAP_MIN,
    WEIGHT_AMOUNT,
    WEIGHT_CATEGORY,
    WEIGHT_CONSTITUENCY,
    WEIGHT_DATE,
    WEIGHT_GPS,
    WEIGHT_LOCATION,
    WEIGHT_SEMANTIC,
)
from app.engines.overlap.similarity import (
    amount_similarity,
    date_proximity,
    gps_similarity,
    location_similarity,
)
from app.engines.overlap.types import (
    OverlapAssessmentOutcome,
    OverlapMode,
    OverlapRecord,
    PairSignals,
)


def _clip_score(value: float) -> int:
    return int(round(min(100.0, max(0.0, value))))


def _bool_as_float(value: bool | None) -> float | None:
    if value is None:
        return None
    return 1.0 if value else 0.0


def category_match(left: OverlapRecord, right: OverlapRecord) -> bool | None:
    if not left.category.strip() or not right.category.strip():
        return None
    return left.category.strip().casefold() == right.category.strip().casefold()


def constituency_match(left: OverlapRecord, right: OverlapRecord) -> bool | None:
    if not left.constituency_usable or not right.constituency_usable:
        return False if (left.constituency.strip() or right.constituency.strip()) else None
    if not left.constituency.strip() or not right.constituency.strip():
        return None
    return left.constituency.strip().casefold() == right.constituency.strip().casefold()


def _supporting_flags(
    signals: dict[str, float | None],
    *,
    date_gap_days: int | None,
    gps_distance_m: float | None,
) -> list[str]:
    flags: list[str] = []
    if signals.get("category") == 1.0:
        flags.append("category")
    if signals.get("constituency") == 1.0:
        flags.append("constituency")
    amount = signals.get("amount")
    if amount is not None and amount >= AMOUNT_SIMILAR_MIN:
        flags.append("amount")
    if date_gap_days is not None and date_gap_days <= DATE_PROXIMATE_DAYS:
        flags.append("date")
    location = signals.get("location")
    if location is not None and location >= LOCATION_SIMILAR_MIN:
        flags.append("location")
    if gps_distance_m is not None and gps_distance_m <= GPS_PROXIMITY_M:
        flags.append("gps")
    return flags


def overall_from_weights(values: dict[str, float | None]) -> float:
    """Renormalise over available signals only."""
    gps_available = values.get("gps") is not None
    weights = {
        "semantic": WEIGHT_SEMANTIC,
        "constituency": WEIGHT_CONSTITUENCY,
        "category": WEIGHT_CATEGORY,
        "amount": WEIGHT_AMOUNT,
        "date": WEIGHT_DATE,
        "location": WEIGHT_LOCATION * (0.5 if gps_available else 1.0),
        "gps": WEIGHT_GPS if gps_available else 0.0,
    }
    weighted_sum = 0.0
    weight_total = 0.0
    for name, weight in weights.items():
        value = values.get(name)
        if value is None or weight <= 0.0:
            continue
        weighted_sum += weight * value
        weight_total += weight
    if weight_total <= 0.0:
        return 0.0
    return weighted_sum / weight_total


def evidence_confidence_from_signals(
    *,
    values: dict[str, float | None],
    embedding_text_present: bool,
    mode: OverlapMode,
    gps_is_synthetic: bool,
) -> int:
    if not embedding_text_present and values.get("gps") is None:
        return MISSING_DESCRIPTION_CONFIDENCE
    points = 0
    if values.get("semantic") is not None:
        points += 18 if embedding_text_present else 8
    if values.get("category") is not None:
        points += 8
    if values.get("constituency") is not None:
        points += 14
    if values.get("amount") is not None:
        points += 10
    if values.get("date") is not None:
        points += 10
    if values.get("location") is not None:
        points += 12
    if values.get("gps") is not None:
        points += 16
    available = sum(1 for value in values.values() if value is not None)
    if available <= 1:
        points = min(points, 28)
    cap = REAL_CONFIDENCE_CAP
    if mode == OverlapMode.HYBRID_TEST and gps_is_synthetic:
        cap = HYBRID_GPS_CONFIDENCE_CAP
    elif mode == OverlapMode.HYBRID_TEST:
        cap = min(cap + 4, 72)
    return max(0, min(cap, points))


def classify_pair(
    *,
    semantic: float | None,
    overall: float,
    supporting: list[str],
    gps_distance_m: float | None,
    embedding_text_present: bool,
) -> OverlapAssessmentOutcome:
    if not embedding_text_present and semantic is None and gps_distance_m is None:
        return OverlapAssessmentOutcome.INSUFFICIENT_EVIDENCE

    gps_proximate = gps_distance_m is not None and gps_distance_m <= GPS_PROXIMITY_M
    semantic_high = semantic is not None and semantic >= SEMANTIC_NEAR_DUPLICATE
    if semantic_high and len(supporting) >= MIN_SUPPORTING_FOR_DUPLICATE:
        return OverlapAssessmentOutcome.POTENTIAL_DUPLICATE

    overlap = False
    if semantic is not None and semantic >= SEMANTIC_OVERLAP_MIN and supporting:
        overlap = True
    if semantic is not None and semantic >= SEMANTIC_HIGH:
        overlap = True
    if gps_proximate and (
        "constituency" in supporting
        or "location" in supporting
        or (semantic or 0.0) >= 0.50
    ):
        overlap = True
    if (
        semantic is not None
        and semantic >= SEMANTIC_OVERLAP_MIN
        and overall >= OVERALL_OVERLAP_MIN
    ):
        overlap = True

    if overlap:
        return OverlapAssessmentOutcome.POTENTIAL_OVERLAP
    return OverlapAssessmentOutcome.NOT_LINKED


def score_pair(
    left: OverlapRecord,
    right: OverlapRecord,
    semantic: float | None,
    *,
    mode: OverlapMode = OverlapMode.REAL,
) -> PairSignals:
    cat = category_match(left, right)
    const = constituency_match(left, right)
    amount = amount_similarity(left.allocation_amount, right.allocation_amount)
    date_sim, date_gap = date_proximity(left.recommended_date, right.recommended_date)
    location = location_similarity(left.place_text, right.place_text)
    gps_sim, gps_dist = gps_similarity(
        left.latitude, left.longitude, right.latitude, right.longitude
    )

    values: dict[str, float | None] = {
        "semantic": semantic,
        "constituency": _bool_as_float(const),
        "category": _bool_as_float(cat),
        "amount": amount,
        "date": date_sim,
        "location": location,
        "gps": gps_sim,
    }
    overall = overall_from_weights(values)
    supporting = _supporting_flags(values, date_gap_days=date_gap, gps_distance_m=gps_dist)
    embedding_present = bool(left.embedding_text.strip() and right.embedding_text.strip())
    outcome = classify_pair(
        semantic=semantic,
        overall=overall,
        supporting=supporting,
        gps_distance_m=gps_dist,
        embedding_text_present=embedding_present,
    )
    unavailable = tuple(name for name, value in values.items() if value is None)
    gps_synthetic = left.gps_is_synthetic or right.gps_is_synthetic
    confidence = evidence_confidence_from_signals(
        values=values,
        embedding_text_present=embedding_present,
        mode=mode,
        gps_is_synthetic=gps_synthetic,
    )
    geographic = location is not None or gps_sim is not None
    return PairSignals(
        semantic_similarity=None if semantic is None else round(semantic, 4),
        category_match=cat,
        constituency_match=const,
        amount_similarity=None if amount is None else round(amount, 4),
        date_proximity=None if date_sim is None else round(date_sim, 4),
        date_gap_days=date_gap,
        location_similarity=None if location is None else round(location, 4),
        gps_similarity=None if gps_sim is None else round(gps_sim, 4),
        gps_distance_m=None if gps_dist is None else round(gps_dist, 1),
        overall_score=round(overall, 4),
        overlap_score=_clip_score(100.0 * overall),
        evidence_confidence=confidence,
        supporting_count=len(supporting),
        supporting_signals=tuple(supporting),
        unavailable_signals=unavailable,
        outcome=outcome,
        geographic_evidence_available=geographic,
    )


def is_review_match(signals: PairSignals) -> bool:
    if signals.outcome in {
        OverlapAssessmentOutcome.POTENTIAL_DUPLICATE,
        OverlapAssessmentOutcome.POTENTIAL_OVERLAP,
    }:
        return (
            signals.overlap_score >= FLAG_SCORE_THRESHOLD
            or signals.outcome == OverlapAssessmentOutcome.POTENTIAL_DUPLICATE
        )
    return False
