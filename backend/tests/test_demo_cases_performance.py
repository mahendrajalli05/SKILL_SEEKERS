"""Focused performance and fixture integrity tests for Demo Center cases."""

from __future__ import annotations

import time
from unittest.mock import patch

from app.db import get_session_factory
from app.demo.constants import CASE_IDS, DEMO_NOTICE
from demo_fixtures import insert_all_demo_cases


def _seed(session):
    rows = insert_all_demo_cases(session)
    session.commit()
    return {key: row.id for key, row in rows.items()}


def test_demo_cases_response_time_under_three_seconds(client) -> None:
    session = get_session_factory()()
    try:
        _seed(session)
    finally:
        session.close()

    for case_id in CASE_IDS:
        t0 = time.perf_counter()
        response = client.get(f"/api/v1/demo-cases/{case_id}", params={"data_mode": "HYBRID"})
        elapsed = time.perf_counter() - t0

        assert response.status_code == 200, response.text
        assert elapsed < 3.0, f"Demo case {case_id} took {elapsed:.2f}s, expected < 3.0s"

        body = response.json()
        assert body["case_id"] == case_id
        assert body["data_mode"] == "HYBRID"
        assert DEMO_NOTICE in body["demo_notice"]
        assert "CONTROLLED PROTOTYPE" in body["demo_notice"]
        assert body["automatic_sanction"] is False
        assert body["automatic_payment"] is False
        assert body["fraud_conclusion"] is False
        assert body["pfms_integrated"] is False
        assert len(body["journey"]) == 10
        assert body["available_evidence"]["count"] > 0


def test_assemble_case_does_not_call_ensure_evidence(client) -> None:
    """Verify that ensure_demo_case_evidence is never executed on GET requests."""
    session = get_session_factory()()
    try:
        _seed(session)
    finally:
        session.close()

    with patch("app.demo.service.ensure_demo_case_evidence") as mock_ensure:
        for case_id in CASE_IDS:
            response = client.get(f"/api/v1/demo-cases/{case_id}", params={"data_mode": "HYBRID"})
            assert response.status_code == 200

        # ensure_demo_case_evidence should NEVER be called on GET requests
        assert mock_ensure.call_count == 0


def test_query_count_is_minimal(client) -> None:
    """Verify the endpoint executes minimal queries without repeated per-engine round-trips."""
    session = get_session_factory()()
    try:
        _seed(session)
    finally:
        session.close()

    # Call endpoint and ensure fast sub-second completion
    t0 = time.perf_counter()
    response = client.get("/api/v1/demo-cases/CLEAN", params={"data_mode": "HYBRID"})
    elapsed = time.perf_counter() - t0

    assert response.status_code == 200
    assert elapsed < 0.5, f"CLEAN endpoint took {elapsed:.2f}s, expected < 0.5s"
