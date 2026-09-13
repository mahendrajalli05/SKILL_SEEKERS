"""Helpers for Risk Fusion V1 tests."""

from __future__ import annotations

from app.domain.enums import (
    DataMode,
    EvidenceDisposition,
    EvidenceEngine,
    EvidenceSeverity,
    SignalType,
    SourceType,
)
from app.domain.schemas.evidence import EvidenceFact, EvidenceObject, EvidenceProvenance
from app.evidence.ids import make_evidence_id

_SIGNAL_META = {
    "cost": (EvidenceEngine.COST, "cost-peer-v1.1", SignalType.ALLOCATION_COST_ANOMALY),
    "schedule": (EvidenceEngine.TIME, "time-peer-v1", SignalType.TIME_ANOMALY),
    "overlap": (EvidenceEngine.OVERLAP, "overlap-multi-v1", SignalType.POTENTIAL_OVERLAP),
    "compliance": (EvidenceEngine.COMPLIANCE, "compliance-rules-v1", SignalType.MPLADS_COMPLIANCE),
}


def _provenance(data_mode: DataMode, internal_id: str = "internal:fusion-test") -> EvidenceProvenance:
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


def make_signal_evidence(
    slot: str,
    *,
    project_id: int = 101,
    score: float | None = 20,
    confidence: float = 0.70,
    disposition: EvidenceDisposition = EvidenceDisposition.WHY_NOT_FLAGGED,
    data_mode: DataMode = DataMode.REAL,
    severity: EvidenceSeverity = EvidenceSeverity.INFO,
    finding: str | None = None,
    explanation: str | None = None,
    evidence_id: str | None = None,
    rule_ids: list[str] | None = None,
    extra_facts: list[EvidenceFact] | None = None,
    peer_quality: int | None = None,
) -> EvidenceObject:
    if isinstance(severity, str):
        severity = EvidenceSeverity(severity)
    engine, version, signal_type = _SIGNAL_META[slot]
    source_type = {
        DataMode.REAL: SourceType.MPLADS_PROJECT_RECORD,
        DataMode.HYBRID: SourceType.HYBRID_ENRICHMENT,
        DataMode.SYNTHETIC: SourceType.SYNTHETIC_TEST_RECORD,
    }[data_mode]
    internal_id = f"internal:fusion:{project_id}"
    facts = [
        EvidenceFact(
            key="data_mode",
            value=data_mode.value,
            source=version,
        )
    ]
    if peer_quality is not None:
        facts.append(
            EvidenceFact(
                key="peer_quality",
                value=peer_quality,
                source=version,
            )
        )
    if extra_facts:
        facts.extend(extra_facts)
    if finding is None:
        finding = f"{slot} evidence finding"
    if explanation is None:
        explanation = f"{slot} evidence explanation based on stored engine output."
    return EvidenceObject(
        evidence_id=evidence_id
        or make_evidence_id(
            engine_name=engine.value,
            engine_version=version,
            project_id=project_id,
            signal_type=signal_type.value,
            data_mode=data_mode.value,
        ),
        project_id=project_id,
        signal_type=signal_type,
        finding=finding,
        severity=severity,
        score=score,
        confidence=confidence,
        source_type=source_type,
        source_ids=[internal_id],
        evidence_facts=facts,
        explanation=explanation,
        engine_name=engine,
        engine_version=version,
        data_mode=data_mode,
        provenance=_provenance(data_mode, internal_id),
        disposition=disposition,
        rule_ids=rule_ids or [],
    )
