from __future__ import annotations

from app.copilot.intent import parse_intent
from app.copilot.types import CopilotIntent
from app.db import get_session_factory
from app.domain.enums import DataMode, EvidenceDisposition, EvidenceFactKind, SignalType
from app.domain.schemas.evidence import EvidenceFact
from app.evidence.repository import persist_evidence_object
from copilot_fixtures import insert_project, make_engine_evidence


def test_ml_intents() -> None:
    assert parse_intent("What ML signal exists for this project?") == CopilotIntent.ML_EVIDENCE
    assert parse_intent("Which model generated this score?") == CopilotIntent.ML_EVIDENCE
    assert parse_intent("Why was the ML anomaly score elevated?") == CopilotIntent.ML_EVIDENCE
    assert parse_intent("Is this a fraud probability?") == CopilotIntent.ML_FRAUD_CLARIFICATION
    assert parse_intent("Is the ML anomaly score a wrongdoing probability?") == CopilotIntent.ML_FRAUD_CLARIFICATION
    assert parse_intent("Did the model confirm misconduct?") == CopilotIntent.ML_FRAUD_CLARIFICATION
    assert parse_intent("Does this ML score mean legal wrongdoing?") == CopilotIntent.ML_FRAUD_CLARIFICATION
    assert parse_intent("Is this fraud?") == CopilotIntent.FORBIDDEN_LEGAL


def _ml_evidence(project_id: int):
    return make_engine_evidence(
        "ml",
        SignalType.ML_ANOMALY_SIGNAL,
        project_id=project_id,
        data_mode=DataMode.SYNTHETIC,
        disposition=EvidenceDisposition.WHY_FLAGGED,
        score=91,
        finding="ELEVATED_ANOMALY_SIGNAL: unsupervised Isolation Forest placed this work in the upper tail.",
        explanation="Allocation is unusual relative to the training distribution for comparable observed records.",
        extra_facts=[
            EvidenceFact(
                key="model_name",
                value="cost-anomaly-v1",
                source="cost-anomaly-v1-test",
                kind=EvidenceFactKind.DERIVED,
            ),
            EvidenceFact(
                key="model_version",
                value="cost-anomaly-v1-9d0c62e3b384",
                source="cost-anomaly-v1-test",
                kind=EvidenceFactKind.DERIVED,
            ),
            EvidenceFact(
                key="ml_anomaly_score",
                value=91,
                source="cost-anomaly-v1-test",
                kind=EvidenceFactKind.DERIVED,
            ),
            EvidenceFact(
                key="feature_schema_version",
                value="cost-features-v1",
                source="cost-anomaly-v1-test",
                kind=EvidenceFactKind.DERIVED,
            ),
        ],
    )


def test_copilot_retrieves_ml_evidence(client) -> None:
    session = get_session_factory()()
    try:
        project = insert_project(session, internal_project_id="internal:synthetic:copilot:ml")
        persist_evidence_object(session, _ml_evidence(project.id))
        session.commit()
        project_id = project.id
    finally:
        session.close()

    signal = client.post(
        f"/api/v1/projects/{project_id}/copilot/chat",
        json={"question": "What ML signal exists for this project?", "data_mode": "SYNTHETIC"},
    )
    assert signal.status_code == 200, signal.text
    body = signal.json()
    assert body["intent"] == "ML_EVIDENCE"
    assert "91" in body["answer"] or "91" in body["sections"]["evidence"]
    assert "cost-anomaly-v1" in body["answer"] or "cost-anomaly-v1" in body["sections"]["why"]
    assert body["evidence_ids"]
    assert all(item.startswith("ev:") for item in body["evidence_ids"])
    lowered = body["answer"].lower()
    assert "the ml anomaly score is not a fraud probability" in lowered
    assert "does not determine legal fraud" in lowered or "not a legal finding" in lowered
    assert "fraud confirmed" not in lowered
    assert "this is confirmed misconduct" not in lowered
    assert "legal guilt" not in lowered
    assert "because the model detected" not in lowered
    assert "this is fraud" not in lowered

    version = client.post(
        f"/api/v1/projects/{project_id}/copilot/chat",
        json={"question": "Which model generated this score?", "data_mode": "SYNTHETIC"},
    ).json()
    assert version["intent"] == "ML_EVIDENCE"
    assert "cost-anomaly-v1-9d0c62e3b384" in version["answer"] or "cost-anomaly-v1-9d0c62e3b384" in version["sections"]["evidence"]

    elevated = client.post(
        f"/api/v1/projects/{project_id}/copilot/chat",
        json={"question": "Why was the ML anomaly score elevated?", "data_mode": "SYNTHETIC"},
    ).json()
    assert "training distribution" in elevated["sections"]["why"].lower() or "training distribution" in elevated["answer"].lower()
    assert "fraudulent because" not in elevated["answer"].lower()

    fraud = client.post(
        f"/api/v1/projects/{project_id}/copilot/chat",
        json={"question": "Is this a fraud probability?", "data_mode": "SYNTHETIC"},
    )
    assert fraud.status_code == 200, fraud.text
    payload = fraud.json()
    assert payload["intent"] == "ML_FRAUD_CLARIFICATION"
    assert "the ml anomaly score is not a fraud probability" in payload["answer"].lower()
    assert "does not determine legal fraud" in payload["answer"].lower()
    assert "wrongdoing probability" in payload["answer"].lower()
    assert "legal conclusion" in payload["answer"].lower()
    assert "confirmed misconduct" in payload["answer"].lower()
    assert payload["recommended_action"] in {"MONITOR", "REVIEW", "INSPECT", "NEED MORE INFORMATION"}
    why = payload["sections"]["why"].lower()
    assert "unusualness" in why or "training distribution" in why
    assert "does not become fraud" in why or "not a fraud probability" in payload["answer"].lower()

    legal = client.post(
        f"/api/v1/projects/{project_id}/copilot/chat",
        json={"question": "Does this ML score mean legal wrongdoing?", "data_mode": "SYNTHETIC"},
    )
    assert legal.status_code == 200, legal.text
    legal_body = legal.json()
    assert legal_body["intent"] == "ML_FRAUD_CLARIFICATION"
    assert "the ml anomaly score is not a fraud probability" in legal_body["answer"].lower()
    assert "cannot determine fraud or legal wrongdoing" in legal_body["answer"].lower()
    assert "guilty" not in legal_body["answer"].lower()
    assert "this project is fraudulent" not in legal_body["answer"].lower()
    assert "this is confirmed misconduct" not in legal_body["answer"].lower()

    misconduct = client.post(
        f"/api/v1/projects/{project_id}/copilot/chat",
        json={"question": "Did the model confirm misconduct?", "data_mode": "SYNTHETIC"},
    )
    assert misconduct.status_code == 200, misconduct.text
    misconduct_body = misconduct.json()
    assert misconduct_body["intent"] == "ML_FRAUD_CLARIFICATION"
    assert "the ml anomaly score is not a fraud probability" in misconduct_body["answer"].lower()
    assert "not" in misconduct_body["answer"].lower() and "confirmed misconduct" in misconduct_body["answer"].lower()
