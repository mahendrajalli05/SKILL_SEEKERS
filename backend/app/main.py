from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.config import get_settings
from app.db import init_db
from app.errors import register_error_handlers
from app.logging_config import configure_logging, get_logger

logger = get_logger("sarvsakshi.api")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    init_db()
    logger.info(
        "sarvsakshi_api_started env=%s db=%s llm_enabled=%s",
        settings.env,
        settings.sqlite_path,
        settings.llm_enabled,
    )
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    application = FastAPI(
        title="SARVSAKSHI API",
        description=(
            "MPLADS Project Integrity & Investigation Layer. "
            "Returns investigation priority and evidence confidence. "
            "Does not output a legal fraud finding."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(application)
    application.include_router(api_router, prefix="/api/v1")

    @application.middleware("http")
    async def log_requests(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "request method=%s path=%s status=%s duration_ms=%.1f",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response

    return application


app = create_app()
