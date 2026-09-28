from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import check_connection, get_db, get_engine
from app.domain.schemas.common import DatabaseHealth, GovernanceNotice, HealthResponse
from app.errors import AppError
from app.models import Base

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(_db: Session = Depends(get_db)) -> HealthResponse:
    settings = get_settings()
    engine = get_engine()
    dialect = engine.dialect.name
    try:
        connected = check_connection()
    except Exception as exc:  # noqa: BLE001 — surface as a structured 503
        db_label = "PostgreSQL" if dialect == "postgresql" else "SQLite"
        raise AppError(
            f"{db_label} is not reachable.",
            code="database_unavailable",
            status_code=503,
        ) from exc

    if dialect == "postgresql":
        host = engine.url.host or "localhost"
        database = engine.url.database or ""
        path = f"{host}/{database}" if database else host
    else:
        path = str(settings.sqlite_path)

    return HealthResponse(
        status="ok",
        service="sarvsakshi-api",
        environment=settings.env,
        database=DatabaseHealth(
            connected=connected,
            dialect=dialect,
            path=path,
            tables=sorted(Base.metadata.tables.keys()),
        ),
        llm_enabled=settings.llm_enabled,
        engine_version=settings.engine_version,
        fusion_config_version=settings.fusion_config_version,
        governance=GovernanceNotice(),
    )
