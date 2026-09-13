from __future__ import annotations

from app.engines.compliance.constants import ENGINE_VERSION as COMPLIANCE_VERSION
from app.engines.cost.constants import ENGINE_VERSION as COST_VERSION
from app.engines.document.constants import ENGINE_VERSION as DOCUMENT_VERSION
from app.engines.fusion.constants import ENGINE_VERSION as FUSION_VERSION
from app.engines.geo.constants import ENGINE_VERSION as GEO_VERSION
from app.engines.graph.constants import ENGINE_VERSION as GRAPH_VERSION
from app.engines.image.constants import ENGINE_VERSION as IMAGE_VERSION
from app.engines.milestone.assess import HOLD, INCONCLUSIVE, INSPECT, PROCEED, assess, recommend
from app.engines.milestone.amounts import cumulative_for, remaining_for, total_planned_amount
from app.engines.milestone.constants import ENGINE_VERSION, GOVERNANCE_NOTE, HYBRID_NOTICE
from app.engines.milestone.types import AssessmentInputs
from app.engines.need.constants import ENGINE_VERSION as NEED_VERSION
from app.engines.overlap.constants import ENGINE_VERSION as OVERLAP_VERSION
from app.engines.pce.constants import ENGINE_VERSION as PCE_VERSION
from app.engines.time.constants import ENGINE_VERSION as TIME_VERSION


def test_frozen_engines_unchanged() -> None:
    assert COST_VERSION == "cost-peer-v1.1"
    assert TIME_VERSION == "time-peer-v1"
    assert OVERLAP_VERSION == "overlap-multi-v1"
    assert COMPLIANCE_VERSION == "compliance-rules-v1"
    assert FUSION_VERSION == "risk-fusion-v1.1"
    assert GRAPH_VERSION == "relationship-graph-v1"
    assert PCE_VERSION == "plan-claim-evidence-v1"
    assert DOCUMENT_VERSION == "document-blueprint-v1"
    assert IMAGE_VERSION == "image-evidence-v1"
    assert GEO_VERSION == "geospatial-consistency-v1"
    assert NEED_VERSION == "need-impact-v1"
    assert ENGINE_VERSION == "milestone-advisor-v1"


def test_governance_wording() -> None:
    assert "does not release funds" in GOVERNANCE_NOTE.casefold()
    assert "authorized officials" in GOVERNANCE_NOTE.casefold()
    assert "fraud" not in GOVERNANCE_NOTE.casefold()
    assert "pfms" not in GOVERNANCE_NOTE.casefold()
    assert "milestone fields are synthetic" in HYBRID_NOTICE.casefold()


def test_amount_cumulative_and_remaining() -> None:
    ordered = [(1, 100_000.0), (2, 150_000.0), (3, 50_000.0)]
    assert cumulative_for(milestone_number=2, planned_amount=150_000.0, ordered=ordered) == 250_000.0
    assert cumulative_for(milestone_number=1, planned_amount=100_000.0, ordered=ordered) == 100_000.0
    total = total_planned_amount(ordered)
    assert total == 300_000.0
    assert remaining_for(cumulative_amount=250_000.0, total_planned=total) == 50_000.0
    assert cumulative_for(milestone_number=2, planned_amount=None, ordered=ordered) is None
    assert total_planned_amount([(1, None), (2, None)]) is None


def test_recommend_proceed_hold_inspect_inconclusive() -> None:
    proceed, _ = recommend(
        AssessmentInputs(
            has_claim=True,
            has_required_evidence=True,
            pce_result="CONSISTENT",
        )
    )
    assert proceed == PROCEED

    hold, _ = recommend(
        AssessmentInputs(
            has_claim=True,
            has_required_evidence=True,
            pce_result="MISMATCH",
        )
    )
    assert hold == HOLD

    hold_missing, _ = recommend(
        AssessmentInputs(
            has_claim=True,
            has_required_evidence=False,
            pce_result="INCONCLUSIVE",
        )
    )
    assert hold_missing == HOLD

    inspect, concerns = recommend(
        AssessmentInputs(
            has_claim=True,
            has_required_evidence=True,
            pce_result="MISMATCH",
            geo_mismatch=True,
            image_reuse=True,
        )
    )
    assert inspect == INSPECT
    assert "geo_mismatch" in concerns
    assert "image_reuse" in concerns

    inspect_geo, _ = recommend(
        AssessmentInputs(
            has_claim=True,
            has_required_evidence=True,
            pce_result="CONSISTENT",
            geo_mismatch=True,
        )
    )
    assert inspect_geo == INSPECT

    inconclusive, _ = recommend(
        AssessmentInputs(
            has_claim=False,
            has_required_evidence=False,
            pce_result="INCONCLUSIVE",
        )
    )
    assert inconclusive == INCONCLUSIVE


def test_risk_score_alone_does_not_force_inspect() -> None:
    result = assess(
        AssessmentInputs(
            has_claim=True,
            has_required_evidence=True,
            pce_result="CONSISTENT",
            cost_flagged=True,
        )
    )
    assert result.recommendation == PROCEED
    assert result.funds_released is False
    assert result.payment_executed is False
    assert result.automatic_sanction is False


def test_deterministic_assessment() -> None:
    inputs = AssessmentInputs(
        has_claim=True,
        has_required_evidence=True,
        pce_result="CONSISTENT",
        cost_flagged=True,
        schedule_mismatch=True,
    )
    first = assess(inputs)
    second = assess(inputs)
    assert first.recommendation == second.recommendation == INSPECT
    assert first.independent_concerns == second.independent_concerns
