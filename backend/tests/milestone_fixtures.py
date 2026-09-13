from __future__ import annotations

from datetime import date

from app.domain.enums import (
    DataMode,
    EvidenceDisposition,
    EvidenceEngine,
    EvidenceSeverity,
    LifecycleStage,
    SignalType,
    SourceType,
)
from app.domain.schemas.evidence import EvidenceObject, EvidenceProvenance
from app.evidence.facts import make_fact
from app.evidence.ids import make_evidence_id
from app.models.project import Project

SYNTHETIC_LABEL = "SYNTHETIC: milestone-advisor unit test (not a government project)"


def insert_project(session, **overrides: object) -> Project:
    values: dict[str, object] = {
        "internal_project_id": "internal:milestone:subject",
        "internal_id_kind": "internal_surrogate_hash",
        "internal_id_scheme": "sarvsakshi_internal_work_v1",
        "source_dataset": "github_vonter_india-mplads-works_MPLADS.csv",
        "is_synthetic": False,
        "lifecycle_stage": LifecycleStage.ONGOING.value,
        "state": "Andhra Pradesh",
        "constituency": "KURNOOL",
        "category": "Normal/Others",
        "work_description": "NA - Construction of community hall",
        "allocation_amount": 2_000_000,
        "recommended_date": date(2023, 6, 1),
        "status": "Ongoing",
        "mp_name": "Example MP",
        "ida": "District Collector_IDA",
    }
    values.update(overrides)
    row = Project(**values)
    session.add(row)
    session.flush()
    return row


def _provenance(data_mode: DataMode, internal_id: str) -> EvidenceProvenance:
    if data_mode == DataMode.HYBRID:
        return EvidenceProvenance(
            data_mode=DataMode.HYBRID,
            source_type=SourceType.HYBRID_ENRICHMENT,
            source_ids=[internal_id],
            internal_project_id=internal_id,
            notes=(
                "HYBRID/TEST: observed MPLADS fields plus synthetic enrichment. "
                "Synthetic fields are not official MPLADS values."
            ),
            source_dataset="github_vonter_india-mplads-works_MPLADS.csv",
            enrichment_used=True,
            enrichment_path="data/synthetic/sarvsakshi_synthetic_enrichment.csv",
        )
    if data_mode == DataMode.SYNTHETIC:
        return EvidenceProvenance(
            data_mode=DataMode.SYNTHETIC,
            source_type=SourceType.SYNTHETIC_TEST_RECORD,
            source_ids=[internal_id],
            internal_project_id=internal_id,
            notes="SYNTHETIC test record; not a government project. For controlled testing only.",
        )
    return EvidenceProvenance(
        data_mode=DataMode.REAL,
        source_type=SourceType.MPLADS_PROJECT_RECORD,
        source_ids=[internal_id],
        internal_project_id=internal_id,
        notes="real MPLADS project records from the cleaned work-level extract.",
        source_dataset="github_vonter_india-mplads-works_MPLADS.csv",
        source_url="https://example.invalid/mplads.csv",
    )


def make_engine_evidence(
    *,
    engine: str,
    engine_version: str,
    signal_type: SignalType,
    project_id: int,
    internal_id: str,
    disposition: EvidenceDisposition,
    finding: str,
    data_mode: DataMode = DataMode.REAL,
    score: float | None = 80,
) -> EvidenceObject:
    source_type = {
        DataMode.REAL: SourceType.MPLADS_PROJECT_RECORD,
        DataMode.HYBRID: SourceType.HYBRID_ENRICHMENT,
        DataMode.SYNTHETIC: SourceType.SYNTHETIC_TEST_RECORD,
    }[data_mode]
    if engine == "geo":
        source_type = SourceType.GEOSPATIAL_RECORD if data_mode == DataMode.REAL else source_type
    if engine == "image" and data_mode == DataMode.REAL:
        source_type = SourceType.IMAGE_ARTIFACT
    provenance = _provenance(data_mode, internal_id)
    if engine in {"geo", "image"} and data_mode == DataMode.REAL:
        provenance = EvidenceProvenance(
            data_mode=DataMode.REAL,
            source_type=source_type,
            source_ids=[internal_id],
            internal_project_id=internal_id,
            notes="real MPLADS project records from the cleaned work-level extract.",
            source_dataset="github_vonter_india-mplads-works_MPLADS.csv",
            source_url="https://example.invalid/mplads.csv",
            enrichment_used=False,
        )
    return EvidenceObject(
        evidence_id=make_evidence_id(
            engine_name=engine,
            engine_version=engine_version,
            project_id=project_id,
            signal_type=signal_type.value,
            data_mode=data_mode.value,
        ),
        project_id=project_id,
        signal_type=signal_type,
        finding=finding,
        severity=EvidenceSeverity.ATTENTION if disposition == EvidenceDisposition.WHY_FLAGGED else EvidenceSeverity.INFO,
        score=score,
        confidence=0.5,
        source_type=source_type,
        source_ids=[internal_id],
        evidence_facts=[make_fact("finding", finding, engine_version)],
        explanation=finding + " This is not a legal finding.",
        engine_name=engine,
        engine_version=engine_version,
        data_mode=data_mode,
        provenance=provenance,
        disposition=disposition,
    )
