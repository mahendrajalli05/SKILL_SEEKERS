"""Modular forensic pipeline.

Input image → integrity → metadata → transformation → manipulation →
AI-generation → explanation → Evidence Object.
Each stage can run independently.
"""

from __future__ import annotations

from typing import Any

from app.domain.enums import DataMode
from app.engines.forensics.ai import analyze_ai_generation
from app.engines.forensics.confidence import capped, confidence_label
from app.engines.forensics.constants import (
    GOVERNANCE_NOTE,
    INCONCLUSIVE,
    INTEGRITY_OK,
    NO_STRONG_FORENSIC_SIGNAL,
    POTENTIAL_MANIPULATION,
    PROTOTYPE_ASSESSMENT_LABEL,
    REVIEW_REQUIRED,
    SIGNAL_QUALITY,
    SIGNAL_REUSE,
)
from app.engines.forensics.explain import assess_overall, build_explanation
from app.engines.forensics.integrity import check_integrity
from app.engines.forensics.manipulation import assess_manipulation
from app.engines.forensics.metadata import analyze_metadata
from app.engines.forensics.pce import frame_against_claim
from app.engines.forensics.transform import analyze_transformation
from app.engines.forensics.types import ForensicResult, ForensicSignal
from app.engines.pce.types import AssembledClaim


def _reuse_signal(analysis: dict[str, Any], *, data_mode: DataMode) -> ForensicSignal:
    exact = bool(analysis.get("exact_duplicate"))
    reuse = bool(analysis.get("potential_reuse"))
    integrity = str(analysis.get("integrity_status") or "UNIQUE")
    if exact:
        result = "EXACT_DUPLICATE"
        findings = ["SHA-256 exact duplicate from Image Evidence V1. Not a legal finding."]
        confidence = 0.55
        assessable = True
    elif reuse:
        result = "POTENTIAL_IMAGE_REUSE"
        findings = ["Perceptual near-duplicate from Image Evidence V1. Not a legal finding."]
        confidence = 0.48
        assessable = True
    elif integrity == "UNREADABLE":
        result = INCONCLUSIVE
        findings = ["Reuse could not be assessed because the file was unreadable."]
        confidence = 0.12
        assessable = False
    else:
        result = "UNIQUE"
        findings = ["No exact or near duplicate was reported by Image Evidence V1."]
        confidence = 0.40
        assessable = True
    numeric = capped(confidence, data_mode)
    return ForensicSignal(
        name=SIGNAL_REUSE,
        result=result,
        confidence_label=confidence_label(numeric, assessable=assessable),
        confidence=numeric,
        available=True,
        findings=findings,
        notes=["Reuse_signal reuses Image Evidence V1 hashes. It is not a new detector."],
        details={
            "integrity_status": integrity,
            "exact_matches": analysis.get("exact_matches") or [],
            "reuse_matches": analysis.get("reuse_matches") or [],
        },
    )


def _quality_signal(analysis: dict[str, Any], *, data_mode: DataMode) -> ForensicSignal:
    quality = analysis.get("quality") or {}
    warnings = list(quality.get("warnings") or [])
    readable = bool(quality.get("readable", True))
    if not readable:
        result = INCONCLUSIVE
        assessable = False
        confidence = 0.12
        findings = ["Image quality could not be assessed."]
    elif warnings:
        result = "QUALITY_WARNING"
        assessable = True
        confidence = 0.36
        findings = warnings
    else:
        result = NO_STRONG_FORENSIC_SIGNAL
        assessable = True
        confidence = 0.40
        findings = ["No technical quality warning was recorded."]
    numeric = capped(confidence, data_mode)
    return ForensicSignal(
        name=SIGNAL_QUALITY,
        result=result,
        confidence_label=confidence_label(numeric, assessable=assessable),
        confidence=numeric,
        available=readable,
        findings=findings,
        notes=["Quality warnings are technical only and are not treated as wrongdoing."],
        details=quality if isinstance(quality, dict) else {},
    )


def evaluate_image_forensics(
    *,
    image_id: int,
    project_id: int,
    payload: bytes | None,
    stored_sha256: str | None,
    mime_type: str | None,
    file_size: int | None,
    data_mode: DataMode,
    image_analysis: dict[str, Any],
    claim: AssembledClaim | None = None,
    filename: str | None = None,
    ahash: str | None = None,
    dhash: str | None = None,
    phash: str | None = None,
) -> ForensicResult:
    integrity = check_integrity(
        payload,
        stored_sha256=stored_sha256,
        mime_type=mime_type,
        file_size=file_size,
    )
    raw = payload or b""
    metadata = analyze_metadata(raw, data_mode=data_mode) if payload else ForensicSignal(
        name="metadata_signal",
        result=INCONCLUSIVE,
        confidence_label=INCONCLUSIVE,
        confidence=0.0,
        available=False,
        findings=["Metadata analysis could not run because stored bytes were missing."],
    )
    transformation = (
        analyze_transformation(raw, metadata_details=metadata.details)
        if payload
        else {"readable": False, "result": INCONCLUSIVE}
    )
    manipulation = assess_manipulation(
        transformation,
        data_mode=data_mode,
        metadata_result=metadata.result,
    )
    ai = (
        analyze_ai_generation(raw, data_mode=data_mode)
        if payload
        else ForensicSignal(
            name="ai_generation_signal",
            result="AI_GENERATION_ANALYSIS_UNAVAILABLE",
            confidence_label=INCONCLUSIVE,
            confidence=0.0,
            available=False,
            findings=["AI-generation analysis unavailable because stored bytes were missing."],
            details={"external_transmission": False},
        )
    )
    reuse = _reuse_signal(image_analysis, data_mode=data_mode)
    quality = _quality_signal(image_analysis, data_mode=data_mode)
    if integrity.status != INTEGRITY_OK:
        manipulation = ForensicSignal(
            name=manipulation.name,
            result=INCONCLUSIVE,
            confidence_label=INCONCLUSIVE,
            confidence=capped(0.12, data_mode),
            available=False,
            findings=["Manipulation analysis is INCONCLUSIVE because file integrity is not OK."],
            notes=manipulation.notes,
            details=manipulation.details,
        )

    overall = assess_overall(
        manipulation=manipulation,
        ai=ai,
        metadata=metadata,
        reuse=reuse,
        quality=quality,
    )
    confidences = [
        item.confidence
        for item in (manipulation, metadata, reuse, quality, ai)
        if item.available or item.result == POTENTIAL_MANIPULATION
    ]
    evidence_confidence = capped(
        (sum(confidences) / len(confidences)) if confidences else 0.18,
        data_mode,
    )
    result = ForensicResult(
        image_id=image_id,
        project_id=project_id,
        data_mode=data_mode,
        integrity=integrity,
        metadata_signal=metadata,
        transformation=transformation,
        manipulation_signal=manipulation,
        ai_generation_signal=ai,
        reuse_signal=reuse,
        quality_signal=quality,
        overall_assessment=overall,
        prototype_assessment_label=PROTOTYPE_ASSESSMENT_LABEL,
        evidence_confidence=evidence_confidence,
        confidence_label=confidence_label(
            evidence_confidence,
            assessable=overall != INCONCLUSIVE,
        ),
        finding=overall,
        source="image-forensics-v1",
        filename=filename,
        mime_type=mime_type,
        file_size=file_size,
        ahash=ahash or image_analysis.get("ahash"),
        dhash=dhash or image_analysis.get("dhash"),
        phash=phash or image_analysis.get("phash"),
        content_sha256=integrity.content_sha256 or stored_sha256,
        bytes_unmodified=integrity.bytes_unmodified,
        note=GOVERNANCE_NOTE,
        synthetic=data_mode.value != "REAL",
        synthetic_label=(
            "TEST DATA — SYNTHETIC forensic image fixture. Not an official government photograph."
            if data_mode.value != "REAL"
            else None
        ),
    )
    result.plan_claim_evidence = frame_against_claim(result, claim)
    result.explanation = build_explanation(result)
    return result
