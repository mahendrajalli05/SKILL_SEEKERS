"""Build evidence provenance from a project row and optional snapshot.

Does not invent government fields. Held-out scenario labels are never copied.
"""

from __future__ import annotations

from app.domain.enums import DataMode, SourceType
from app.domain.schemas.evidence import EvidenceProvenance
from app.evidence.constants import (
    HYBRID_ENRICHMENT_RELATIVE_PATH,
    HYBRID_ENRICHMENT_SHA256,
    HYBRID_PROVENANCE_NOTE,
    REAL_PROVENANCE_NOTE,
    SYNTHETIC_PROVENANCE_NOTE,
)
from app.models.project import Project
from app.models.snapshot import DatasetSnapshot


def _iso(value: object) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    text = str(value).strip()
    return text or None


def resolve_data_mode(*, is_synthetic: bool, engine_mode: str | None = None) -> DataMode:
    if is_synthetic:
        return DataMode.SYNTHETIC
    if engine_mode in {"HYBRID_TEST", "HYBRID"}:
        return DataMode.HYBRID
    return DataMode.REAL


def resolve_source_type(data_mode: DataMode, *, primary: SourceType | None = None) -> SourceType:
    if primary is not None:
        return primary
    if data_mode == DataMode.SYNTHETIC:
        return SourceType.SYNTHETIC_TEST_RECORD
    if data_mode == DataMode.HYBRID:
        return SourceType.HYBRID_ENRICHMENT
    return SourceType.MPLADS_PROJECT_RECORD


def build_source_ids(
    internal_project_id: str,
    extra: list[str] | tuple[str, ...] | None = None,
) -> list[str]:
    ids: list[str] = []
    seen: set[str] = set()
    for item in (internal_project_id, *(extra or ())):
        text = str(item).strip()
        if text and text not in seen:
            seen.add(text)
            ids.append(text)
    return ids


def build_provenance(
    project: Project,
    *,
    data_mode: DataMode,
    source_type: SourceType,
    source_ids: list[str],
    snapshot: DatasetSnapshot | None = None,
    extra_notes: str | None = None,
) -> EvidenceProvenance:
    snap = snapshot or getattr(project, "snapshot", None)
    if data_mode == DataMode.SYNTHETIC:
        notes = SYNTHETIC_PROVENANCE_NOTE
        if project.synthetic_label:
            notes = f"{notes} Label: {project.synthetic_label}."
        enrichment_used = False
        enrichment_path = None
        enrichment_sha256 = None
    elif data_mode == DataMode.HYBRID:
        notes = HYBRID_PROVENANCE_NOTE
        enrichment_used = True
        enrichment_path = HYBRID_ENRICHMENT_RELATIVE_PATH
        enrichment_sha256 = HYBRID_ENRICHMENT_SHA256
    else:
        notes = REAL_PROVENANCE_NOTE
        enrichment_used = False
        enrichment_path = None
        enrichment_sha256 = None
    if extra_notes:
        notes = f"{notes} {extra_notes}".strip()

    source_dataset = project.source_dataset
    source_url = snap.source_url if snap is not None else None
    if data_mode == DataMode.REAL and not source_dataset and not source_url:
        source_dataset = source_dataset or "mplads_works_cleaned.csv"

    return EvidenceProvenance(
        data_mode=data_mode,
        source_type=source_type,
        source_ids=source_ids,
        internal_project_id=project.internal_project_id,
        notes=notes,
        source_dataset=source_dataset,
        source_url=source_url,
        extracted_at=_iso(snap.extracted_at) if snap is not None else None,
        download_date=snap.download_date if snap is not None else None,
        publisher=snap.publisher if snap is not None else None,
        file_sha256=snap.file_sha256 if snap is not None else None,
        source_filename=snap.source_filename if snap is not None else None,
        source_sha256=snap.source_sha256 if snap is not None else None,
        snapshot_id=snap.id if snap is not None else None,
        internal_id_scheme=project.internal_id_scheme,
        source_first_row_number=project.source_first_row_number,
        enrichment_used=enrichment_used,
        enrichment_path=enrichment_path,
        enrichment_sha256=enrichment_sha256,
    )
