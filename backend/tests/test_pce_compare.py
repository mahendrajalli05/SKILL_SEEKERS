from __future__ import annotations

from datetime import date

from app.db import get_session_factory
from app.domain.enums import DataMode
from app.engines.cost.constants import ENGINE_VERSION as COST_VERSION
from app.engines.compliance.constants import ENGINE_VERSION as COMPLIANCE_VERSION
from app.engines.fusion.constants import ENGINE_VERSION as FUSION_VERSION
from app.engines.graph.constants import ENGINE_VERSION as GRAPH_VERSION
from app.engines.overlap.constants import ENGINE_VERSION as OVERLAP_VERSION
from app.engines.pce.compare import (
    compare_plan_claim_evidence,
    format_amount,
    overall_result,
    relative_difference,
)
from app.engines.pce.constants import ENGINE_VERSION, RELATIVE_MISMATCH_THRESHOLD
from app.engines.pce.service import (
    record_claim,
    record_evidence,
    record_plan,
    verify_project,
)
from app.engines.pce.types import AssembledClaim, AssembledEvidenceItem, ConsistencyStatus
from app.engines.time.constants import ENGINE_VERSION as TIME_VERSION
from app.models.project import Project


SYNTHETIC_LABEL = "SYNTHETIC: plan-claim-evidence unit test (not a government project)"


def _insert(session, **overrides: object) -> Project:
    values: dict[str, object] = {
        "internal_project_id": "internal:synthetic:pce:subject",
        "internal_id_kind": "internal_surrogate_hash",
        "internal_id_scheme": "sarvsakshi_internal_work_v1",
        "source_dataset": "github_vonter_india-mplads-works_MPLADS.csv",
        "is_synthetic": False,
        "lifecycle_stage": "ONGOING",
        "state": "Andhra Pradesh",
        "constituency": "KURNOOL",
        "category": "Normal/Others",
        "work_description": "NA - Construction of community hall",
        "allocation_amount": 2_000_000,
        "recommended_date": date(2023, 6, 1),
        "status": "Ongoing",
    }
    values.update(overrides)
    row = Project(**values)
    session.add(row)
    session.flush()
    return row


def test_frozen_engines_unchanged(client) -> None:
    assert COST_VERSION == "cost-peer-v1.1"
    assert TIME_VERSION == "time-peer-v1"
    assert OVERLAP_VERSION == "overlap-multi-v1"
    assert COMPLIANCE_VERSION == "compliance-rules-v1"
    assert FUSION_VERSION == "risk-fusion-v1.1"
    assert GRAPH_VERSION == "relationship-graph-v1"
    assert ENGINE_VERSION == "plan-claim-evidence-v1"
    assert RELATIVE_MISMATCH_THRESHOLD == 0.10


def test_nineteen_vs_twenty_lakh_is_consistent() -> None:
    assert relative_difference(1_900_000, 2_000_000) < RELATIVE_MISMATCH_THRESHOLD
    assert "14" in format_amount(1_400_000)
    assert "lakh" in format_amount(1_400_000)


def test_compare_consistent_quantity_and_cost() -> None:
    plan = _plan(dimensions=2000, budget=2_000_000, milestone=2_000_000)
    claim = _claim(quantity=1950, expenditure=1_900_000, progress=100)
    evidence = [_evidence(quantity=1940, expenditure=1_900_000)]
    rows = compare_plan_claim_evidence(plan, claim, evidence)
    by_id = {item.comparison_id: item for item in rows}
    assert by_id["quantity_plan_vs_claim"].status == ConsistencyStatus.CONSISTENT
    assert by_id["cost_plan_vs_claim"].status == ConsistencyStatus.CONSISTENT
    assert by_id["cost_claim_vs_milestone"].status == ConsistencyStatus.CONSISTENT
    assert overall_result(rows, has_claim=True, has_evidence=True) == ConsistencyStatus.CONSISTENT


def test_milestone_underspend_is_consistent() -> None:
    plan = _plan(dimensions=None, budget=1_500_000, milestone=1_500_000)
    claim = _claim(quantity=None, expenditure=1_400_000, progress=80)
    evidence = [_evidence(quantity=None, expenditure=1_400_000, kind="pdf")]
    rows = compare_plan_claim_evidence(plan, claim, evidence)
    by_id = {item.comparison_id: item for item in rows}
    assert by_id["cost_claim_vs_milestone"].status == ConsistencyStatus.CONSISTENT
    assert "no expenditure mismatch" in by_id["cost_claim_vs_milestone"].explanation.casefold()


def test_compare_quantity_mismatch() -> None:
    plan = _plan(dimensions=2000, budget=2_000_000)
    claim = _claim(quantity=2000, expenditure=2_000_000, progress=100)
    evidence = [_evidence(quantity=800)]
    rows = compare_plan_claim_evidence(plan, claim, evidence)
    by_id = {item.comparison_id: item for item in rows}
    assert by_id["quantity_claim_vs_evidence"].status == ConsistencyStatus.MISMATCH
    assert overall_result(rows, has_claim=True, has_evidence=True) == ConsistencyStatus.MISMATCH
    blob = " ".join(item.explanation for item in rows).casefold()
    assert "fraud" not in blob


def test_compare_inconclusive_photo_only() -> None:
    plan = _plan(dimensions=None, budget=2_000_000)
    claim = _claim(quantity=None, expenditure=None, progress=100)
    evidence = [_evidence(quantity=None, kind="image")]
    rows = compare_plan_claim_evidence(plan, claim, evidence)
    assert overall_result(rows, has_claim=True, has_evidence=True) == ConsistencyStatus.INCONCLUSIVE
    text = " ".join(item.explanation for item in rows)
    assert "sufficient information" in text.casefold() or "photo" in text.casefold()


def test_missing_plan_claim_or_evidence_is_inconclusive(client) -> None:
    session = get_session_factory()()
    try:
        project = _insert(session, internal_project_id="internal:synthetic:pce:missing")
        session.commit()
        result = verify_project(session, project, DataMode.REAL, persist=True)
        session.commit()
        assert result.overall_result == ConsistencyStatus.INCONCLUSIVE
        assert "recorded claim" in " ".join(result.missing_information).casefold() or any(
            "claim" in item.casefold() for item in result.missing_information
        )
        assert "fraud" not in result.explanation.casefold()
    finally:
        session.close()


def test_cost_mismatch_and_expenditure_unavailable(client) -> None:
    session = get_session_factory()()
    try:
        project = _insert(session, internal_project_id="internal:synthetic:pce:cost")
        record_plan(
            session,
            project,
            {
                "dimensions_value": 2000,
                "dimensions_unit": "sq.ft",
                "budget_estimate": 1_500_000,
                "milestone_amount": 1_500_000,
            },
            DataMode.REAL,
        )
        record_claim(
            session,
            project,
            {"claimed_quantity": 2000, "claimed_quantity_unit": "sq.ft", "claimed_expenditure": 2_400_000},
            DataMode.REAL,
        )
        record_evidence(
            session,
            project,
            {"document_type": "pdf", "filename": "bill.pdf", "observed_expenditure": 2_400_000},
            DataMode.REAL,
        )
        mismatched = verify_project(session, project, DataMode.REAL, persist=False)
        assert mismatched.overall_result == ConsistencyStatus.MISMATCH

        project2 = _insert(
            session,
            internal_project_id="internal:synthetic:pce:exp-missing",
            allocation_amount=1_000_000,
        )
        record_claim(
            session,
            project2,
            {"claimed_progress_percent": 50, "claimed_completion_state": "ongoing"},
            DataMode.REAL,
        )
        record_evidence(
            session,
            project2,
            {"document_type": "pdf", "filename": "note.pdf"},
            DataMode.REAL,
        )
        unavailable = verify_project(session, project2, DataMode.REAL, persist=False)
        assert unavailable.overall_result == ConsistencyStatus.INCONCLUSIVE
        assert any("expenditure" in item.casefold() for item in unavailable.missing_information)
    finally:
        session.close()


def test_unit_mismatch_is_inconclusive_not_converted() -> None:
    plan = _plan(dimensions=2000, budget=2_000_000)
    plan.dimensions_unit = "sq.ft"
    claim = _claim(quantity=186, expenditure=1_900_000)
    claim.claimed_quantity_unit = "sq.m"
    rows = compare_plan_claim_evidence(plan, claim, [])
    by_id = {item.comparison_id: item for item in rows}
    assert by_id["quantity_plan_vs_claim"].status == ConsistencyStatus.INCONCLUSIVE
    assert "conversion" in by_id["quantity_plan_vs_claim"].explanation.casefold()
    assert by_id["quantity_cost_conversion"].status == ConsistencyStatus.INCONCLUSIVE
    assert "unit rates" in by_id["quantity_cost_conversion"].explanation.casefold()


def test_no_unsupported_inference_from_photo() -> None:
    plan = _plan(dimensions=2000, budget=2_000_000)
    claim = _claim(quantity=2000, expenditure=1_900_000, progress=100)
    evidence = [_evidence(quantity=None, kind="image")]
    rows = compare_plan_claim_evidence(plan, claim, evidence)
    completion = [item for item in rows if item.comparison_id == "completion_claim_vs_evidence"]
    assert completion
    assert completion[0].status == ConsistencyStatus.INCONCLUSIVE


def _plan(*, dimensions: float | None, budget: float | None, milestone: float | None = None):
    from app.engines.pce.types import AssembledPlan

    return AssembledPlan(
        project_id=1,
        internal_project_id="internal:test",
        data_mode=DataMode.REAL,
        sanctioned_scope="community hall",
        budget_estimate=budget,
        budget_from_extract=True,
        blueprint_document_id=None,
        dimensions_value=dimensions,
        dimensions_unit="sq.ft" if dimensions is not None else None,
        milestone_label="M1" if milestone else None,
        milestone_amount=milestone,
        planned_start_date=None,
        planned_completion_date=None,
        source="test",
        provenance={"notes": "real MPLADS project records from the cleaned work-level extract."},
        recorded=dimensions is not None or milestone is not None,
    )


def _claim(*, quantity: float | None, expenditure: float | None, progress: float | None = None) -> AssembledClaim:
    return AssembledClaim(
        project_id=1,
        claim_id=1,
        data_mode=DataMode.REAL,
        claimed_progress=None,
        claimed_progress_percent=progress,
        claimed_expenditure=expenditure,
        claimed_completion_state="completed" if progress == 100 else None,
        claimed_quantity=quantity,
        claimed_quantity_unit="sq.ft" if quantity is not None else None,
        milestone_claimed="M1",
        claim_date="2024-06-01",
        claimant_source="implementing_agency",
        recorded=True,
    )


def _evidence(*, quantity: float | None, expenditure: float | None = None, kind: str = "pdf") -> AssembledEvidenceItem:
    return AssembledEvidenceItem(
        evidence_kind=kind,
        document_id=1,
        photo_id=None if kind != "image" else 1,
        evidence_id="ev:document:1:document:REAL:test",
        filename="site.jpg" if kind == "image" else "boq.pdf",
        source="officer_upload",
        data_mode=DataMode.REAL,
        timestamp="2024-06-01T10:00:00+00:00",
        latitude=15.8 if kind == "image" else None,
        longitude=78.0 if kind == "image" else None,
        content_hash="abc123",
        observed_quantity=quantity,
        observed_quantity_unit="sq.ft" if quantity is not None else None,
        observed_expenditure=expenditure,
        notes="photo only" if quantity is None else None,
    )
