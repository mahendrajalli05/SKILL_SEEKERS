from __future__ import annotations

from app.domain.enums import DataMode
from app.engines.need.constants import INCONCLUSIVE
from app.engines.need.evaluate import evaluate_need_impact
from app.engines.need.types import ConstituencyContext
from tests.need_test_support import high_need_enrichment, sample_inputs


def test_evaluate_is_deterministic() -> None:
    inputs = sample_inputs(
        data_mode=DataMode.HYBRID,
        enrichment=high_need_enrichment("internal:need-impact:subject"),
    )
    first = evaluate_need_impact(inputs)
    second = evaluate_need_impact(inputs)
    assert first.priority_score == second.priority_score
    assert first.need.score == second.need.score
    assert first.impact.score == second.impact.score
    assert first.evidence_confidence == second.evidence_confidence
    assert first.priority_class == second.priority_class


def test_historical_constituency_counts_do_not_change_need() -> None:
    enrichment = high_need_enrichment("internal:need-impact:subject")
    sparse = ConstituencyContext(
        constituency="SPARSE",
        usable_as_geography=True,
        constituency_work_count=1,
        category_work_count=1,
        locality_work_count=None,
        locality_field=None,
        reason="contextual",
        used_as_need_score=False,
    )
    dense = ConstituencyContext(
        constituency="DENSE",
        usable_as_geography=True,
        constituency_work_count=400,
        category_work_count=80,
        locality_work_count=None,
        locality_field=None,
        reason="contextual",
        used_as_need_score=False,
    )
    left = evaluate_need_impact(
        sample_inputs(data_mode=DataMode.HYBRID, constituency="SPARSE", enrichment=enrichment),
        constituency_context=sparse,
    )
    right = evaluate_need_impact(
        sample_inputs(data_mode=DataMode.HYBRID, constituency="DENSE", enrichment=enrichment),
        constituency_context=dense,
    )
    assert left.need.score == right.need.score
    assert left.priority_score == right.priority_score
    assert sparse.used_as_need_score is False
    assert "not used as Need Score" in " ".join(left.contextual_evidence)


def test_allocation_amount_is_not_an_impact_proxy() -> None:
    enrichment = high_need_enrichment("internal:need-impact:subject")
    cheap = evaluate_need_impact(
        sample_inputs(data_mode=DataMode.HYBRID, allocation_amount=1, enrichment=enrichment)
    )
    costly = evaluate_need_impact(
        sample_inputs(data_mode=DataMode.HYBRID, allocation_amount=50_000_000, enrichment=enrichment)
    )
    assert cheap.impact.score == costly.impact.score
    assert cheap.need.score == costly.need.score


def test_real_missing_inputs_do_not_fabricate_values() -> None:
    result = evaluate_need_impact(sample_inputs(data_mode=DataMode.REAL))
    payload = result.as_dict()
    assert result.priority_class == INCONCLUSIVE
    assert payload["need"]["score"] is None
    assert "population" not in str(payload["need"]["score"])
    for component in result.need.components:
        if component.key == "population":
            assert component.available is False
            assert component.score is None
    assert result.automatic_sanction is False
