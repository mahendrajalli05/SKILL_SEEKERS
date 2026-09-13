"""End-to-End Lifecycle Orchestration V1 tests. Controlled fixtures only."""

from __future__ import annotations

from app.db import get_session_factory
from app.domain.enums import DataMode, EvidenceDisposition, LifecycleStage
from app.engines.fusion.service import assess_project_risk
from app.engines.fusion_v2.constants import ENGINE_VERSION as FUSION_V2_VERSION
from app.engines.fusion_v2.constants import GROUP_WEIGHTS
from app.engines.fusion_v2.service import assess_project_risk_v2
from app.engines.lifecycle.constants import FROZEN_FUSION_V2_VERSION, FROZEN_FUSION_V2_WEIGHTS
from app.engines.lifecycle.service import get_project_lifecycle, record_planning_decision
from app.engines.lifecycle.state import derive_current_stage, risk_fusion_appropriate
from app.engines.lifecycle.timeline import build_timeline
from app.engines.lifecycle.types import LifecycleFacts
from app.engines.milestone.service import create_milestone
from app.engines.pce.service import record_claim, record_plan
from app.evidence.repository import persist_evidence_object
from app.models.fusion import FusionScore
from app.models.fusion_v2 import FusionScoreV2
from app.review.service import record_officer_decision
from fusion_v2_fixtures import make_group_evidence
from lifecycle_fixtures import SYNTHETIC_LABEL, insert_project
from sqlalchemy import select


def _facts(**overrides: object) -> LifecycleFacts:
    values = dict(
        lifecycle_state=LifecycleStage.FUTURE.value,
        source_status="Unsanctioned",
        planning_state="PLANNING",
        data_mode=DataMode.REAL,
    )
    values.update(overrides)
    return LifecycleFacts(**values)  # type: ignore[arg-type]


def test_fusion_v2_formula_remains_frozen() -> None:
    assert FUSION_V2_VERSION == FROZEN_FUSION_V2_VERSION
    assert GROUP_WEIGHTS == FROZEN_FUSION_V2_WEIGHTS


def test_future_current_stage_is_prioritization() -> None:
    facts = _facts()
    assert derive_current_stage(facts) == "PRIORITIZATION"
    assert risk_fusion_appropriate(facts.lifecycle_state, has_investigation_evidence=False) is False


def test_ongoing_walks_plan_claim_evidence() -> None:
    empty = _facts(lifecycle_state="ONGOING", source_status="Ongoing", risk_appropriate=True)
    assert derive_current_stage(empty) == "PLAN"
    planned = _facts(lifecycle_state="ONGOING", source_status="Ongoing", has_plan=True, risk_appropriate=True)
    assert derive_current_stage(planned) == "CLAIM"
    claimed = _facts(
        lifecycle_state="ONGOING",
        source_status="Ongoing",
        has_plan=True,
        has_claim=True,
        risk_appropriate=True,
    )
    assert derive_current_stage(claimed) == "EVIDENCE"


def test_completed_insufficient_is_inconclusive() -> None:
    facts = _facts(
        lifecycle_state="COMPLETED",
        source_status="Completed",
        completed_insufficient=True,
        risk_appropriate=True,
        risk_insufficient=True,
    )
    assert derive_current_stage(facts) == "FINAL_INVESTIGATION"
    nodes = {item.stage: item.status for item in build_timeline(facts, "FINAL_INVESTIGATION")}
    assert nodes["FINAL_INVESTIGATION"] == "INCONCLUSIVE"
    assert nodes["COMPLETION"] == "COMPLETED"


def test_unknown_lifecycle_marks_timeline_not_available() -> None:
    facts = _facts(lifecycle_state="UNKNOWN", source_status=None)
    current = derive_current_stage(facts)
    assert current == "UNKNOWN"
    nodes = build_timeline(facts, current)
    assert all(item.status in {"NOT AVAILABLE", "CURRENT"} for item in nodes)


def test_future_project_api_and_need_impact(client) -> None:
    session = get_session_factory()()
    try:
        project = insert_project(session, internal_project_id="internal:lifecycle:future")
        session.commit()
        project_id = project.id
    finally:
        session.close()
    body = client.get(f"/api/v2/projects/{project_id}/lifecycle", params={"data_mode": "REAL"}).json()
    assert body["lifecycle_state"] == "FUTURE"
    assert body["source_status"] == "Unsanctioned"
    assert body["workflow_label"] == "SARVSAKSHI workflow state"
    assert body["source_status_label"] == "Source status"
    assert body["current_stage"] == "PRIORITIZATION"
    assert body["automatic_sanction"] is False
    assert body["automatic_payment"] is False
    assert body["fraud_conclusion"] is False
    assert body["need_impact_summary"] is not None
    assert "fraud" not in body["explanation"].casefold() or "not" in body["explanation"].casefold()
    assert "pfms" not in body["explanation"].casefold() or "not" in body["explanation"].casefold()
    assert body["data_mode"] == "REAL"


def test_ongoing_project_uses_risk_and_pce(client) -> None:
    session = get_session_factory()()
    try:
        project = insert_project(
            session,
            internal_project_id="internal:lifecycle:ongoing",
            lifecycle_stage="ONGOING",
            status="Ongoing",
        )
        record_plan(
            session,
            project,
            {"sanctioned_scope": "Community hall 20x10", "budget_estimate": 2_000_000},
            DataMode.REAL,
        )
        record_claim(
            session,
            project,
            {"claimed_progress": "Foundation complete", "claimed_progress_percent": 40},
            DataMode.REAL,
        )
        persist_evidence_object(
            session,
            make_group_evidence("cost", project_id=project.id, score=40, data_mode=DataMode.REAL),
        )
        session.commit()
        project_id = project.id
        first = get_project_lifecycle(session, project, DataMode.REAL)
        second = get_project_lifecycle(session, project, DataMode.REAL)
    finally:
        session.close()
    assert first.current_stage == second.current_stage
    assert first.lifecycle_state == "ONGOING"
    assert first.pce_summary is not None
    assert first.pce_summary["plan_recorded"] is True
    assert first.pce_summary["claim_recorded"] is True
    assert first.risk_summary is not None
    assert first.risk_summary["appropriate"] is True
    assert first.risk_summary["formula_unchanged"] is True
    assert first.pce_summary["completion_date"] is None
    assert first.pce_summary["expenditure"] is None
    body = client.get(f"/api/v2/projects/{project_id}/lifecycle", params={"data_mode": "REAL"}).json()
    assert body["lifecycle_state"] == "ONGOING"
    assert any(item["stage"] == "PLAN" for item in body["timeline"])


def test_completed_inconclusive_without_evidence(client) -> None:
    session = get_session_factory()()
    try:
        project = insert_project(
            session,
            internal_project_id="internal:lifecycle:completed",
            lifecycle_stage="COMPLETED",
            status="Completed",
        )
        session.commit()
        project_id = project.id
    finally:
        session.close()
    body = client.get(f"/api/v2/projects/{project_id}/lifecycle", params={"data_mode": "REAL"}).json()
    assert body["lifecycle_state"] == "COMPLETED"
    assert body["final_case_summary"]["result"] == "INCONCLUSIVE"
    assert body["final_case_summary"]["completion_date"] is None
    assert body["final_case_summary"]["expenditure"] is None
    assert body["recommendation"] == "INCONCLUSIVE"
    assert body["satellite_status"]["status"] == "SATELLITE_UNAVAILABLE"


def test_unknown_lifecycle(client) -> None:
    session = get_session_factory()()
    try:
        project = insert_project(
            session,
            internal_project_id="internal:lifecycle:unknown",
            lifecycle_stage="UNKNOWN",
            status=None,
        )
        session.commit()
        project_id = project.id
    finally:
        session.close()
    body = client.get(f"/api/v2/projects/{project_id}/lifecycle").json()
    assert body["lifecycle_state"] == "UNKNOWN"
    assert body["current_stage"] == "UNKNOWN"


def test_planning_transition_does_not_change_scores(client) -> None:
    session = get_session_factory()()
    try:
        project = insert_project(session, internal_project_id="internal:lifecycle:plan-decision")
        persist_evidence_object(
            session,
            make_group_evidence("cost", project_id=project.id, score=80, disposition=EvidenceDisposition.WHY_FLAGGED),
        )
        session.commit()
        project_id = project.id
        assess_project_risk(session, project_id, data_mode=DataMode.REAL, persist=True)
        assess_project_risk_v2(session, project_id, data_mode=DataMode.REAL, persist=True)
        v1_before = session.scalars(select(FusionScore).where(FusionScore.project_id == project_id)).first()
        v2_before = session.scalars(select(FusionScoreV2).where(FusionScoreV2.project_id == project_id)).first()
        assert v1_before is not None and v2_before is not None
        snap = (
            v1_before.investigation_priority,
            v1_before.evidence_confidence,
            v2_before.investigation_priority,
            v2_before.evidence_confidence,
        )
        record_planning_decision(
            session,
            project,
            action="PRIORITIZE",
            reason="High need in constituency. Not a sanction.",
            actor_role="officer",
            data_mode=DataMode.REAL,
        )
        session.commit()
        v1_after = session.scalars(select(FusionScore).where(FusionScore.project_id == project_id)).first()
        v2_after = session.scalars(select(FusionScoreV2).where(FusionScoreV2.project_id == project_id)).first()
        assert (
            v1_after.investigation_priority,
            v1_after.evidence_confidence,
            v2_after.investigation_priority,
            v2_after.evidence_confidence,
        ) == snap
        result = get_project_lifecycle(session, project, DataMode.REAL)
        assert result.planning_state == "PRIORITIZED"
        assert project.lifecycle_stage == "FUTURE"
    finally:
        session.close()

    posted = client.post(
        f"/api/v2/projects/{project_id}/lifecycle/decision",
        params={"data_mode": "REAL"},
        json={"action": "DEFER", "reason": "Budget not available this year."},
    )
    assert posted.status_code == 200
    assert posted.json()["resulting_state"] == "DEFERRED"
    assert posted.json()["automatic_sanction"] is False
    later = client.get(f"/api/v2/projects/{project_id}/lifecycle", params={"data_mode": "REAL"}).json()
    assert later["planning_state"] == "DEFERRED"


def test_hybrid_and_synthetic_data_mode(client) -> None:
    session = get_session_factory()()
    try:
        hybrid = insert_project(session, internal_project_id="internal:lifecycle:hybrid")
        synthetic = insert_project(
            session,
            internal_project_id="internal:lifecycle:synthetic",
            is_synthetic=True,
            synthetic_label=SYNTHETIC_LABEL,
        )
        session.commit()
        hid, sid = hybrid.id, synthetic.id
    finally:
        session.close()
    hybrid_body = client.get(f"/api/v2/projects/{hid}/lifecycle", params={"data_mode": "HYBRID"}).json()
    assert hybrid_body["data_mode"] == "HYBRID"
    assert "HYBRID" in hybrid_body["explanation"]
    syn_body = client.get(f"/api/v2/projects/{sid}/lifecycle", params={"data_mode": "REAL"}).json()
    assert syn_body["data_mode"] == "SYNTHETIC"
    assert syn_body["is_synthetic"] is True
    assert "SYNTHETIC" in (syn_body["synthetic_label"] or syn_body["explanation"])


def test_milestone_and_officer_decision_summaries(client) -> None:
    session = get_session_factory()()
    try:
        project = insert_project(
            session,
            internal_project_id="internal:lifecycle:milestone",
            lifecycle_stage="ONGOING",
            status="Ongoing",
        )
        record_plan(session, project, {"sanctioned_scope": "Hall", "budget_estimate": 1_000_000}, DataMode.REAL)
        record_claim(session, project, {"claimed_progress": "Started", "claimed_progress_percent": 10}, DataMode.REAL)
        persist_evidence_object(
            session,
            make_group_evidence("cost", project_id=project.id, score=20, data_mode=DataMode.REAL),
        )
        create_milestone(
            session,
            project,
            {"milestone_number": 1, "milestone_name": "Foundation", "planned_amount": 400_000},
            DataMode.REAL,
        )
        session.commit()
        project_id = project.id
        result = get_project_lifecycle(session, project, DataMode.REAL)
        assert result.milestone_summary is not None
        assert result.milestone_summary["count"] == 1
        assert result.current_stage == "MILESTONE"
        record_officer_decision(
            session,
            project,
            decision_type="need_more_info",
            reason="Inspector should verify progress photographs.",
            actor_role="officer",
        )
        session.commit()
        after = get_project_lifecycle(session, project, DataMode.REAL)
        assert any(item["kind"] == "investigation" for item in after.officer_decisions)
    finally:
        session.close()
    listed = client.get(f"/api/v2/projects/{project_id}/lifecycle").json()
    assert listed["document_status"] is None or listed["document_status"]["available"] in {True, False}
    assert listed["image_status"] is None
    assert listed["citizen_summary"] is None or listed["citizen_summary"]["available"] is False
    assert listed["geospatial_status"] is None or listed["geospatial_status"]["available"] is False


def test_planning_rejected_for_ongoing(client) -> None:
    session = get_session_factory()()
    try:
        project = insert_project(
            session,
            internal_project_id="internal:lifecycle:no-plan",
            lifecycle_stage="ONGOING",
            status="Ongoing",
        )
        session.commit()
        project_id = project.id
    finally:
        session.close()
    response = client.post(
        f"/api/v2/projects/{project_id}/lifecycle/decision",
        json={"action": "PRIORITIZE", "reason": "Should not apply"},
    )
    assert response.status_code == 422


def test_v1_risk_still_available(client) -> None:
    session = get_session_factory()()
    try:
        project = insert_project(session, internal_project_id="internal:lifecycle:v1compat")
        session.commit()
        project_id = project.id
    finally:
        session.close()
    v1 = client.get(f"/api/v1/projects/{project_id}/risk", params={"data_mode": "REAL"})
    v2 = client.get(f"/api/v2/projects/{project_id}/risk", params={"data_mode": "REAL"})
    life = client.get(f"/api/v2/projects/{project_id}/lifecycle", params={"data_mode": "REAL"})
    assert v1.status_code == 200
    assert v2.status_code == 200
    assert life.status_code == 200
    assert v1.json()["engine_version"] == "risk-fusion-v1.1"
    assert v2.json()["engine_version"] == "risk-fusion-v2"
    assert life.json()["engine_version"] == "lifecycle-orchestration-v1"


def test_missing_project(client) -> None:
    response = client.get("/api/v2/projects/999999/lifecycle")
    assert response.status_code == 404
