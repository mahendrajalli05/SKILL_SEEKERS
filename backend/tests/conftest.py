from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import reset_settings_cache
from app.db import init_db, reset_engine


@pytest.fixture()
def client(tmp_path, monkeypatch) -> TestClient:
    db_path = tmp_path / "sarvsakshi-test.db"
    monkeypatch.setenv("SARVSAKSHI_DATABASE_PATH", str(db_path))
    monkeypatch.setenv("SARVSAKSHI_LLM_ENABLED", "false")
    reset_settings_cache()
    reset_engine()
    init_db()

    from app.main import create_app

    with TestClient(create_app()) as test_client:
        yield test_client

    reset_engine()
    reset_settings_cache()
