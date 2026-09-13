"""Advanced Image Forensics V1 typed payloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain.enums import DataMode
from app.engines.forensics.constants import (
    AI_GENERATION_ANALYSIS_UNAVAILABLE,
    ENGINE_VERSION,
    GOVERNANCE_NOTE,
    INCONCLUSIVE,
    LIMITATIONS,
    NO_STRONG_FORENSIC_SIGNAL,
    PROTOTYPE_ASSESSMENT_LABEL,
)


@dataclass
class ForensicSignal:
    name: str
    result: str
    confidence_label: str
    confidence: float
    available: bool
    findings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "result": self.result,
            "confidence_label": self.confidence_label,
            "confidence": self.confidence,
            "available": self.available,
            "findings": list(self.findings),
            "notes": list(self.notes),
            "details": self.details,
        }


@dataclass
class IntegrityCheck:
    status: str
    readable: bool
    content_sha256: str
    stored_sha256: str | None
    bytes_unmodified: bool
    mime_type: str | None
    file_size: int | None
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "readable": self.readable,
            "content_sha256": self.content_sha256,
            "stored_sha256": self.stored_sha256,
            "bytes_unmodified": self.bytes_unmodified,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "notes": list(self.notes),
        }


@dataclass
class PlanClaimEvidenceFraming:
    claim: str | None
    forensic: str
    result: str
    note: str
    claim_marked_false: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "claim": self.claim,
            "forensic": self.forensic,
            "result": self.result,
            "note": self.note,
            "claim_marked_false": self.claim_marked_false,
        }


@dataclass
class ForensicResult:
    image_id: int
    project_id: int
    data_mode: DataMode
    integrity: IntegrityCheck
    metadata_signal: ForensicSignal
    transformation: dict[str, Any]
    manipulation_signal: ForensicSignal
    ai_generation_signal: ForensicSignal
    reuse_signal: ForensicSignal
    quality_signal: ForensicSignal
    overall_assessment: str
    prototype_assessment_label: str = PROTOTYPE_ASSESSMENT_LABEL
    evidence_confidence: float = 0.0
    confidence_label: str = INCONCLUSIVE
    explanation: str = ""
    limitations: list[str] = field(default_factory=lambda: list(LIMITATIONS))
    plan_claim_evidence: PlanClaimEvidenceFraming | None = None
    evidence_ids: list[str] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)
    engine_version: str = ENGINE_VERSION
    note: str = GOVERNANCE_NOTE
    external_transmission: bool = False
    bytes_unmodified: bool = True
    thumbnail_data_url: str | None = None
    finding: str = NO_STRONG_FORENSIC_SIGNAL
    source: str = ENGINE_VERSION
    filename: str | None = None
    mime_type: str | None = None
    file_size: int | None = None
    ahash: str | None = None
    dhash: str | None = None
    phash: str | None = None
    content_sha256: str | None = None
    synthetic: bool = False
    synthetic_label: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "image_id": self.image_id,
            "project_id": self.project_id,
            "data_mode": self.data_mode.value,
            "integrity": self.integrity.as_dict(),
            "metadata_signal": self.metadata_signal.as_dict(),
            "transformation": self.transformation,
            "manipulation_signal": self.manipulation_signal.as_dict(),
            "ai_generation_signal": self.ai_generation_signal.as_dict(),
            "reuse_signal": self.reuse_signal.as_dict(),
            "quality_signal": self.quality_signal.as_dict(),
            "overall_assessment": self.overall_assessment,
            "prototype_assessment_label": self.prototype_assessment_label,
            "evidence_confidence": self.evidence_confidence,
            "confidence_label": self.confidence_label,
            "explanation": self.explanation,
            "limitations": list(self.limitations),
            "plan_claim_evidence": (
                self.plan_claim_evidence.as_dict() if self.plan_claim_evidence else None
            ),
            "evidence_ids": list(self.evidence_ids),
            "provenance": self.provenance,
            "engine_version": self.engine_version,
            "note": self.note,
            "external_transmission": self.external_transmission,
            "bytes_unmodified": self.bytes_unmodified,
            "thumbnail_data_url": self.thumbnail_data_url,
            "finding": self.finding,
            "source": self.source,
            "filename": self.filename,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "ahash": self.ahash,
            "dhash": self.dhash,
            "phash": self.phash,
            "content_sha256": self.content_sha256,
            "synthetic": self.synthetic,
            "synthetic_label": self.synthetic_label,
            "ai_generation_analysis": self.ai_generation_signal.result
            or AI_GENERATION_ANALYSIS_UNAVAILABLE,
        }
