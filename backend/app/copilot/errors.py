"""Investigation Copilot V1 errors."""

from __future__ import annotations

from app.errors import AppError


class CopilotError(AppError):
    """Officer-facing Copilot failure. Never invents a substitute answer."""
