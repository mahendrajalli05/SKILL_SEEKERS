from __future__ import annotations

import pytest

from app.domain.enums import DataMode, EvidenceDisposition
from app.engines.fusion.constants import INTEGRATED_WEIGHT_SUM
from app.engines.fusion.fuse import fuse_evidence
from app.engines.fusion.scoring import bounded_score, evidence_confidence, investigation_priority
from fusion_fixtures import make_signal_evidence


def _display_ip(raw: float) -> int:
    return bounded_score(raw / INTEGRATED_WEIGHT_SUM)


def test_all_four_signals_at_100_produce_ip_100() -> None:
    result = fuse_evidence(
        [
            make_signal_evidence("cost", score=100, disposition=EvidenceDisposition.WHY_FLAGGED),
            make_signal_evidence("schedule", score=100, disposition=EvidenceDisposition.WHY_FLAGGED),
            make_signal_evidence("overlap", score=100, disposition=EvidenceDisposition.WHY_FLAGGED),
            make_signal_evidence(
                "compliance",
                score=None,
                disposition=EvidenceDisposition.WHY_FLAGGED,
                severity="attention",
                rule_ids=["R001", "R002", "R004"],
            ),
        ],
        project_id=101,
    )
    assert result.raw_risk == pytest.approx(70)
    assert result.investigation_priority_0_100 == pytest.approx(100.0)
    assert result.investigation_priority == 100
    assert result.available_signal_weight == pytest.approx(0.70)
    assert result.unavailable_signal_weight == pytest.approx(0.0)
    assert result.evidence_coverage == pytest.approx(1.0)


def test_one_signal_retains_missing_signal_penalty() -> None:
    cost_only = fuse_evidence(
        [make_signal_evidence("cost", score=100, disposition=EvidenceDisposition.WHY_FLAGGED)],
        project_id=101,
    )
    schedule_only = fuse_evidence(
        [make_signal_evidence("schedule", score=100, disposition=EvidenceDisposition.WHY_FLAGGED)],
        project_id=101,
    )
    assert cost_only.raw_risk == pytest.approx(25)
    assert cost_only.available_signal_weight == pytest.approx(0.25)
    assert cost_only.unavailable_signal_weight == pytest.approx(0.45)
    assert cost_only.investigation_priority_0_100 == pytest.approx(35.7)
    assert cost_only.investigation_priority == 36
    assert cost_only.investigation_priority != 100
    assert schedule_only.raw_risk == pytest.approx(15)
    assert schedule_only.investigation_priority == _display_ip(15)
    assert schedule_only.investigation_priority != 100
    assert schedule_only.available_signal_weight == pytest.approx(0.15)
    assert schedule_only.unavailable_signal_weight == pytest.approx(0.55)


def test_no_signals_produce_zero_inconclusive() -> None:
    result = fuse_evidence([], project_id=101)
    assert result.investigation_priority == 0
    assert result.raw_risk == pytest.approx(0.0)
    assert result.evidence_confidence == 0
    assert result.explanation_type.value == "INSUFFICIENT_EVIDENCE"
    assert "inconclusive" in result.explanation.lower()


def test_missing_signals_are_not_silently_renormalized() -> None:
    result = fuse_evidence(
        [make_signal_evidence("cost", score=100, disposition=EvidenceDisposition.WHY_FLAGGED)],
        project_id=101,
    )
    available_only = (0.25 * 100) / 0.25
    assert available_only == 100
    assert result.investigation_priority != 100
    assert result.investigation_priority == _display_ip(25)
    four = fuse_evidence(
        [
            make_signal_evidence("cost", score=100, disposition=EvidenceDisposition.WHY_FLAGGED),
            make_signal_evidence("schedule", score=100, disposition=EvidenceDisposition.WHY_FLAGGED),
            make_signal_evidence("overlap", score=100, disposition=EvidenceDisposition.WHY_FLAGGED),
            make_signal_evidence(
                "compliance",
                score=None,
                disposition=EvidenceDisposition.WHY_FLAGGED,
                severity="attention",
                rule_ids=["R001", "R002", "R004"],
            ),
        ],
        project_id=101,
    )
    assert four.investigation_priority > result.investigation_priority


def test_evidence_confidence_remains_independent() -> None:
    high_ip_low_ec = fuse_evidence(
        [
            make_signal_evidence(
                "cost",
                score=100,
                confidence=0.10,
                peer_quality=10,
                disposition=EvidenceDisposition.WHY_FLAGGED,
            )
        ],
        project_id=101,
    )
    low_ip_higher_ec = fuse_evidence(
        [
            make_signal_evidence("cost", score=8, confidence=0.90, disposition=EvidenceDisposition.WHY_NOT_FLAGGED),
            make_signal_evidence("schedule", score=5, confidence=0.90, disposition=EvidenceDisposition.WHY_NOT_FLAGGED),
            make_signal_evidence("overlap", score=4, confidence=0.90, disposition=EvidenceDisposition.WHY_NOT_FLAGGED),
            make_signal_evidence(
                "compliance",
                score=None,
                confidence=0.90,
                disposition=EvidenceDisposition.WHY_NOT_FLAGGED,
            ),
        ],
        project_id=101,
    )
    assert high_ip_low_ec.investigation_priority > low_ip_higher_ec.investigation_priority
    assert high_ip_low_ec.evidence_confidence != high_ip_low_ec.investigation_priority
    assert low_ip_higher_ec.evidence_confidence != low_ip_higher_ec.investigation_priority
    assert high_ip_low_ec.evidence_confidence < low_ip_higher_ec.evidence_confidence


def test_real_and_hybrid_modes_remain_distinguishable() -> None:
    real_objects = [
        make_signal_evidence("cost", score=80, data_mode=DataMode.REAL, disposition=EvidenceDisposition.WHY_FLAGGED),
        make_signal_evidence(
            "overlap", score=80, data_mode=DataMode.REAL, disposition=EvidenceDisposition.WHY_FLAGGED
        ),
    ]
    hybrid_objects = [
        make_signal_evidence("cost", score=80, data_mode=DataMode.REAL, disposition=EvidenceDisposition.WHY_FLAGGED),
        make_signal_evidence(
            "overlap", score=80, data_mode=DataMode.HYBRID, disposition=EvidenceDisposition.WHY_FLAGGED
        ),
    ]
    real = fuse_evidence(real_objects, project_id=101, requested_data_mode=DataMode.REAL)
    hybrid = fuse_evidence(hybrid_objects, project_id=101, requested_data_mode=DataMode.HYBRID)
    assert real.data_mode == DataMode.REAL
    assert hybrid.data_mode == DataMode.HYBRID
    assert real.investigation_priority == hybrid.investigation_priority
    assert "REAL" in real.explanation
    assert "HYBRID" in hybrid.explanation
    assert hybrid.evidence_confidence <= 72
    assert "synthetic enrichment" in hybrid.explanation


def test_display_formula_example_cost_100() -> None:
    result = fuse_evidence(
        [make_signal_evidence("cost", score=100, disposition=EvidenceDisposition.WHY_FLAGGED)],
        project_id=101,
    )
    assert result.raw_risk == pytest.approx(25)
    assert result.available_signal_weight == pytest.approx(0.25)
    assert result.unavailable_signal_weight == pytest.approx(0.45)
    assert result.investigation_priority_0_100 == pytest.approx(35.7)
    assert result.investigation_priority == 36
    assert "Investigation Priority" in result.explanation
    assert "Evidence Confidence" in result.explanation
    assert "Available signals" in result.explanation
    assert "Unavailable signals" in result.explanation
    assert "Top contributing signals" in result.explanation


def test_bounded_and_deterministic_display_score() -> None:
    objects = [
        make_signal_evidence("cost", score=41, disposition=EvidenceDisposition.WHY_NOT_FLAGGED),
        make_signal_evidence("overlap", score=66, disposition=EvidenceDisposition.WHY_FLAGGED),
    ]
    first = fuse_evidence(objects, project_id=101)
    second = fuse_evidence(objects, project_id=101)
    assert first.investigation_priority == second.investigation_priority
    assert 0 <= first.investigation_priority <= 100
    assert investigation_priority(first.all_signals) == first.investigation_priority
    empty_ec = evidence_confidence([], data_mode=DataMode.REAL)
    assert empty_ec == 0
