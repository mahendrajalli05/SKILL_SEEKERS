from __future__ import annotations

from app.domain.enums import DataMode
from app.engines.need.constants import GOVERNANCE_NOTE, INCONCLUSIVE, WEIGHT_NOTE
from app.engines.need.evaluate import evaluate_need_impact
from tests.need_test_support import high_need_enrichment, sample_inputs


def test_explanation_states_prototype_weights_and_human_authority() -> None:
    result = evaluate_need_impact(
        sample_inputs(
            data_mode=DataMode.HYBRID,
            enrichment=high_need_enrichment("internal:need-impact:subject"),
        )
    )
    text = f"{result.explanation} {result.governance_note} {result.weight_note}"
    assert WEIGHT_NOTE in text
    assert "authorized officials" in text.casefold()
    assert "fraud" not in text.casefold()
    assert "sanction approved" not in text.casefold()
    assert "sanction denied" not in text.casefold()
    assert result.automatic_sanction is False


def test_inconclusive_explanation_does_not_force_ranking() -> None:
    result = evaluate_need_impact(sample_inputs(data_mode=DataMode.REAL))
    assert result.priority_class == INCONCLUSIVE
    assert "not forced" in result.explanation.casefold() or "inconclusive" in result.explanation.casefold()
    assert GOVERNANCE_NOTE in result.explanation or GOVERNANCE_NOTE == result.governance_note
    assert "historical" in result.explanation.casefold()
    assert "mp name is not used as a geographic substitute" in result.explanation.casefold()


def test_hybrid_explanation_labels_synthetic_values() -> None:
    result = evaluate_need_impact(
        sample_inputs(
            data_mode=DataMode.HYBRID,
            enrichment=high_need_enrichment("internal:need-impact:subject"),
        )
    )
    assert "TEST/SYNTHETIC" in result.explanation or result.enrichment_label == "TEST/SYNTHETIC"
    assert "government facts" in result.explanation.casefold() or "not government" in result.explanation.casefold()
