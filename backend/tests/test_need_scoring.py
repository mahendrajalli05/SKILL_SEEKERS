from __future__ import annotations

from datetime import date

from app.domain.enums import DataMode
from app.engines.need.constants import (
    ESSENTIAL_SERVICE_HIGH_SCORE,
    ESSENTIAL_SERVICE_LOW_SCORE,
    HIGH_PRIORITY,
    INCONCLUSIVE,
    LOW_PRIORITY,
)
from app.engines.need.evaluate import evaluate_need_impact
from app.engines.need.scoring import (
    beneficiary_score,
    combine_priority,
    score_impact,
    score_need,
    waiting_urgency_score,
    weighted_available_score,
)
from app.engines.need.types import DimensionScore, SignalComponent
from tests.need_test_support import high_need_enrichment, low_need_enrichment, sample_inputs


def test_high_need_hybrid_case() -> None:
    inputs = sample_inputs(
        data_mode=DataMode.HYBRID,
        enrichment=high_need_enrichment("internal:need-impact:subject"),
    )
    need = score_need(inputs)
    assert need.available is True
    assert need.score is not None and need.score >= 85
    assert need.finding != INCONCLUSIVE
    assert all(item.synthetic for item in need.components if item.used_in_score and item.available)


def test_low_need_hybrid_case() -> None:
    inputs = sample_inputs(
        data_mode=DataMode.HYBRID,
        enrichment=low_need_enrichment("internal:need-impact:subject"),
    )
    need = score_need(inputs)
    assert need.available is True
    assert need.score is not None and need.score <= 20


def test_high_impact_from_observed_essential_service() -> None:
    inputs = sample_inputs(data_mode=DataMode.REAL, enrichment=None)
    impact = score_impact(inputs)
    assert impact.available is True
    assert impact.score == ESSENTIAL_SERVICE_HIGH_SCORE
    assert "census" in impact.explanation.casefold() or "work-type" in " ".join(impact.top_reasons).casefold() or "work-type" in impact.explanation.casefold()
    unavailable = {item.key for item in impact.components if not item.available}
    assert "beneficiary_count" in unavailable or "Beneficiary count" in impact.unavailable_inputs


def test_low_impact_from_observed_beautification() -> None:
    inputs = sample_inputs(
        data_mode=DataMode.REAL,
        category="Normal/Others",
        work_description="Installation of commemorative statue",
        enrichment=None,
    )
    impact = score_impact(inputs)
    assert impact.available is True
    assert impact.score == ESSENTIAL_SERVICE_LOW_SCORE


def test_real_need_is_inconclusive_without_invented_population() -> None:
    inputs = sample_inputs(data_mode=DataMode.REAL, enrichment=None)
    need = score_need(inputs)
    assert need.available is False
    assert need.score is None
    assert need.finding == INCONCLUSIVE
    assert "not invented" in need.explanation.casefold() or "were not invented" in need.explanation.casefold()
    for item in need.components:
        if item.key in {"population", "infrastructure_gap", "underserved_area"}:
            assert item.available is False
            assert item.score is None


def test_missing_inputs_make_impact_inconclusive() -> None:
    inputs = sample_inputs(
        data_mode=DataMode.REAL,
        category="Normal/Others",
        work_description="Misc package item",
        enrichment=None,
    )
    impact = score_impact(inputs)
    assert impact.available is False
    assert impact.score is None
    assert impact.finding == INCONCLUSIVE


def test_overall_inconclusive_when_need_unavailable() -> None:
    result = evaluate_need_impact(sample_inputs(data_mode=DataMode.REAL))
    assert result.priority_class == INCONCLUSIVE
    assert result.priority_score is None
    assert result.automatic_sanction is False
    assert result.need.available is False
    assert result.impact.available is True


def test_hybrid_high_priority_class() -> None:
    result = evaluate_need_impact(
        sample_inputs(
            data_mode=DataMode.HYBRID,
            enrichment=high_need_enrichment("internal:need-impact:subject"),
        )
    )
    assert result.priority_class == HIGH_PRIORITY
    assert result.priority_score is not None and result.priority_score >= 70
    assert result.enrichment_label == "TEST/SYNTHETIC"
    assert result.automatic_sanction is False


def test_hybrid_low_priority_class() -> None:
    result = evaluate_need_impact(
        sample_inputs(
            data_mode=DataMode.HYBRID,
            category="Normal/Others",
            work_description="Installation of commemorative statue",
            enrichment=low_need_enrichment("internal:need-impact:subject"),
        )
    )
    assert result.priority_class == LOW_PRIORITY
    assert result.priority_score is not None and result.priority_score < 40


def test_real_mode_does_not_consume_enrichment() -> None:
    result = evaluate_need_impact(
        sample_inputs(
            data_mode=DataMode.REAL,
            enrichment=high_need_enrichment("internal:need-impact:subject"),
        )
    )
    assert result.need.available is False
    assert result.priority_class == INCONCLUSIVE
    assert result.enrichment_used is False
    assert result.need.score is None


def test_historical_counts_are_not_need_inputs() -> None:
    need = score_need(sample_inputs(data_mode=DataMode.REAL))
    keys = {item.key for item in need.components if item.used_in_score}
    assert "previous_projects" not in keys
    assert "historical_funding" not in keys
    assert "constituency_work_count" not in keys


def test_beneficiary_bands_are_deterministic() -> None:
    assert beneficiary_score(None) is None
    assert beneficiary_score(0) == 0.0
    assert beneficiary_score(12_000) == 95.0
    assert waiting_urgency_score(date(2023, 6, 1), date(2026, 9, 10)) == 88.0


def test_weighted_score_renormalizes_available_only() -> None:
    components = [
        SignalComponent(
            key="a",
            label="a",
            available=True,
            score=100,
            weight=0.30,
            source="test",
            data_mode="HYBRID",
            synthetic=True,
        ),
        SignalComponent(
            key="b",
            label="b",
            available=False,
            score=None,
            weight=0.70,
            source="unavailable",
            data_mode="HYBRID",
        ),
    ]
    assert weighted_available_score(components) == 100.0


def test_combine_priority_requires_need_and_impact() -> None:
    need = DimensionScore("need", None, False, 0.18, INCONCLUSIVE, "missing")
    impact = DimensionScore("impact", 85, True, 0.4, "IMPACT_ASSESSED", "ok")
    urgency = DimensionScore("urgency", 50, True, 0.4, "URGENCY_ASSESSED", "ok")
    score, klass = combine_priority(need, impact, urgency)
    assert score is None
    assert klass == INCONCLUSIVE
