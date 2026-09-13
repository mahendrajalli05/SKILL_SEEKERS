"""Controlled fixtures for Investigation Copilot V1 tests."""

from __future__ import annotations

from datetime import date

from app.domain.enums import (
    DataMode,
    EvidenceDisposition,
    EvidenceSeverity,
    SignalType,
    SourceType,
)
from app.domain.schemas.evidence import EvidenceFact, EvidenceObject, EvidenceProvenance
from app.evidence.ids import make_evidence_id
from app.models.project import Project

SYNTHETIC_LABEL = "SYNTHETIC: investigation-copilot unit test (not a government project)"


def insert_project(session, **overrides: object) -> Project:
    values: dict[str, object] = {
        "internal_project_id": "internal:synthetic:copilot:subject",
        "internal_id_kind": "internal_surrogate_hash",
        "internal_id_scheme": "sarvsakshi_internal_work_v1",
        "source_dataset": "github_vonter_india-mplads-works_MPLADS.csv",
        "is_synthetic": True,
        "synthetic_label": SYNTHETIC_LABEL,
        "lifecycle_stage": "FUTURE",
        "state": "Andhra Pradesh",
        "constituency": "KURNOOL",
        "category": "Normal/Others",
        "work_description": "NA - Construction of water tanks",
        "allocation_amount": 500_000,
        "recommended_date": date(2023, 6, 1),
        "status": "Unsanctioned",
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
            notes="HYBRID/TEST: observed MPLADS fields plus synthetic enrichment.",
            enrichment_used=True,
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
    )


def make_engine_evidence(
    engine: str,
    signal: SignalType,
    *,
    project_id: int,
    data_mode: DataMode = DataMode.SYNTHETIC,
    disposition: EvidenceDisposition = EvidenceDisposition.WHY_NOT_FLAGGED,
    score: float | None = 20,
    finding: str = "Stored engine finding.",
    explanation: str = "Stored engine explanation.",
    comparables: list | None = None,
    rule_ids: list[str] | None = None,
    extra_facts: list[EvidenceFact] | None = None,
) -> EvidenceObject:
    source_type = {
        DataMode.REAL: SourceType.MPLADS_PROJECT_RECORD,
        DataMode.HYBRID: SourceType.HYBRID_ENRICHMENT,
        DataMode.SYNTHETIC: SourceType.SYNTHETIC_TEST_RECORD,
    }[data_mode]
    internal_id = f"internal:copilot:{project_id}"
    version = f"{engine}-v1-test"
    return EvidenceObject(
        evidence_id=make_evidence_id(
            engine_name=engine,
            engine_version=version,
            project_id=project_id,
            signal_type=signal.value,
            data_mode=data_mode.value,
        ),
        project_id=project_id,
        signal_type=signal,
        finding=finding,
        severity=EvidenceSeverity.WATCH if disposition == EvidenceDisposition.WHY_FLAGGED else EvidenceSeverity.INFO,
        score=score,
        confidence=0.7,
        source_type=source_type,
        source_ids=[internal_id],
        evidence_facts=extra_facts
        or [
            EvidenceFact(key="data_mode", value=data_mode.value, source=version),
        ],
        explanation=explanation,
        engine_name=engine,
        engine_version=version,
        data_mode=data_mode,
        provenance=_provenance(data_mode, internal_id),
        disposition=disposition,
        comparables=comparables or [],
        rule_ids=rule_ids or [],
        guideline_refs=rule_ids or [],
    )


def flagged_cost(project_id: int, data_mode: DataMode = DataMode.SYNTHETIC) -> EvidenceObject:
    from fusion_fixtures import make_signal_evidence

    return make_signal_evidence(
        "cost",
        project_id=project_id,
        score=67,
        disposition=EvidenceDisposition.WHY_FLAGGED,
        data_mode=data_mode,
        finding="Allocation Cost Anomaly is elevated versus peers.",
        explanation="WHY FLAGGED: allocation is above the peer median.",
    ).model_copy(
        update={
            "comparables": [
                {
                    "project_id": 88,
                    "internal_project_id": "internal:synthetic:copilot:peer",
                    "allocation_amount": 210000,
                    "constituency": "KURNOOL",
                }
            ]
        }
    )


def flagged_overlap(project_id: int, data_mode: DataMode = DataMode.SYNTHETIC) -> EvidenceObject:
    from fusion_fixtures import make_signal_evidence

    return make_signal_evidence(
        "overlap",
        project_id=project_id,
        score=81,
        disposition=EvidenceDisposition.WHY_FLAGGED,
        data_mode=data_mode,
        finding="Potential overlap with another stored work.",
        explanation="WHY FLAGGED: multi-signal similarity is above the review threshold.",
    ).model_copy(
        update={
            "comparables": [
                {
                    "linked_project_id": 89,
                    "linked_internal_project_id": "internal:synthetic:copilot:overlap",
                    "overall_overlap_score": 81,
                }
            ]
        }
    )
