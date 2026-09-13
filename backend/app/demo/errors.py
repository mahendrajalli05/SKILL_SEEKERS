"""Demo Cases V1 errors. Not an intelligence-engine failure."""

from __future__ import annotations


class DemoCaseError(Exception):
    def __init__(self, message: str, *, code: str = "demo_case_error", status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
