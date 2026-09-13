"""Advanced image-forensics hook.

V1 does not run an AI-generated or manipulation detector. The backend is
structured so a later model can be added without changing the Evidence Object
envelope. No manipulation score is fabricated.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.engines.image.constants import (
    AUTHENTICITY_CAPABILITY,
    AUTHENTICITY_EXPLANATION,
    AUTHENTICITY_RESULT,
)
from app.engines.image.types import AuthenticityCapability


@dataclass(frozen=True)
class ForensicsResult:
    capability: str
    result: str
    explanation: str
    score: None = None


class ImageForensicsBackend(Protocol):
    def analyze(self, payload: bytes) -> ForensicsResult:
        """Return an authenticity assessment. Must not invent a score in V1."""


class NotImplementedForensics:
    """Default V1 backend. Explicitly inconclusive."""

    def analyze(self, payload: bytes) -> ForensicsResult:
        _ = payload
        return ForensicsResult(
            capability=AUTHENTICITY_CAPABILITY,
            result=AUTHENTICITY_RESULT,
            explanation=AUTHENTICITY_EXPLANATION,
            score=None,
        )


_BACKEND: ImageForensicsBackend = NotImplementedForensics()


def get_forensics_backend() -> ImageForensicsBackend:
    return _BACKEND


def set_forensics_backend(backend: ImageForensicsBackend) -> None:
    """Test/future hook. Production V1 keeps NotImplementedForensics."""
    global _BACKEND
    _BACKEND = backend


def reset_forensics_backend() -> None:
    global _BACKEND
    _BACKEND = NotImplementedForensics()


def assess_authenticity(payload: bytes) -> AuthenticityCapability:
    result = get_forensics_backend().analyze(payload)
    return AuthenticityCapability(
        capability=result.capability,
        result=result.result,
        explanation=result.explanation,
        score=result.score,
    )
