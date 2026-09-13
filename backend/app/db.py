from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.logging_config import get_logger
from app.models import Base

# Skeleton columns from Phase 1. Presence means this file predates the cleaned schema.
_STALE_PROJECT_COLUMNS = frozenset(
    {
        "unique_work_number",
        "implementing_district",
        "sanction_date",
        "date_of_completion",
        "utilised_amount",
    }
)
_REQUIRED_PROJECT_COLUMNS = frozenset({"internal_project_id", "source_mp_name", "allocation_amount"})

# Additive Evidence Object V1 columns. Existing rows stay; values are filled on persist.
_EVIDENCE_OBJECT_COLUMNS = {
    "evidence_id": "TEXT",
    "engine_name": "TEXT",
    "signal_type": "TEXT",
    "disposition": "TEXT",
    "finding": "TEXT",
    "explanation": "TEXT",
    "score": "FLOAT",
    "confidence": "FLOAT",
    "source_type": "TEXT",
    "source_ids_json": "TEXT",
    "data_mode": "TEXT",
    "provenance_json": "TEXT",
}
_EVIDENCE_FACT_COLUMNS = {
    "fact_kind": "TEXT DEFAULT 'OBSERVATION'",
    "statement": "TEXT",
}
_FUSION_SCORE_COLUMNS = {
    "data_mode": "TEXT",
    "recommended_action": "TEXT",
    "explanation_type": "TEXT",
    "payload_json": "TEXT",
}
_CLAIM_COLUMNS = {
    "claimed_progress_percent": "FLOAT",
    "claimed_quantity": "FLOAT",
    "claimed_quantity_unit": "TEXT",
    "claim_date": "DATETIME",
    "claimant_source": "TEXT",
    "supporting_document_ids_json": "TEXT",
    "data_mode": "TEXT",
    "provenance_json": "TEXT",
}
_DOCUMENT_COLUMNS = {
    "filename": "TEXT",
    "document_type": "TEXT",
    "source": "TEXT",
    "data_mode": "TEXT",
    "provenance_json": "TEXT",
    "content_sha256": "TEXT",
    "observed_quantity": "FLOAT",
    "observed_quantity_unit": "TEXT",
    "observed_expenditure": "FLOAT",
    "notes": "TEXT",
    "mime_type": "TEXT",
    "file_size": "INTEGER",
    "extraction_status": "TEXT",
    "integrity_status": "TEXT",
    "duplicate_of_id": "INTEGER",
}
_PLAN_ARTIFACT_COLUMNS = {
    "extraction_status": "TEXT",
    "extraction_method": "TEXT",
    "text_sha256": "TEXT",
    "attached_to_plan": "INTEGER",
    "attached_to_evidence": "INTEGER",
    "data_mode": "TEXT",
    "provenance_json": "TEXT",
}
_CITIZEN_REPORT_COLUMNS = {
    "satisfaction_rating": "INTEGER",
    "observation_text": "TEXT",
    "issue_category": "TEXT",
    "submitted_at": "DATETIME",
    "image_id": "INTEGER",
    "submission_status": "TEXT",
    "verification_result": "TEXT",
    "timestamp_status": "TEXT",
    "data_mode": "TEXT",
    "provenance_json": "TEXT",
    "analysis_json": "TEXT",
    "duplicate_flag": "TEXT",
    "watermark_path": "TEXT",
    "evidence_ids_json": "TEXT",
    "rejection_reason": "TEXT",
    "synthetic": "INTEGER DEFAULT 0",
    "capture_timestamp": "TEXT",
}
_PHOTO_COLUMNS = {
    "filename": "TEXT",
    "source": "TEXT",
    "data_mode": "TEXT",
    "provenance_json": "TEXT",
    "observed_quantity": "FLOAT",
    "observed_quantity_unit": "TEXT",
    "notes": "TEXT",
    "mime_type": "TEXT",
    "file_size": "INTEGER",
    "content_sha256": "TEXT",
    "ahash": "TEXT",
    "dhash": "TEXT",
    "duplicate_of_id": "INTEGER",
    "integrity_status": "TEXT",
    "attached_to_evidence": "INTEGER",
    "analysis_json": "TEXT",
    "analysis_status": "TEXT",
    "forensics_json": "TEXT",
    "forensics_status": "TEXT",
}

_COPILOT_TURN_COLUMNS = {
    "session_id": "TEXT",
    "data_mode": "TEXT",
    "intent": "TEXT",
    "evidence_ids_json": "TEXT",
    "recommended_action": "TEXT",
}

logger = get_logger("sarvsakshi.db")

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        settings = get_settings()
        settings.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(
            settings.sqlalchemy_url,
            connect_args={"check_same_thread": False, "timeout": 30.0},
            future=True,
        )

        @event.listens_for(_engine, "connect")
        def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:  # type: ignore[no-untyped-def]
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            # WAL plus a bounded busy timeout keeps concurrent API reads/writes from failing immediately.
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA busy_timeout=30000")
            cursor.close()

        logger.info("sqlite_engine_created path=%s", settings.sqlite_path)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(),
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            future=True,
        )
    return _session_factory


def reset_engine() -> None:
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None


def schema_is_stale(engine: Engine | None = None) -> bool:
    """True when an older skeleton ``project`` table cannot hold cleaned fields."""
    engine = engine or get_engine()
    inspector = inspect(engine)
    if "project" not in inspector.get_table_names():
        return False
    columns = {column["name"] for column in inspector.get_columns("project")}
    if _REQUIRED_PROJECT_COLUMNS - columns:
        return True
    return bool(columns & _STALE_PROJECT_COLUMNS)


def _add_missing_columns(engine: Engine, table: str, columns: dict[str, str]) -> None:
    inspector = inspect(engine)
    if table not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns(table)}
    with engine.begin() as connection:
        for name, declaration in columns.items():
            if name in existing:
                continue
            connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {declaration}"))
            logger.info("sqlite_column_added table=%s column=%s", table, name)


def ensure_fusion_schema(engine: Engine | None = None) -> None:
    """Add Risk Fusion V1 columns without dropping existing fusion rows."""
    engine = engine or get_engine()
    _add_missing_columns(engine, "fusion_score", _FUSION_SCORE_COLUMNS)


def ensure_evidence_schema(engine: Engine | None = None) -> None:
    """Add Evidence Object V1 columns without dropping existing tables or rows."""
    engine = engine or get_engine()
    _add_missing_columns(engine, "evidence_object", _EVIDENCE_OBJECT_COLUMNS)
    _add_missing_columns(engine, "evidence_fact", _EVIDENCE_FACT_COLUMNS)
    inspector = inspect(engine)
    if "evidence_object" not in inspector.get_table_names():
        return
    index_names = {item["name"] for item in inspector.get_indexes("evidence_object")}
    with engine.begin() as connection:
        if "ix_evidence_object_evidence_id" not in index_names and "uq_evidence_object_evidence_id" not in index_names:
            connection.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ix_evidence_object_evidence_id "
                    "ON evidence_object (evidence_id)"
                )
            )
        if "ix_evidence_object_project_id" not in index_names:
            connection.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_evidence_object_project_id "
                    "ON evidence_object (project_id)"
                )
            )
        if "ix_evidence_object_data_mode" not in index_names:
            connection.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_evidence_object_data_mode "
                    "ON evidence_object (data_mode)"
                )
            )


def ensure_pce_schema(engine: Engine | None = None) -> None:
    """Add Plan–Claim–Evidence V1 columns without dropping existing rows."""
    engine = engine or get_engine()
    _add_missing_columns(engine, "claim", _CLAIM_COLUMNS)
    _add_missing_columns(engine, "document", _DOCUMENT_COLUMNS)
    _add_missing_columns(engine, "photo", _PHOTO_COLUMNS)


def ensure_document_schema(engine: Engine | None = None) -> None:
    """Add Document & Blueprint V1 columns without dropping existing rows."""
    engine = engine or get_engine()
    _add_missing_columns(engine, "document", _DOCUMENT_COLUMNS)
    _add_missing_columns(engine, "plan_artifact", _PLAN_ARTIFACT_COLUMNS)


def ensure_image_schema(engine: Engine | None = None) -> None:
    """Add Image Evidence V1 columns without dropping existing photo rows."""
    engine = engine or get_engine()
    _add_missing_columns(engine, "photo", _PHOTO_COLUMNS)


def ensure_citizen_schema(engine: Engine | None = None) -> None:
    """Add Jan-Sakshi V1 columns without dropping existing citizen rows."""
    engine = engine or get_engine()
    _add_missing_columns(engine, "citizen_report", _CITIZEN_REPORT_COLUMNS)


def ensure_copilot_schema(engine: Engine | None = None) -> None:
    """Add Investigation Copilot V1 columns without dropping existing turns."""
    engine = engine or get_engine()
    _add_missing_columns(engine, "copilot_turn", _COPILOT_TURN_COLUMNS)


def init_db() -> None:
    """Create empty tables. Does not insert any government or demo rows."""
    engine = get_engine()
    if schema_is_stale(engine):
        logger.warning("stale sqlite schema detected; recreating empty tables")
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    ensure_evidence_schema(engine)
    ensure_fusion_schema(engine)
    ensure_pce_schema(engine)
    ensure_document_schema(engine)
    ensure_image_schema(engine)
    ensure_citizen_schema(engine)
    ensure_copilot_schema(engine)
    logger.info("sqlite_tables_ready tables=%s", sorted(Base.metadata.tables.keys()))


def check_connection() -> bool:
    with get_engine().connect() as connection:
        connection.execute(text("SELECT 1"))
    return True


def get_db() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
