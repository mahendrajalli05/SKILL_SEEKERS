from __future__ import annotations

import os
import tempfile
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image
from sqlalchemy.pool import NullPool

from app.config import REPO_ROOT, Settings, get_settings, reset_settings_cache
from app.db import get_engine, init_db, reset_engine
from app.engines.citizen.watermark import save_watermark_copy
from app.engines.document.repository import (
    resolve_stored_path as resolve_doc_path,
    save_bytes as save_doc_bytes,
)
from app.engines.image.repository import (
    resolve_stored_path as resolve_image_path,
    save_bytes as save_image_bytes,
)


def test_sqlite_engine_preserves_local_behavior() -> None:
    """Ensure SQLite does NOT use NullPool and keeps its normal connection setup."""
    reset_engine()
    reset_settings_cache()
    try:
        engine = get_engine()
        assert not isinstance(engine.pool, NullPool)
        assert engine.url.drivername == "sqlite"
    finally:
        reset_engine()
        reset_settings_cache()


def test_postgres_engine_uses_nullpool() -> None:
    """Ensure non-SQLite (PostgreSQL / Supabase Transaction Pooler) uses NullPool."""
    reset_engine()
    reset_settings_cache()
    fake_pg_url = "postgresql+psycopg2://postgres.test:password@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"
    with patch.dict(os.environ, {"DATABASE_URL": fake_pg_url}, clear=False):
        reset_settings_cache()
        # Mock create_engine or let it instantiate with NullPool
        with patch("app.db.create_engine") as mock_create_engine:
            mock_create_engine.return_value = MagicMock()
            get_engine()
            assert mock_create_engine.called
            _, kwargs = mock_create_engine.call_args
            assert kwargs.get("poolclass") is NullPool
    reset_engine()
    reset_settings_cache()


def test_init_db_skipped_when_disabled() -> None:
    """Ensure init_db() does not run DDL or schema inspection when init_db_on_startup is False."""
    reset_settings_cache()
    with patch.dict(os.environ, {"SARVSAKSHI_INIT_DB_ON_STARTUP": "false"}, clear=False):
        reset_settings_cache()
        settings = get_settings()
        assert settings.init_db_on_startup is False

        with patch("app.db.Base.metadata.create_all") as mock_create_all:
            init_db(force=False)
            assert not mock_create_all.called

            # force=True overrides the guard
            with patch("app.db.ensure_evidence_schema"), \
                 patch("app.db.ensure_fusion_schema"), \
                 patch("app.db.ensure_pce_schema"), \
                 patch("app.db.ensure_document_schema"), \
                 patch("app.db.ensure_image_schema"), \
                 patch("app.db.ensure_citizen_schema"), \
                 patch("app.db.ensure_copilot_schema"), \
                 patch("app.db.schema_is_stale", return_value=False):
                init_db(force=True)
                assert mock_create_all.called
    reset_settings_cache()


def test_storage_root_falls_back_to_tmp_in_serverless() -> None:
    """Ensure storage_root points to tempdir in serverless and REPO_ROOT locally."""
    reset_settings_cache()
    local_settings = Settings(is_serverless=False, upload_dir="")
    assert local_settings.storage_root == REPO_ROOT

    serverless_settings = Settings(is_serverless=True, upload_dir="")
    temp_dir = Path(tempfile.gettempdir())
    assert serverless_settings.storage_root.is_relative_to(temp_dir) or str(serverless_settings.storage_root).startswith(str(temp_dir))


def test_serverless_image_upload_and_resolve(tmp_path: Path) -> None:
    """Ensure image repository writes and reads from configured temporary storage."""
    reset_settings_cache()
    test_upload_root = tmp_path / "serverless_uploads"
    with patch.dict(os.environ, {"SARVSAKSHI_UPLOAD_DIR": str(test_upload_root), "SARVSAKSHI_SERVERLESS": "true"}, clear=False):
        reset_settings_cache()
        settings = get_settings()
        assert settings.storage_root == test_upload_root

        project_id = 8888
        filename = "site_photo.jpg"
        payload = b"dummy-image-bytes-for-test"
        digest = "abcdef0123456789abcdef0123456789"

        stored_rel = save_image_bytes(project_id, filename, payload, digest)
        assert "data/uploads/images/8888" in stored_rel

        # Verify physical file was written under test_upload_root
        expected_file = test_upload_root / stored_rel
        assert expected_file.is_file()
        assert expected_file.read_bytes() == payload

        # Verify resolution
        resolved = resolve_image_path(stored_rel)
        assert resolved is not None
        assert resolved == expected_file
    reset_settings_cache()


def test_serverless_document_upload_and_resolve(tmp_path: Path) -> None:
    """Ensure document repository writes and reads from configured temporary storage."""
    reset_settings_cache()
    test_upload_root = tmp_path / "serverless_docs"
    with patch.dict(os.environ, {"SARVSAKSHI_UPLOAD_DIR": str(test_upload_root), "SARVSAKSHI_SERVERLESS": "true"}, clear=False):
        reset_settings_cache()

        project_id = 7777
        filename = "blueprint.pdf"
        payload = b"%PDF-1.4 dummy-pdf-content"
        digest = "1234567890abcdef1234567890abcdef"

        stored_rel = save_doc_bytes(project_id, filename, payload, digest)
        assert "data/uploads/documents/7777" in stored_rel

        expected_file = test_upload_root / stored_rel
        assert expected_file.is_file()
        assert expected_file.read_bytes() == payload

        resolved = resolve_doc_path(stored_rel)
        assert resolved is not None
        assert resolved == expected_file
    reset_settings_cache()


def test_serverless_citizen_watermark(tmp_path: Path) -> None:
    """Ensure citizen watermark writes to temporary storage without read-only errors."""
    reset_settings_cache()
    test_upload_root = tmp_path / "serverless_watermark"

    # Create a small valid test JPEG image in memory
    buf = BytesIO()
    img = Image.new("RGB", (700, 500), color=(100, 150, 200))
    img.save(buf, format="JPEG")
    image_bytes = buf.getvalue()

    with patch.dict(os.environ, {"SARVSAKSHI_UPLOAD_DIR": str(test_upload_root), "SARVSAKSHI_SERVERLESS": "true"}, clear=False):
        reset_settings_cache()
        result = save_watermark_copy(
            image_bytes,
            project_id=5555,
            original_digest="testdigest123456",
            scheme_id="MPLADS-TEST-001",
            submitted_at="2026-03-29T10:00:00Z",
            latitude=17.385,
            longitude=78.486,
        )
        assert result.generated is True
        assert result.watermark_path is not None
        assert "data/uploads/citizen_watermarks/5555" in result.watermark_path

        expected_file = test_upload_root / result.watermark_path
        assert expected_file.is_file()
        assert len(expected_file.read_bytes()) > 0
    reset_settings_cache()
