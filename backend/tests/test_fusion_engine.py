from __future__ import annotations

import pytest

from app.domain.enums import DataMode, EvidenceDisposition
from app.engines.fusion.constants import INTEGRATED_WEIGHT_SUM
from app.engines.fusion.fuse import fuse_evidence
from app.engines.fusion.scoring import bounded_score, investigation_priority
from fusion_fixtures import make_signal_evidence


def _display_ip(raw: float) -> int:
    return bounded_score(raw / INTEGRATED_WEIGHT_SUM)


def test_all_four_signals_available() -> None:
    objects = [
        make_signal_evidence("cost", score=80, confidence=0.55, disposition=EvidenceDisposition.WHY_FLAGGED),
        make_signal_evidence("schedule", score=80, confidence=0.55, disposition=EvidenceDisposition.WHY_FLAGGED),
        make_signal_evidence("overlap", score=80, confidence=0.55, disposition=EvidenceDisposition.WHY_FLAGGED),
        make_signal_evidence(
            "compliance",
            score=None,
            confidence=0.55,
            disposition=EvidenceDisposition.WHY_FLAGGED,
            severity="attention",
            rule_ids=["R004"],
        ),
    ]
    result = fuse_evidence(objects, project_id=101, internal_project_id="internal:fusion:101")
    assert {item.signal_id for item in result.contributing_signals} == {
        "cost",
        "schedule",
        "overlap",
        "compliance",
    }
    raw = 0.25 * 80 + 0.15 * 80 + 0.15 * 80 + 0.15 * 80
    expected = _display_ip(raw)
    assert result.raw_risk == pytest.approx(raw)
    assert result.investigation_priority == expected
    assert result.investigation_priority == 80
    assert 0 <= result.investigation_priority <= 100
    assert 0 <= result.evidence_confidence <= 100
    assert result.investigation_priority != result.evidence_confidence
    assert result.available_weight == pytest.approx(0.70)
    assert result.available_signal_weight == pytest.approx(0.70)
    assert result.unavailable_signal_weight == pytest.approx(0.0)
    assert result.evidence_coverage == pytest.approx(1.0)
    assert "fraud" not in result.explanation.casefold()


def test_only_one_signal_available() -> None:
    result = fuse_evidence(
        [make_signal_evidence("cost", score=100, disposition=EvidenceDisposition.WHY_FLAGGED)],
        project_id=101,
    )
    assert result.raw_risk == pytest.approx(25)
    assert result.investigation_priority_0_100 == pytest.approx(35.7)
    assert result.investigation_priority == 36
    assert result.investigation_priority != 100
    assert result.available_weight == pytest.approx(0.25)
    assert result.available_signal_weight == pytest.approx(0.25)
    assert result.unavailable_signal_weight == pytest.approx(0.45)
    assert result.evidence_coverage == pytest.approx(0.25 / 0.70, rel=1e-3)
    assert {item.signal_id for item in result.contributing_signals} == {"cost"}
    names = {item.display_name for item in result.unavailable_signals}
    assert "Schedule" in names
    assert "Overlap" in names
    assert "Compliance" in names


def test_missing_signals_are_unavailable_not_zero_risk() -> None:
    result = fuse_evidence([], project_id=101, requested_data_mode=DataMode.REAL)
    assert result.investigation_priority == 0
    assert result.investigation_priority_0_100 == pytest.approx(0.0)
    assert result.raw_risk == pytest.approx(0.0)
    assert result.evidence_confidence == 0
    assert result.explanation_type.value == "INSUFFICIENT_EVIDENCE"
    assert result.available_weight == 0.0
    assert result.available_signal_weight == pytest.approx(0.0)
    assert result.unavailable_signal_weight == pytest.approx(0.70)
    assert result.evidence_coverage == pytest.approx(0.0)
    assert result.reserved_unavailable_weight == pytest.approx(0.30)
    future = {item.signal_id for item in result.unavailable_signals}
    assert {
        "field_evidence",
        "relationship_graph",
        "citizen_evidence",
        "geospatial",
        "image",
        "document",
        "milestone",
        "cost",
        "schedule",
        "overlap",
        "compliance",
    } <= future
    assert all(item.risk_score is None for item in result.unavailable_signals)
    assert "not redistributed" in result.explanation.lower() or "not redistributed" in result.explanation
    assert "inconclusive" in result.explanation.lower()


def test_not_assessable_evidence_does_not_count_as_low_risk() -> None:
    objects = [
        make_signal_evidence("cost", score=40, disposition=EvidenceDisposition.WHY_NOT_FLAGGED),
        make_signal_evidence(
            "schedule",
            score=None,
            disposition=EvidenceDisposition.NOT_ASSESSABLE,
            confidence=0.12,
            finding="Time Anomaly is not assessable: recommendation date and status only.",
        ),
    ]
    result = fuse_evidence(objects, project_id=101)
    assert result.raw_risk == pytest.approx(10)
    assert result.investigation_priority == _display_ip(10)
    schedule = next(item for item in result.all_signals if item.signal_id == "schedule")
    assert schedule.state.value == "NOT_ASSESSABLE"
    assert schedule.risk_score is None
    assert schedule.contribution == 0.0
    assert "not assessable" in result.explanation.lower()


def test_low_risk() -> None:
    objects = [
        make_signal_evidence("cost", score=8, disposition=EvidenceDisposition.WHY_NOT_FLAGGED),
        make_signal_evidence("schedule", score=5, disposition=EvidenceDisposition.WHY_NOT_FLAGGED),
        make_signal_evidence("overlap", score=10, disposition=EvidenceDisposition.WHY_NOT_FLAGGED),
        make_signal_evidence("compliance", score=None, disposition=EvidenceDisposition.WHY_NOT_FLAGGED),
    ]
    result = fuse_evidence(objects, project_id=101)
    raw = 0.25 * 8 + 0.15 * 5 + 0.15 * 10
    assert result.investigation_priority == _display_ip(raw)
    assert result.priority_band.value == "LOW"
    assert result.recommended_action.value == "MONITOR"
    assert result.explanation_type.value == "WHY_NOT_FLAGGED"


def test_medium_risk() -> None:
    objects = [
        make_signal_evidence("cost", score=72, disposition=EvidenceDisposition.WHY_FLAGGED),
        make_signal_evidence(
            "schedule",
            score=None,
            disposition=EvidenceDisposition.NOT_ASSESSABLE,
        ),
        make_signal_evidence("overlap", score=83, disposition=EvidenceDisposition.WHY_FLAGGED),
        make_signal_evidence(
            "compliance",
            score=None,
            disposition=EvidenceDisposition.WHY_FLAGGED,
            severity="watch",
            rule_ids=["R003"],
        ),
    ]
    result = fuse_evidence(objects, project_id=101)
    raw = 0.25 * 72 + 0.15 * 83 + 0.15 * 60
    expected = _display_ip(raw)
    assert result.investigation_priority == expected
    assert result.investigation_priority == 56
    assert result.priority_band.value == "HIGH"
    assert result.recommended_action.value == "INSPECT"


def test_high_risk() -> None:
    objects = [
        make_signal_evidence("cost", score=100, disposition=EvidenceDisposition.WHY_FLAGGED),
        make_signal_evidence("schedule", score=100, disposition=EvidenceDisposition.WHY_FLAGGED),
        make_signal_evidence("overlap", score=100, disposition=EvidenceDisposition.WHY_FLAGGED),
        make_signal_evidence(
            "compliance",
            score=None,
            disposition=EvidenceDisposition.WHY_FLAGGED,
            severity="attention",
            rule_ids=["R004"],
        ),
    ]
    result = fuse_evidence(objects, project_id=101)
    assert result.raw_risk == pytest.approx(67)
    assert result.investigation_priority == 96
    assert result.priority_band.value == "HIGH"
    assert result.recommended_action.value == "INVESTIGATE"
    assert result.explanation_type.value == "WHY_FLAGGED"
    assert "not a legal" in result.explanation.lower()


def test_low_evidence_confidence_is_not_equal_to_priority() -> None:
    result = fuse_evidence(
        [
            make_signal_evidence(
                "cost",
                score=100,
                confidence=0.10,
                peer_quality=20,
                disposition=EvidenceDisposition.WHY_FLAGGED,
            )
        ],
        project_id=101,
    )
    assert result.investigation_priority == 36
    assert result.evidence_confidence < 40
    assert result.evidence_confidence != result.investigation_priority
    assert "confidence" in result.explanation


def test_conflicting_signals() -> None:
    objects = [
        make_signal_evidence("cost", score=90, disposition=EvidenceDisposition.WHY_FLAGGED),
        make_signal_evidence("schedule", score=5, disposition=EvidenceDisposition.WHY_NOT_FLAGGED),
        make_signal_evidence("overlap", score=80, disposition=EvidenceDisposition.WHY_FLAGGED),
        make_signal_evidence("compliance", score=None, disposition=EvidenceDisposition.WHY_NOT_FLAGGED),
    ]
    result = fuse_evidence(objects, project_id=101)
    raw = 0.25 * 90 + 0.15 * 5 + 0.15 * 80
    assert result.investigation_priority == _display_ip(raw)
    assert result.priority_band.value == "HIGH"
    assert "conflict" in result.explanation.lower() or result.explanation_type.value == "WHY_FLAGGED"


def test_duplicate_evidence_is_not_double_counted() -> None:
    first = make_signal_evidence(
        "cost",
        score=40,
        evidence_id="ev:cost:101:allocation_cost_anomaly:REAL:aaa",
        disposition=EvidenceDisposition.WHY_NOT_FLAGGED,
    )
    second = make_signal_evidence(
        "cost",
        score=90,
        evidence_id="ev:cost:101:allocation_cost_anomaly:REAL:zzz",
        disposition=EvidenceDisposition.WHY_FLAGGED,
    )
    result = fuse_evidence([first, second, second], project_id=101)
    cost = next(item for item in result.contributing_signals if item.signal_id == "cost")
    assert cost.risk_score == 90
    assert result.raw_risk == pytest.approx(22.5)
    assert result.investigation_priority == _display_ip(22.5)
    assert result.investigation_priority != _display_ip(0.25 * 40 + 0.25 * 90)
    assert second.evidence_id in result.ignored_duplicate_evidence_ids or first.evidence_id in result.ignored_duplicate_evidence_ids
    assert result.ignored_duplicate_evidence_ids


def test_output_is_deterministic() -> None:
    objects = [
        make_signal_evidence("cost", score=41, disposition=EvidenceDisposition.WHY_NOT_FLAGGED),
        make_signal_evidence("overlap", score=66, disposition=EvidenceDisposition.WHY_FLAGGED),
    ]
    first = fuse_evidence(objects, project_id=101)
    second = fuse_evidence(objects, project_id=101)
    assert first.investigation_priority == second.investigation_priority
    assert first.investigation_priority_0_100 == second.investigation_priority_0_100
    assert first.raw_risk == second.raw_risk
    assert first.evidence_confidence == second.evidence_confidence
    assert first.explanation == second.explanation
    assert first.recommended_action == second.recommended_action
    assert first.evidence_ids == second.evidence_ids


def test_scores_are_bounded_0_100() -> None:
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
    assert 0 <= result.investigation_priority <= 100
    assert 0 <= result.investigation_priority_0_100 <= 100
    assert 0 <= result.evidence_confidence <= 100
    assert result.investigation_priority == 100
    empty = fuse_evidence([], project_id=101)
    assert result.investigation_priority >= empty.investigation_priority
    assert empty.investigation_priority == 0


def test_monotonicity() -> None:
    low = fuse_evidence(
        [make_signal_evidence("cost", score=20, disposition=EvidenceDisposition.WHY_NOT_FLAGGED)],
        project_id=101,
    )
    high = fuse_evidence(
        [make_signal_evidence("cost", score=80, disposition=EvidenceDisposition.WHY_FLAGGED)],
        project_id=101,
    )
    assert high.investigation_priority > low.investigation_priority
    four_low = fuse_evidence(
        [
            make_signal_evidence("cost", score=20, disposition=EvidenceDisposition.WHY_NOT_FLAGGED),
            make_signal_evidence("overlap", score=20, disposition=EvidenceDisposition.WHY_NOT_FLAGGED),
        ],
        project_id=101,
    )
    four_high = fuse_evidence(
        [
            make_signal_evidence("cost", score=20, disposition=EvidenceDisposition.WHY_NOT_FLAGGED),
            make_signal_evidence("overlap", score=80, disposition=EvidenceDisposition.WHY_FLAGGED),
        ],
        project_id=101,
    )
    assert four_high.investigation_priority > four_low.investigation_priority


def test_investigation_priority_uses_unrenormalized_weights() -> None:
    signals_high = [
        make_signal_evidence("cost", score=100, disposition=EvidenceDisposition.WHY_FLAGGED)
    ]
    result = fuse_evidence(signals_high, project_id=101)
    assert result.raw_risk == pytest.approx(25)
    assert result.investigation_priority == 36
    assert result.investigation_priority != 100
    assert result.unused_weight == pytest.approx(0.75)
    assert result.unavailable_signal_weight == pytest.approx(0.45)
    assert investigation_priority(result.all_signals) == 36
