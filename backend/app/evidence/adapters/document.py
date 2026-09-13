"""Document & Blueprint V1 → canonical Evidence Object V1.

Does not change Evidence Object validation or frozen engine scoring.
"""

from __future__ import annotations

import hashlib
from typing import Any

from app.domain.enums import (
    DataMode,
    EvidenceDisposition,
    EvidenceEngine,
    EvidenceFactKind,
    EvidenceSeverity,
    SignalType,
    SourceType,
)
from app.domain.schemas.evidence import EvidenceObject
from app.engines.document.constants import ENGINE_NAME, ENGINE_VERSION
from app.engines.document.types import PlanConflict
from app.evidence.constants import DISPOSITION_TO_STATUS
from app.evidence.facts import make_fact
from app.evidence.provenance import build_provenance, build_source_ids
from app.models.project import Project
from app.models.snapshot import DatasetSnapshot


def _source_type(data_mode: DataMode) -> SourceType:
    if data_mode == DataMode.SYNTHETIC:
        return SourceType.SYNTHETIC_TEST_RECORD
    if data_mode == DataMode.HYBRID:
        return SourceType.HYBRID_ENRICHMENT
    return SourceType.DOCUMENT_ARTIFACT


def _evidence_id(project_id: int, document_id: int, data_mode: str, digest_key: str) -> str:
    payload = "|".join(
        [ENGINE_NAME, ENGINE_VERSION, str(project_id), str(document_id), data_mode, digest_key]
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"ev:{ENGINE_NAME}:{project_id}:document:{data_mode}:{digest}"


def extraction_to_evidence(
    project: Project,
    *,
    document_id: int,
    data_mode: DataMode,
    extraction: dict[str, Any],
    conflicts: list[PlanConflict],
    integrity_status: str,
    snapshot: DatasetSnapshot | None = None,
) -> EvidenceObject:
    source_type = _source_type(data_mode)
    source_ids = build_source_ids(project.internal_project_id, [f"document:{document_id}"])
    extra_notes = (
        "Officer-uploaded document extraction. Authenticity is not verified. "
        "This is not an official government document merely because it was uploaded."
    )
    if data_mode == DataMode.SYNTHETIC:
        extra_notes = f"{extra_notes} SYNTHETIC test fixture. Not a government project."
    provenance = build_provenance(
        project,
        data_mode=data_mode,
        source_type=source_type,
        source_ids=source_ids,
        snapshot=snapshot,
        extra_notes=extra_notes,
    )
    fields = [item for item in extraction.get("fields") or [] if isinstance(item, dict)]
    available = [item for item in fields if item.get("available")]
    status = str(extraction.get("status") or "INCONCLUSIVE")
    if conflicts:
        finding = "PLAN DATA CONFLICT between document sources"
        disposition = EvidenceDisposition.WHY_FLAGGED
        severity = EvidenceSeverity.WATCH
        explanation = (
            "Extracted document facts conflict with another recorded plan source. "
            "No source was chosen as truth. This is not a legal finding."
        )
    elif status in {"OCR_NOT_AVAILABLE", "INCONCLUSIVE"} or not available:
        finding = "Document extraction is INCONCLUSIVE"
        disposition = EvidenceDisposition.INCONCLUSIVE
        severity = EvidenceSeverity.INFO
        notes = extraction.get("notes") or []
        explanation = " ".join(str(item) for item in notes) or (
            "No labelled fields could be extracted from the uploaded document."
        )
    else:
        finding = "Extracted document facts recorded from officer-uploaded file"
        disposition = EvidenceDisposition.INCONCLUSIVE
        severity = EvidenceSeverity.INFO
        explanation = (
            "Structured fields were extracted from machine-readable text. "
            "Authenticity is not verified. Low-confidence values are not treated as authoritative."
        )
    facts = [
        make_fact("document_id", document_id, f"document:{document_id}", kind=EvidenceFactKind.OBSERVATION),
        make_fact("extraction_status", status, ENGINE_VERSION),
        make_fact("extraction_method", extraction.get("extraction_method"), ENGINE_VERSION),
        make_fact("integrity_status", integrity_status, ENGINE_VERSION),
        make_fact("page_count", extraction.get("page_count"), ENGINE_VERSION, kind=EvidenceFactKind.OBSERVATION),
        make_fact("data_mode", data_mode.value, ENGINE_VERSION, kind=EvidenceFactKind.OBSERVATION),
    ]
    for item in fields:
        source = f"document:{document_id}"
        if item.get("source_location"):
            source = f"{source} {item['source_location']}"
        facts.append(
            make_fact(
                str(item.get("name")),
                {
                    "value": item.get("value"),
                    "unit": item.get("unit"),
                    "confidence": item.get("confidence"),
                    "extraction_method": item.get("extraction_method"),
                    "source_location": item.get("source_location"),
                    "available": item.get("available"),
                    "unavailable_reason": item.get("unavailable_reason"),
                    "document_id": document_id,
                    "data_mode": data_mode.value,
                },
                source,
                kind=EvidenceFactKind.OBSERVATION,
            )
        )
    if conflicts:
        facts.append(
            make_fact(
                "plan_conflicts",
                [item.as_dict() for item in conflicts],
                ENGINE_VERSION,
            )
        )
    key = "|".join(
        [
            str(document_id),
            str(extraction.get("extraction_method") or ""),
            str(extraction.get("text_sha256") or ""),
            status,
        ]
    )
    return EvidenceObject(
        evidence_id=_evidence_id(project.id, document_id, data_mode.value, key),
        project_id=project.id,
        signal_type=SignalType.DOCUMENT,
        finding=finding,
        severity=severity,
        score=None,
        confidence=0.2 if not available else min(0.9, max(item.get("confidence") or 0.2 for item in available)),
        source_type=source_type,
        source_ids=source_ids,
        evidence_facts=facts,
        explanation=explanation,
        engine_name=EvidenceEngine.DOCUMENT.value,
        engine_version=ENGINE_VERSION,
        data_mode=data_mode,
        provenance=provenance,
        disposition=disposition,
        status=DISPOSITION_TO_STATUS[disposition],
    )
