from __future__ import annotations

from app.domain.enums import DataMode
from app.engines.need.constants import HIGH_PRIORITY, INCONCLUSIVE, LOW_PRIORITY
from app.engines.need.evaluate import evaluate_need_impact
from app.engines.need.rank import rank_assessments
from tests.need_test_support import high_need_enrichment, low_need_enrichment, sample_inputs


def _hybrid(project_id: int, internal_id: str, amount: int, enrichment, **overrides):
    return evaluate_need_impact(
        sample_inputs(
            project_id=project_id,
            internal_project_id=internal_id,
            allocation_amount=amount,
            data_mode=DataMode.HYBRID,
            enrichment=enrichment(internal_id),
            **overrides,
        )
    )


def test_ranking_orders_by_priority_score() -> None:
    high = _hybrid(1, "internal:need-impact:high-need", 1_000_000, high_need_enrichment)
    low = _hybrid(
        2,
        "internal:need-impact:low-need",
        1_000_000,
        low_need_enrichment,
        category="Normal/Others",
        work_description="Installation of commemorative statue",
    )
    ranked = rank_assessments([low, high])
    assert [item.project_id for item in ranked.items] == [1, 2]
    assert ranked.items[0].priority_class == HIGH_PRIORITY
    assert ranked.items[1].priority_class == LOW_PRIORITY
    assert ranked.items[0].why_ranked_above is not None
    assert "Priority Score" in ranked.items[0].why_ranked_above
    assert ranked.automatic_sanction is False
    assert ranked.planning_simulation is True
    assert ranked.sanction_decision is None if hasattr(ranked, "sanction_decision") else True
    blob = ranked.as_dict()
    assert blob["sanction_decision"] is None
    assert "sanction approved" not in ranked.explanation.casefold()


def test_budget_constrained_ranking() -> None:
    p1 = _hybrid(1, "internal:a", 3_000_000, high_need_enrichment)
    p2 = _hybrid(
        2,
        "internal:b",
        3_000_000,
        low_need_enrichment,
        category="Normal/Others",
        work_description="Installation of commemorative statue",
    )
    ranked = rank_assessments([high if False else p1, p2], available_budget=4_000_000, available_budget_crore=0.4)
    assert ranked.items[0].within_hypothetical_budget is True
    assert ranked.items[1].within_hypothetical_budget is False
    assert ranked.remaining_budget == 1_000_000
    assert "not a sanction" in (ranked.items[0].budget_note or "").casefold()
    assert "not a sanction denial" in (ranked.items[1].budget_note or "").casefold()


def test_inconclusive_is_not_forced_into_ranking() -> None:
    real = evaluate_need_impact(sample_inputs(project_id=9, data_mode=DataMode.REAL))
    high = _hybrid(1, "internal:need-impact:high-need", 500_000, high_need_enrichment)
    ranked = rank_assessments([real, high])
    assert [item.project_id for item in ranked.items] == [1]
    assert ranked.unranked[0].project_id == 9
    assert ranked.unranked[0].priority_class == INCONCLUSIVE
    assert ranked.unranked[0].rank is None


def test_tie_uses_confidence_then_project_id() -> None:
    first = _hybrid(10, "internal:tie-a", 100, high_need_enrichment)
    second = _hybrid(11, "internal:tie-b", 100, high_need_enrichment)
    assert first.priority_score == second.priority_score
    ranked = rank_assessments([second, first])
    assert [item.project_id for item in ranked.items] == [10, 11]
    assert "stable project id" in (ranked.items[0].why_ranked_above or "").casefold() or "project id" in (
        ranked.items[0].why_ranked_above or ""
    ).casefold()


def test_ranking_is_deterministic() -> None:
    high = _hybrid(3, "internal:need-impact:high-need", 100, high_need_enrichment)
    low = _hybrid(
        4,
        "internal:need-impact:low-need",
        100,
        low_need_enrichment,
        category="Normal/Others",
        work_description="Installation of commemorative statue",
    )
    first = rank_assessments([low, high])
    second = rank_assessments([high, low])
    assert [item.project_id for item in first.items] == [item.project_id for item in second.items]
    assert [item.priority_score for item in first.items] == [item.priority_score for item in second.items]
