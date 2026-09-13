"""Potential manipulation signal. Independent of AI-generation and metadata."""

from __future__ import annotations

from typing import Any

from app.domain.enums import DataMode
from app.engines.forensics.confidence import capped, confidence_label
from app.engines.forensics.constants import (
    INCONCLUSIVE,
    NO_STRONG_FORENSIC_SIGNAL,
    POTENTIAL_MANIPULATION,
    SIGNAL_MANIPULATION,
)
from app.engines.forensics.types import ForensicSignal


def assess_manipulation(
    transformation: dict[str, Any],
    *,
    data_mode: DataMode,
    metadata_result: str,
) -> ForensicSignal:
    findings: list[str] = []
    notes = [
        "Manipulation analysis is a prototype assistance layer. "
        "It does not claim that an image is manipulated.",
    ]
    repeated = transformation.get("repeated_regions") or {}
    resampling = transformation.get("resampling") or {}
    recompression = transformation.get("recompression") or {}
    readable = bool(transformation.get("readable"))

    copy_move = repeated.get("result") == "REPEATED_REGION_SIGNAL" and int(repeated.get("match_pairs") or 0) >= 1
    dimension_mismatch = bool(resampling.get("dimension_mismatch"))
    editor_combo = metadata_result == "METADATA_ANOMALY" and dimension_mismatch
    if copy_move:
        findings.append(str(repeated.get("note") or "Repeated regions were observed."))
    if dimension_mismatch:
        findings.append(str(resampling.get("note") or "Dimension mismatch was observed."))
    if recompression.get("low_quality_jpeg"):
        notes.append(
            "Low JPEG quality / possible recompression was recorded as context only."
        )

    if not readable:
        result = INCONCLUSIVE
        assessable = False
        confidence = 0.12
        findings.append("The file could not be decoded, so manipulation analysis is INCONCLUSIVE.")
    elif copy_move or editor_combo:
        result = POTENTIAL_MANIPULATION
        assessable = True
        confidence = 0.52 if copy_move else 0.38
        notes.append("POTENTIAL_MANIPULATION is a review signal, not a finding that the image is manipulated.")
    elif dimension_mismatch or recompression.get("uneven"):
        result = INCONCLUSIVE
        assessable = False
        confidence = 0.28
        findings.append(
            "Transformation indicators were present but are not independently sufficient. "
            "The manipulation signal is INCONCLUSIVE."
        )
    else:
        result = NO_STRONG_FORENSIC_SIGNAL
        assessable = True
        confidence = 0.34
        findings.append("No strong, independently supportable manipulation indicator was identified.")

    numeric = capped(confidence, data_mode)
    return ForensicSignal(
        name=SIGNAL_MANIPULATION,
        result=result,
        confidence_label=confidence_label(numeric, assessable=assessable),
        confidence=numeric,
        available=readable,
        findings=findings,
        notes=notes,
        details={
            "copy_move": copy_move,
            "dimension_mismatch": dimension_mismatch,
            "low_quality_jpeg": bool(recompression.get("low_quality_jpeg")),
            "match_pairs": repeated.get("match_pairs"),
        },
    )
