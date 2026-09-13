from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import reset_settings_cache
from app.db import init_db, reset_engine
from app.identity.scheme_id import reset_scheme_id_cache
from app.search.enrichment_display import reset_enrichment_display_cache
from app.search.hybrid import reset_hybrid_id_cache


@pytest.fixture()
def client(tmp_path, monkeypatch) -> TestClient:
    db_path = tmp_path / "sarvsakshi-test.db"
    monkeypatch.setenv("SARVSAKSHI_DATABASE_PATH", str(db_path))
    monkeypatch.setenv("SARVSAKSHI_LLM_ENABLED", "false")
    reset_settings_cache()
    reset_engine()
    reset_scheme_id_cache()
    reset_enrichment_display_cache()
    reset_hybrid_id_cache()
    init_db()

    from app.main import create_app

    with TestClient(create_app()) as test_client:
        yield test_client

    reset_engine()
    reset_scheme_id_cache()
    reset_enrichment_display_cache()
    reset_hybrid_id_cache()
    reset_settings_cache()
