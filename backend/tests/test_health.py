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


def test_health_reports_postgresql_connected(client) -> None:
    from unittest.mock import MagicMock, patch
    from sqlalchemy.engine import make_url

    mock_engine = MagicMock()
    mock_engine.dialect.name = "postgresql"
    mock_engine.url = make_url("postgresql+psycopg2://secret_user:super_secret_password@dpg-c1234567-a.oregon-postgres.render.com:5432/sarvsakshi_db")

    with patch("app.api.routes.health.get_engine", return_value=mock_engine), \
         patch("app.api.routes.health.check_connection", return_value=True):
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"]["connected"] is True
    assert body["database"]["dialect"] == "postgresql"
    assert body["database"]["path"] == "dpg-c1234567-a.oregon-postgres.render.com/sarvsakshi_db"
    assert "super_secret_password" not in response.text
    assert "secret_user" not in response.text
    assert "postgresql+psycopg2" not in response.text


def test_health_reports_database_unreachable(client) -> None:
    from unittest.mock import MagicMock, patch

    mock_engine = MagicMock()
    mock_engine.dialect.name = "postgresql"

    with patch("app.api.routes.health.get_engine", return_value=mock_engine), \
         patch("app.api.routes.health.check_connection", side_effect=Exception("Connection refused")):
        response = client.get("/api/v1/health")

    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "database_unavailable"
    assert "PostgreSQL is not reachable" in body["error"]["message"]
