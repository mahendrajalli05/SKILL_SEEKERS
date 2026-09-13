"""Milestone Advisor V1 errors."""

from __future__ import annotations

from app.errors import AppError


class MilestoneError(AppError):
    def __init__(
        self,
        message: str,
        *,
        code: str = "milestone_error",
        status_code: int = 400,
    ) -> None:
        super().__init__(message, code=code, status_code=status_code)
