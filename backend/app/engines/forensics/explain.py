"""Human-readable forensic explanations. Never claims fraud or certainty."""

from __future__ import annotations

from app.engines.forensics.constants import (
    AI_GENERATION_ANALYSIS_UNAVAILABLE,
    ASSESSMENT_FORMULA,
    GOVERNANCE_NOTE,
    INCONCLUSIVE,
    METADATA_ANOMALY,
    NO_STRONG_FORENSIC_SIGNAL,
    POTENTIAL_MANIPULATION,
    PROTOTYPE_ASSESSMENT_LABEL,
    REVIEW_REQUIRED,
)
from app.engines.forensics.types import ForensicResult, ForensicSignal

_WEAK = {INCONCLUSIVE, AI_GENERATION_ANALYSIS_UNAVAILABLE}


def _signal_sentence(signal: ForensicSignal) -> str:
    bits = [f"{signal.name}={signal.result} (confidence {signal.confidence_label})."]
    bits.extend(signal.findings)
    return " ".join(bits)


def overall_finding(result: ForensicResult) -> str:
    return result.overall_assessment


def assess_overall(
    *,
    manipulation: ForensicSignal,
    ai: ForensicSignal,
    metadata: ForensicSignal,
    reuse: ForensicSignal,
    quality: ForensicSignal,
) -> str:
    _ = (ai, quality)
    if (
        manipulation.result == POTENTIAL_MANIPULATION
        or metadata.result == METADATA_ANOMALY
        or reuse.result in {"EXACT_DUPLICATE", "POTENTIAL_IMAGE_REUSE"}
    ):
        return REVIEW_REQUIRED
    independent = [manipulation.result, metadata.result, reuse.result]
    if all(item in _WEAK for item in independent):
        return INCONCLUSIVE
    if manipulation.result in {NO_STRONG_FORENSIC_SIGNAL, INCONCLUSIVE} and reuse.result in {
        "UNIQUE",
        NO_STRONG_FORENSIC_SIGNAL,
        INCONCLUSIVE,
    }:
        return NO_STRONG_FORENSIC_SIGNAL
    return INCONCLUSIVE


def build_explanation(result: ForensicResult) -> str:
    parts = [
        GOVERNANCE_NOTE,
        PROTOTYPE_ASSESSMENT_LABEL,
        f"Overall forensic assessment: {result.overall_assessment}.",
        _signal_sentence(result.manipulation_signal),
        _signal_sentence(result.ai_generation_signal),
        _signal_sentence(result.metadata_signal),
        _signal_sentence(result.reuse_signal),
        _signal_sentence(result.quality_signal),
        f"Integrity: {result.integrity.status}. Original bytes unmodified: {result.bytes_unmodified}.",
        ASSESSMENT_FORMULA,
    ]
    if result.data_mode.value != "REAL":
        parts.append(
            "This forensic run uses labelled TEST/SYNTHETIC image context and is not real field evidence."
        )
    return " ".join(parts)
