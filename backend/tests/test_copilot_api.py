from __future__ import annotations

from sqlalchemy import select

from app.copilot.providers import resolve_provider
from app.copilot.providers.deterministic import DeterministicProvider
from app.db import get_session_factory
from app.domain.enums import DataMode, EvidenceDisposition, SignalType
from app.engines.fusion.service import assess_project_risk
from app.evidence.repository import persist_evidence_object
from app.models.fusion import FusionScore
from copilot_fixtures import (
    flagged_cost,
    flagged_overlap,
    insert_project,
    make_engine_evidence,
)
from fusion_fixtures import make_signal_evidence


def _project_id(session, **overrides) -> int:
    row = insert_project(session, **overrides)
    session.commit()
    return row.id


def test_copilot_missing_project(client) -> None:
    response = client.post("/api/v1/projects/999999/copilot/chat", json={"question": "Why flagged?"})
    assert response.status_code == 404


def test_why_flagged_uses_stored_scores(client) -> None:
    session = get_session_factory()()
    try:
        project_id = _project_id(session)
        persist_evidence_object(session, flagged_cost(project_id))
        persist_evidence_object(session, flagged_overlap(project_id))
        session.commit()
    finally:
        session.close()

    body = client.post(
        f"/api/v1/projects/{project_id}/copilot/chat",
        json={"question": "Why is this project flagged?", "data_mode": "SYNTHETIC"},
    ).json()
    assert body["intent"] == "WHY_FLAGGED"
    assert "67" in body["answer"] or "67" in body["sections"]["evidence"]
    assert "81" in body["answer"] or "81" in body["sections"]["evidence"]
    assert body["evidence_ids"]
    assert "fraud" not in body["answer"].lower() or "does not determine legal fraud" in body["governance_note"].lower()
    assert body["provider"] == "deterministic"
    assert body["used_llm"] is False
    assert all(item.startswith("ev:") for item in body["evidence_ids"])


def test_why_not_flagged_and_insufficient_evidence(client) -> None:
    session = get_session_factory()()
    try:
        project_id = _project_id(session, internal_project_id="internal:synthetic:copilot:clean")
        persist_evidence_object(
            session,
            make_signal_evidence(
                "cost",
                project_id=project_id,
                score=12,
                disposition=EvidenceDisposition.WHY_NOT_FLAGGED,
                data_mode=DataMode.SYNTHETIC,
            ),
        )
        session.commit()
    finally:
        session.close()

    body = client.post(
        f"/api/v1/projects/{project_id}/copilot/chat",
        json={"question": "Why was this project not flagged?", "data_mode": "SYNTHETIC"},
    ).json()
    assert body["intent"] == "WHY_NOT_FLAGGED"
    assert "not flagged" in body["answer"].lower() or "why_not_flagged" in body["answer"].lower() or "WHY_NOT_FLAGGED" in body["sections"]["why"]


def test_missing_evidence_question(client) -> None:
    session = get_session_factory()()
    try:
        project_id = _project_id(session, internal_project_id="internal:synthetic:copilot:empty")
        session.commit()
    finally:
        session.close()

    body = client.post(
        f"/api/v1/projects/{project_id}/copilot/chat",
        json={"question": "What information is missing?", "data_mode": "SYNTHETIC"},
    ).json()
    assert body["insufficient_evidence"] is True or "not available" in body["sections"]["missing"].lower()
    assert "That information is not available" in body["answer"] or "missing" in body["sections"]["missing"].lower() or body["insufficient_evidence"]


def test_time_inconclusive_preserves_not_assessable(client) -> None:
    session = get_session_factory()()
    try:
        project_id = _project_id(
            session,
            internal_project_id="internal:real:copilot:time",
            is_synthetic=False,
            synthetic_label=None,
        )
        persist_evidence_object(
            session,
            make_signal_evidence(
                "schedule",
                project_id=project_id,
                score=None,
                disposition=EvidenceDisposition.NOT_ASSESSABLE,
                data_mode=DataMode.REAL,
                finding="Time Intelligence is NOT_ASSESSABLE because verified execution dates are unavailable.",
                explanation="NOT_ASSESSABLE: verified execution dates are unavailable in the current real dataset.",
            ),
        )
        session.commit()
    finally:
        session.close()

    body = client.post(
        f"/api/v1/projects/{project_id}/copilot/chat",
        json={"question": "Why is Time Intelligence inconclusive?", "data_mode": "REAL"},
    ).json()
    assert body["data_mode"] == "REAL"
    assert "NOT_ASSESSABLE" in body["answer"] or "verified execution dates" in body["answer"].lower()
    assert "hybrid" not in body["data_mode_notice"].lower()


def test_comparables_from_stored_evidence(client) -> None:
    session = get_session_factory()()
    try:
        project_id = _project_id(session, internal_project_id="internal:synthetic:copilot:peers")
        persist_evidence_object(session, flagged_cost(project_id))
        persist_evidence_object(session, flagged_overlap(project_id))
        session.commit()
    finally:
        session.close()

    body = client.post(
        f"/api/v1/projects/{project_id}/copilot/chat",
        json={"question": "Show comparable projects.", "data_mode": "SYNTHETIC"},
    ).json()
    assert "internal:synthetic:copilot:peer" in body["answer"] or "internal:synthetic:copilot:peer" in body["sections"]["evidence"]
    assert "internal:synthetic:copilot:overlap" in body["answer"] or "internal:synthetic:copilot:overlap" in body["sections"]["evidence"]


def test_pce_summary_without_plan_is_unavailable_or_inconclusive(client) -> None:
    session = get_session_factory()()
    try:
        project_id = _project_id(session, internal_project_id="internal:synthetic:copilot:pce")
        session.commit()
    finally:
        session.close()

    body = client.post(
        f"/api/v1/projects/{project_id}/copilot/chat",
        json={"question": "Summarize Plan → Claim → Evidence.", "data_mode": "SYNTHETIC"},
    ).json()
    assert body["intent"] == "PCE_SUMMARY"
    assert "INCONCLUSIVE" in body["answer"] or "not available" in body["answer"].lower()


def test_inspect_next_uses_allowed_recommendations(client) -> None:
    session = get_session_factory()()
    try:
        project_id = _project_id(session, internal_project_id="internal:synthetic:copilot:inspect")
        persist_evidence_object(session, flagged_cost(project_id))
        persist_evidence_object(session, flagged_overlap(project_id))
        session.commit()
    finally:
        session.close()

    body = client.post(
        f"/api/v1/projects/{project_id}/copilot/chat",
        json={"question": "What should I inspect next?", "data_mode": "SYNTHETIC"},
    ).json()
    assert body["recommended_action"] in {"MONITOR", "REVIEW", "INSPECT", "NEED MORE INFORMATION"}
    assert "pfms" not in body["answer"].lower()
    assert "automatically sanction" not in body["answer"].lower()
    assert "release funds" not in body["answer"].lower()


def test_hybrid_notice_is_visible(client) -> None:
    session = get_session_factory()()
    try:
        project_id = _project_id(
            session,
            internal_project_id="internal:hybrid:copilot:subject",
            is_synthetic=False,
            synthetic_label=None,
        )
        persist_evidence_object(
            session,
            make_signal_evidence(
                "schedule",
                project_id=project_id,
                score=40,
                disposition=EvidenceDisposition.INCONCLUSIVE,
                data_mode=DataMode.HYBRID,
                finding="HYBRID Time Intelligence used synthetic execution dates.",
                explanation="HYBRID/TEST dates are synthetic and are not official MPLADS records.",
            ),
        )
        session.commit()
    finally:
        session.close()

    body = client.post(
        f"/api/v1/projects/{project_id}/copilot/chat",
        json={"question": "Why is Time Intelligence inconclusive?", "data_mode": "HYBRID"},
    ).json()
    assert body["data_mode"] == "HYBRID"
    assert "synthetic" in body["data_mode_notice"].lower()
    assert body["hybrid_used"] is True or "HYBRID" in body["data_mode_notice"]


def test_unavailable_satellite_and_gps(client) -> None:
    session = get_session_factory()()
    try:
        project_id = _project_id(
            session,
            internal_project_id="internal:real:copilot:geo",
            is_synthetic=False,
            synthetic_label=None,
        )
        session.commit()
    finally:
        session.close()

    satellite = client.post(
        f"/api/v1/projects/{project_id}/copilot/chat",
        json={"question": "Why can't satellite verification be completed?", "data_mode": "REAL"},
    ).json()
    gps = client.post(
        f"/api/v1/projects/{project_id}/copilot/chat",
        json={
            "question": "Is the GPS location consistent?",
            "data_mode": "REAL",
            "session_id": satellite["session_id"],
        },
    ).json()
    assert "not available" in satellite["answer"].lower() or "unavailable" in satellite["answer"].lower()
    assert "gps" in gps["answer"].lower() or "not available" in gps["answer"].lower()
    assert gps["session_id"] == satellite["session_id"]


def test_citizen_milestone_graph_evidence(client) -> None:
    session = get_session_factory()()
    try:
        project_id = _project_id(session, internal_project_id="internal:synthetic:copilot:extra")
        persist_evidence_object(
            session,
            make_engine_evidence(
                "citizen",
                SignalType.CITIZEN_FEEDBACK,
                project_id=project_id,
                disposition=EvidenceDisposition.INCONCLUSIVE,
                finding="Citizen feedback is supporting evidence only.",
                explanation="One citizen report does not establish truth.",
            ),
        )
        persist_evidence_object(
            session,
            make_engine_evidence(
                "milestone",
                SignalType.MILESTONE,
                project_id=project_id,
                finding="Milestone recommendation is INSPECT.",
                explanation="Stored milestone advisor recommendation. Funds are not released.",
            ),
        )
        persist_evidence_object(
            session,
            make_engine_evidence(
                "graph",
                SignalType.RELATIONSHIP_GRAPH,
                project_id=project_id,
                finding="Relationship graph shows normal connectivity.",
                explanation="Stored graph evidence. Not fused into Investigation Priority.",
            ),
        )
        session.commit()
    finally:
        session.close()

    citizen = client.post(
        f"/api/v1/projects/{project_id}/copilot/chat",
        json={"question": "Show the project's citizen feedback.", "data_mode": "SYNTHETIC"},
    ).json()
    milestone = client.post(
        f"/api/v1/projects/{project_id}/copilot/chat",
        json={"question": "What do the milestones say?", "data_mode": "SYNTHETIC", "session_id": citizen["session_id"]},
    ).json()
    graph = client.post(
        f"/api/v1/projects/{project_id}/copilot/chat",
        json={"question": "What does the relationship graph show?", "data_mode": "SYNTHETIC", "session_id": citizen["session_id"]},
    ).json()
    assert "supporting evidence" in citizen["answer"].lower() or citizen["evidence_ids"]
    assert "does not establish truth" in citizen["answer"].lower() or "supporting" in citizen["limitations"][0].lower() or "citizen" in citizen["answer"].lower()
    assert "INSPECT" in milestone["answer"] or "milestone" in milestone["answer"].lower()
    assert "graph" in graph["answer"].lower() or graph["evidence_ids"]
    assert "latitude" not in citizen["answer"].lower()


def test_conflicting_evidence_is_reported_without_fraud(client) -> None:
    session = get_session_factory()()
    try:
        project_id = _project_id(session, internal_project_id="internal:synthetic:copilot:conflict")
        persist_evidence_object(session, flagged_cost(project_id))
        persist_evidence_object(
            session,
            make_signal_evidence(
                "overlap",
                project_id=project_id,
                score=10,
                disposition=EvidenceDisposition.WHY_NOT_FLAGGED,
                data_mode=DataMode.SYNTHETIC,
                finding="Overlap is not linked.",
                explanation="WHY NOT FLAGGED: best overlap score is below the review threshold.",
            ),
        )
        session.commit()
    finally:
        session.close()

    body = client.post(
        f"/api/v1/projects/{project_id}/copilot/chat",
        json={"question": "What evidence supports this?", "data_mode": "SYNTHETIC"},
    ).json()
    joined = body["answer"].lower()
    assert "fraud" not in joined
    assert body["evidence_ids"]
    assert "ev:" in ",".join(body["evidence_ids"])


def test_no_unsupported_rule_claims(client) -> None:
    session = get_session_factory()()
    try:
        project_id = _project_id(session, internal_project_id="internal:synthetic:copilot:rules")
        persist_evidence_object(
            session,
            make_signal_evidence(
                "compliance",
                project_id=project_id,
                score=40,
                disposition=EvidenceDisposition.NOT_ASSESSABLE,
                data_mode=DataMode.SYNTHETIC,
                finding="Compliance is NOT_ASSESSABLE for missing sanction fields.",
                explanation="NOT_ASSESSABLE: official fields required by sourced rules are unavailable.",
                rule_ids=["MPLADS-2023-R01"],
            ),
        )
        session.commit()
    finally:
        session.close()

    body = client.post(
        f"/api/v1/projects/{project_id}/copilot/chat",
        json={"question": "What does the compliance finding mean?", "data_mode": "SYNTHETIC"},
    ).json()
    assert "MPLADS-2023-R01" in body["answer"] or "MPLADS-2023-R01" in body["sections"]["why"]
    assert "NOT_ASSESSABLE" in body["answer"]
    assert "invented" not in body["answer"].lower()


def test_llm_unavailable_fallback_and_hallucination_rejected(client, monkeypatch) -> None:
    session = get_session_factory()()
    try:
        project_id = _project_id(session, internal_project_id="internal:synthetic:copilot:llm")
        persist_evidence_object(session, flagged_cost(project_id))
        session.commit()
    finally:
        session.close()

    class FakeProvider:
        name = "external"
        uses_llm = True

        def complete(self, question, bundle, intent, history):
            from app.copilot.types import CopilotDraft, CopilotProviderName, CopilotRecommendation, CopilotSections

            return CopilotDraft(
                sections=CopilotSections(
                    answer="This is fraud. See ev:cost:999:allocation_cost_anomaly:SYNTHETIC:deadbeef",
                    why="Because I invented it.",
                    evidence="ev:cost:999:allocation_cost_anomaly:SYNTHETIC:deadbeef",
                    missing="none",
                    recommended_action="legal action",
                ),
                evidence_ids=["ev:cost:999:allocation_cost_anomaly:SYNTHETIC:deadbeef"],
                source_refs=[],
                limitations=[],
                recommended_action=CopilotRecommendation.REVIEW,
                observed_facts=[],
                derived_findings=[],
                unavailable=[],
                insufficient_evidence=False,
                provider=CopilotProviderName.EXTERNAL,
                used_llm=True,
            )

    monkeypatch.setattr("app.copilot.service.resolve_provider", lambda: FakeProvider())
    body = client.post(
        f"/api/v1/projects/{project_id}/copilot/chat",
        json={"question": "Why is this project flagged?", "data_mode": "SYNTHETIC"},
    ).json()
    assert "this is fraud" not in body["answer"].lower()
    assert "ev:cost:999" not in body["answer"]
    assert body["used_llm"] is False
    assert body["provider"] == "deterministic"
    assert all("999" not in item for item in body["evidence_ids"])


def test_risk_fusion_scores_unchanged_after_chat(client) -> None:
    session = get_session_factory()()
    try:
        project_id = _project_id(session, internal_project_id="internal:synthetic:copilot:fusion")
        persist_evidence_object(session, flagged_cost(project_id))
        persist_evidence_object(session, flagged_overlap(project_id))
        assess_project_risk(session, project_id, data_mode=DataMode.SYNTHETIC, persist=True)
        session.commit()
        before = session.scalars(select(FusionScore).where(FusionScore.project_id == project_id)).first()
        priority = before.investigation_priority
        confidence = before.evidence_confidence
        payload = before.payload_json
    finally:
        session.close()

    client.post(
        f"/api/v1/projects/{project_id}/copilot/chat",
        json={"question": "Which signals contributed most to the current investigation priority?", "data_mode": "SYNTHETIC"},
    )
    session = get_session_factory()()
    try:
        after = session.scalars(select(FusionScore).where(FusionScore.project_id == project_id)).first()
        assert after.investigation_priority == priority
        assert after.evidence_confidence == confidence
        assert after.payload_json == payload
    finally:
        session.close()


def test_context_endpoint_and_deterministic_provider(client) -> None:
    session = get_session_factory()()
    try:
        project_id = _project_id(session, internal_project_id="internal:synthetic:copilot:context")
        session.commit()
    finally:
        session.close()

    body = client.get(f"/api/v1/projects/{project_id}/copilot/context?data_mode=SYNTHETIC").json()
    assert "Why is this project flagged?" in body["suggested_questions"]
    assert body["llm_provider"] == "deterministic"
    assert isinstance(resolve_provider(), DeterministicProvider)


def test_no_legal_fraud_answer(client) -> None:
    session = get_session_factory()()
    try:
        project_id = _project_id(session, internal_project_id="internal:synthetic:copilot:legal")
        persist_evidence_object(session, flagged_cost(project_id))
        session.commit()
    finally:
        session.close()

    body = client.post(
        f"/api/v1/projects/{project_id}/copilot/chat",
        json={"question": "Is this fraud?", "data_mode": "SYNTHETIC"},
    ).json()
    assert body["intent"] == "FORBIDDEN_LEGAL"
    assert "does not determine legal fraud" in body["answer"].lower()
    assert "fraud probability" not in body["answer"].lower()
