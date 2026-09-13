"""Plan–Claim–Evidence errors."""

from __future__ import annotations

from app.errors import AppError


class PceError(AppError):
    def __init__(self, message: str, *, code: str = "pce_error", status_code: int = 400) -> None:
        super().__init__(message, code=code, status_code=status_code)
