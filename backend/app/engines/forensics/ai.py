"""AI-generation detector abstraction.

V1 does not ship a validated local detector and does not transmit images
to external services by default. A future forensic model can be plugged in
via set_ai_detector().
"""

from __future__ import annotations

from typing import Any, Protocol

from app.config import get_settings
from app.domain.enums import DataMode
from app.engines.forensics.confidence import capped, confidence_label
from app.engines.forensics.constants import (
    AI_BACKEND_UNAVAILABLE,
    AI_GENERATION_ANALYSIS_UNAVAILABLE,
    INCONCLUSIVE,
    POTENTIAL_AI_GENERATION,
    SIGNAL_AI,
)
from app.engines.forensics.types import ForensicSignal


class AiGenerationDetector(Protocol):
    name: str

    def available(self) -> bool:
        """True only when a testable local model is actually loaded."""

    def analyze(self, payload: bytes) -> dict[str, Any]:
        """Return a detector payload. Must not invent certainty."""


class UnavailableAiGenerationDetector:
    """Default V1 backend. No local model is bundled."""

    name = AI_BACKEND_UNAVAILABLE

    def available(self) -> bool:
        return False

    def analyze(self, payload: bytes) -> dict[str, Any]:
        _ = payload
        return {
            "capability": AI_GENERATION_ANALYSIS_UNAVAILABLE,
            "result": AI_GENERATION_ANALYSIS_UNAVAILABLE,
            "score": None,
            "explanation": (
                "No suitable open-source AI-generated-image detector is bundled or "
                "justified in Image Forensics V1. Arbitrary pixel heuristics are not used. "
                "Result: AI_GENERATION_ANALYSIS_UNAVAILABLE."
            ),
            "external_transmission": False,
        }


_DETECTOR: AiGenerationDetector = UnavailableAiGenerationDetector()


def get_ai_detector() -> AiGenerationDetector:
    return _DETECTOR


def set_ai_detector(detector: AiGenerationDetector) -> None:
    """Test/future hook. Production V1 keeps UnavailableAiGenerationDetector."""
    global _DETECTOR
    _DETECTOR = detector


def reset_ai_detector() -> None:
    global _DETECTOR
    _DETECTOR = UnavailableAiGenerationDetector()


def _external_requested() -> bool:
    settings = get_settings()
    return bool(getattr(settings, "forensics_ai_external_enabled", False))


def analyze_ai_generation(payload: bytes, *, data_mode: DataMode) -> ForensicSignal:
    if _external_requested():
        notes = [
            "External AI analysis was requested in configuration, but Image Forensics V1 "
            "does not transmit project images to external services. Result remains unavailable.",
        ]
        raw = UnavailableAiGenerationDetector().analyze(payload)
        raw["external_transmission"] = False
    else:
        detector = get_ai_detector()
        raw = detector.analyze(payload)
        notes = [
            "Project images are processed locally. They are not sent to external services by default.",
        ]

    result = str(raw.get("result") or AI_GENERATION_ANALYSIS_UNAVAILABLE)
    if result not in {AI_GENERATION_ANALYSIS_UNAVAILABLE, INCONCLUSIVE, POTENTIAL_AI_GENERATION}:
        result = INCONCLUSIVE
    available = result not in {AI_GENERATION_ANALYSIS_UNAVAILABLE, INCONCLUSIVE}
    if result == POTENTIAL_AI_GENERATION and raw.get("score") is None:
        result = INCONCLUSIVE
        notes.append(
            "A detector returned a potential AI-generation signal without a testable score. "
            "The result is treated as INCONCLUSIVE."
        )
        available = False
    confidence = 0.0 if not available else capped(0.4, data_mode)
    numeric = capped(confidence, data_mode)
    explanation = str(raw.get("explanation") or "")
    return ForensicSignal(
        name=SIGNAL_AI,
        result=result,
        confidence_label=confidence_label(numeric, assessable=available),
        confidence=numeric,
        available=available,
        findings=[explanation] if explanation else [],
        notes=notes,
        details={
            "capability": raw.get("capability") or AI_GENERATION_ANALYSIS_UNAVAILABLE,
            "backend": getattr(get_ai_detector(), "name", AI_BACKEND_UNAVAILABLE),
            "score": raw.get("score"),
            "external_transmission": False,
        },
    )
