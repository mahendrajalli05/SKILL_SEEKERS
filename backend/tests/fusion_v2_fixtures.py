"""Helpers for Risk Fusion V2 tests. Does not invent government evidence."""

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
from fusion_fixtures import make_signal_evidence

_GROUP_META = {
    "cost": (EvidenceEngine.COST, "cost-peer-v1.1", SignalType.ALLOCATION_COST_ANOMALY),
    "time": (EvidenceEngine.TIME, "time-peer-v1", SignalType.TIME_ANOMALY),
    "schedule": (EvidenceEngine.TIME, "time-peer-v1", SignalType.TIME_ANOMALY),
    "overlap": (EvidenceEngine.OVERLAP, "overlap-multi-v1", SignalType.POTENTIAL_OVERLAP),
    "compliance": (EvidenceEngine.COMPLIANCE, "compliance-rules-v1", SignalType.MPLADS_COMPLIANCE),
    "graph": (EvidenceEngine.GRAPH, "relationship-graph-v1", SignalType.RELATIONSHIP_GRAPH),
    "document": (EvidenceEngine.DOCUMENT, "document-blueprint-v1", SignalType.DOCUMENT),
    "image": (EvidenceEngine.IMAGE, "image-evidence-v1", SignalType.IMAGE_POTENTIAL_REUSE),
    "forensics": (EvidenceEngine.FORENSICS, "image-forensics-v1", SignalType.IMAGE_FORENSIC_MANIPULATION),
    "geospatial": (EvidenceEngine.GEO, "geospatial-consistency-v1", SignalType.GEOSPATIAL_LOCATION_MISMATCH),
    "satellite": (EvidenceEngine.SATELLITE, "satellite-remote-sensing-v1", SignalType.SATELLITE_CHANGE),
    "citizen": (EvidenceEngine.CITIZEN, "jan-sakshi-v1", SignalType.CITIZEN_AGGREGATE),
    "milestone": (EvidenceEngine.MILESTONE, "milestone-advisor-v1", SignalType.MILESTONE),
    "pce": (EvidenceEngine.PCE, "plan-claim-evidence-v1", SignalType.PLAN_CLAIM_EVIDENCE),
    "need": (EvidenceEngine.NEED, "need-impact-v1", SignalType.PRIORITY_ASSESSMENT),
}


def _provenance(data_mode: DataMode, internal_id: str = "internal:fusion-v2-test") -> EvidenceProvenance:
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


def make_group_evidence(
    group: str,
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
    signal_type: SignalType | None = None,
    extra_facts: list[EvidenceFact] | None = None,
    peer_quality: int | None = None,
    source_ids: list[str] | None = None,
) -> EvidenceObject:
    if group in {"cost", "schedule", "overlap", "compliance"} and signal_type is None:
        return make_signal_evidence(
            "schedule" if group == "time" else group,
            project_id=project_id,
            score=score,
            confidence=confidence,
            disposition=disposition,
            data_mode=data_mode,
            severity=severity,
            finding=finding,
            explanation=explanation,
            evidence_id=evidence_id,
            extra_facts=extra_facts,
            peer_quality=peer_quality,
        )
    engine, version, default_signal = _GROUP_META[group]
    chosen_signal = signal_type or default_signal
    source_type = {
        DataMode.REAL: SourceType.MPLADS_PROJECT_RECORD,
        DataMode.HYBRID: SourceType.HYBRID_ENRICHMENT,
        DataMode.SYNTHETIC: SourceType.SYNTHETIC_TEST_RECORD,
    }[data_mode]
    internal_id = f"internal:fusion-v2:{project_id}"
    facts = [
        EvidenceFact(key="data_mode", value=data_mode.value, source=version),
    ]
    if peer_quality is not None:
        facts.append(EvidenceFact(key="peer_quality", value=peer_quality, source=version))
    if extra_facts:
        facts.extend(extra_facts)
    if finding is None:
        finding = f"{group} evidence finding"
    if explanation is None:
        explanation = f"{group} evidence explanation based on stored engine output."
    return EvidenceObject(
        evidence_id=evidence_id
        or make_evidence_id(
            engine_name=engine.value,
            engine_version=version,
            project_id=project_id,
            signal_type=chosen_signal.value,
            data_mode=data_mode.value,
        ),
        project_id=project_id,
        signal_type=chosen_signal,
        finding=finding,
        severity=severity,
        score=score,
        confidence=confidence,
        source_type=source_type,
        source_ids=source_ids or [internal_id],
        evidence_facts=facts,
        explanation=explanation,
        engine_name=engine,
        engine_version=version,
        data_mode=data_mode,
        provenance=_provenance(data_mode, internal_id),
        disposition=disposition,
    )


def all_major_groups(
    *,
    project_id: int = 101,
    score: int = 80,
    disposition: EvidenceDisposition = EvidenceDisposition.WHY_FLAGGED,
    data_mode: DataMode = DataMode.REAL,
    confidence: float = 0.80,
) -> list[EvidenceObject]:
    groups = [
        "cost",
        "time",
        "overlap",
        "compliance",
        "graph",
        "document",
        "image",
        "forensics",
        "geospatial",
        "satellite",
        "citizen",
        "milestone",
        "pce",
        "need",
    ]
    items = []
    for group in groups:
        extra = None
        if group == "graph":
            extra = [
                EvidenceFact(key="strongest_relationship", value="IDA", source="relationship-graph-v1"),
                EvidenceFact(key="similar_project_count", value=0, source="relationship-graph-v1"),
                EvidenceFact(key="independent_signal_count", value=2, source="relationship-graph-v1"),
            ]
        if group == "need":
            items.append(
                make_group_evidence(
                    group,
                    project_id=project_id,
                    score=score,
                    confidence=confidence,
                    disposition=EvidenceDisposition.WHY_NOT_FLAGGED,
                    data_mode=data_mode,
                )
            )
            continue
        items.append(
            make_group_evidence(
                group,
                project_id=project_id,
                score=score,
                confidence=confidence,
                disposition=disposition,
                data_mode=data_mode,
                extra_facts=extra,
            )
        )
    return items
