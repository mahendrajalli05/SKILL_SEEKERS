from __future__ import annotations

from app.copilot.intent import parse_intent
from app.copilot.types import CopilotIntent
from app.db import get_session_factory
from app.domain.enums import DataMode, EvidenceDisposition
from app.domain.schemas.evidence import EvidenceFact
from app.engines.fusion.service import assess_project_risk
from app.engines.fusion_v2.service import assess_project_risk_v2
from app.evidence.repository import persist_evidence_object
from copilot_fixtures import insert_project
from fusion_v2_fixtures import make_group_evidence


def test_v2_copilot_intents() -> None:
    assert parse_intent("Which evidence contributed most?") == CopilotIntent.RISK_V2_CONTRIBUTION
    assert parse_intent("Which evidence was discounted as correlated?") == CopilotIntent.RISK_V2_CORRELATED
    assert parse_intent("What evidence is conflicting?") == CopilotIntent.RISK_V2_CONFLICTING
    assert parse_intent("Why is the new score higher?") == CopilotIntent.RISK_V2_SCORE_CHANGE


def test_copilot_explains_v2_contribution_and_correlation(client) -> None:
    session = get_session_factory()()
    try:
        project = insert_project(session, internal_project_id="internal:synthetic:copilot:v2")
        persist_evidence_object(
            session,
            make_group_evidence(
                "overlap",
                project_id=project.id,
                score=90,
                disposition=EvidenceDisposition.WHY_FLAGGED,
                data_mode=DataMode.SYNTHETIC,
            ),
        )
        persist_evidence_object(
            session,
            make_group_evidence(
                "graph",
                project_id=project.id,
                score=95,
                disposition=EvidenceDisposition.WHY_FLAGGED,
                data_mode=DataMode.SYNTHETIC,
                extra_facts=[
                    EvidenceFact(key="strongest_relationship", value="SIMILAR_TO", source="relationship-graph-v1"),
                    EvidenceFact(key="similar_project_count", value=2, source="relationship-graph-v1"),
                ],
            ),
        )
        session.commit()
        project_id = project.id
        assess_project_risk(session, project_id, data_mode=DataMode.SYNTHETIC, persist=True)
        assess_project_risk_v2(session, project_id, data_mode=DataMode.SYNTHETIC, persist=True)
    finally:
        session.close()

    contrib = client.post(
        f"/api/v1/projects/{project_id}/copilot/chat",
        json={"question": "Which evidence contributed most?", "data_mode": "SYNTHETIC"},
    ).json()
    assert contrib["intent"] == "RISK_V2_CONTRIBUTION"
    assert "contributed most" in contrib["answer"].lower()
    assert "fraud probability" not in contrib["answer"].lower() or "not a fraud" in contrib["answer"].lower()

    correlated = client.post(
        f"/api/v1/projects/{project_id}/copilot/chat",
        json={"question": "Which evidence was discounted as correlated?", "data_mode": "SYNTHETIC"},
    ).json()
    assert correlated["intent"] == "RISK_V2_CORRELATED"
    assert "correlated" in correlated["answer"].lower() or "discount" in correlated["answer"].lower() or "independent" in correlated["answer"].lower()

    higher = client.post(
        f"/api/v1/projects/{project_id}/copilot/chat",
        json={"question": "Why is the new score higher?", "data_mode": "SYNTHETIC"},
    ).json()
    assert higher["intent"] == "RISK_V2_SCORE_CHANGE"
    assert "v2" in higher["answer"].lower()
    assert "fraud" not in higher["answer"].lower() or "not a fraud" in higher["answer"].lower()
