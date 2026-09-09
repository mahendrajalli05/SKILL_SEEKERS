from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.logging_config import get_logger

logger = get_logger("sarvsakshi.errors")


class AppError(Exception):
    def __init__(self, message: str, *, code: str = "app_error", status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


def error_body(*, code: str, message: str, details: Any = None) -> dict[str, Any]:
    body: dict[str, Any] = {"error": {"code": code, "message": message}}
    if details is not None:
        body["error"]["details"] = details
    return body


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
        logger.warning("app_error code=%s message=%s", exc.code, exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(code=exc.code, message=exc.message),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation(_request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=error_body(
                code="validation_error",
                message="Request did not match the expected schema.",
                details=exc.errors(),
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(code="http_error", message=str(exc.detail)),
        )

    @app.exception_handler(SQLAlchemyError)
    async def handle_db(_request: Request, exc: SQLAlchemyError) -> JSONResponse:
        logger.exception("database_error: %s", exc)
        return JSONResponse(
            status_code=500,
            content=error_body(
                code="database_error",
                message="The database could not complete this request.",
            ),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_error: %s", exc)
        return JSONResponse(
            status_code=500,
            content=error_body(
                code="internal_error",
                message="An unexpected server error occurred.",
            ),
        )
