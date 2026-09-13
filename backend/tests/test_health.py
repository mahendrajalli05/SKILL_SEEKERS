from __future__ import annotations


def test_health_reports_sqlite_connected(client) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"]["connected"] is True
    assert body["database"]["dialect"] == "sqlite"
    assert "project" in body["database"]["tables"]
    assert body["llm_enabled"] is False


def test_health_governance_does_not_offer_fraud_probability(client) -> None:
    body = client.get("/api/v1/health").json()
    outputs = body["governance"]["outputs"]
    excluded = body["governance"]["does_not_output"]
    assert "investigation_priority" in outputs
    assert "evidence_confidence" in outputs
    assert "legal_fraud_probability" in excluded
    assert "legal_fraud_finding" in excluded
