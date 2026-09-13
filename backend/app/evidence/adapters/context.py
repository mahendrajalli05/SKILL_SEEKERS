"""Contextual observations → Evidence Object V1.

Does not create a second evidence architecture. Does not claim fraud.
"""

from __future__ import annotations

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
from app.engines.context.constants import (
    ENGINE_NAME,
    ENGINE_VERSION,
    INDICATOR_INFRASTRUCTURE,
    INDICATOR_REFERENCE_COST,
    INDICATOR_STATE_POPULATION,
    KIND_DERIVED_CONTEXT,
    KIND_OBSERVED_EXTERNAL,
    KIND_PROJECT_FACT,
    STATUS_AVAILABLE,
    STATUS_INCONCLUSIVE,
)
from app.engines.context.explain import explain_observation, explain_result
from app.engines.context.types import ContextObservation, ContextResult
from app.evidence.constants import DISPOSITION_TO_STATUS
from app.evidence.facts import make_fact
from app.evidence.ids import make_evidence_id
from app.evidence.provenance import build_provenance, build_source_ids
from app.models.project import Project


def _source_type(item: ContextObservation, data_mode: DataMode) -> SourceType:
    if data_mode == DataMode.SYNTHETIC:
        return SourceType.SYNTHETIC_TEST_RECORD
    if data_mode == DataMode.HYBRID:
        return SourceType.HYBRID_ENRICHMENT
    if item.context_kind == KIND_PROJECT_FACT:
        return SourceType.MPLADS_PROJECT_RECORD
    return SourceType.EXTERNAL_PUBLIC_DATASET


def _disposition(items: list[ContextObservation]) -> EvidenceDisposition:
    if any(item.status == STATUS_AVAILABLE for item in items):
        return EvidenceDisposition.WHY_NOT_FLAGGED
    if any(item.status == STATUS_INCONCLUSIVE for item in items):
        return EvidenceDisposition.INCONCLUSIVE
    return EvidenceDisposition.NOT_ASSESSABLE


def _facts(items: list[ContextObservation], derived: str) -> list:
    facts = []
    for item in items:
        kind = EvidenceFactKind.OBSERVATION
        if item.context_kind == KIND_DERIVED_CONTEXT or item.derived:
            kind = EvidenceFactKind.DERIVED
        source = item.source_url or item.source_id or derived
        facts.extend(
            [
                make_fact("indicator", item.indicator, source, kind=kind),
                make_fact("status", item.status, source, kind=kind),
                make_fact("value", item.value, source, kind=kind),
                make_fact("unit", item.unit, source, kind=kind),
                make_fact("geographic_level", item.geographic_level, source, kind=kind),
                make_fact("geo_key", item.geo_key, source, kind=kind),
                make_fact("reference_year", item.reference_year, source, kind=kind),
                make_fact("context_kind", item.context_kind, derived, kind=EvidenceFactKind.DERIVED),
                make_fact("data_mode", item.data_mode.value, derived, kind=EvidenceFactKind.OBSERVATION),
                make_fact("limitations", item.limitations, source, kind=EvidenceFactKind.DERIVED),
            ]
        )
        if item.comparison:
            facts.append(make_fact("comparison", item.comparison, derived, kind=EvidenceFactKind.DERIVED))
    return facts


def _object(
    project: Project,
    result: ContextResult,
    *,
    signal: SignalType,
    items: list[ContextObservation],
    finding: str,
) -> EvidenceObject | None:
    if not items:
        return None
    representative = items[0]
    for item in items:
        if item.status == STATUS_AVAILABLE and item.context_kind == KIND_OBSERVED_EXTERNAL:
            representative = item
            break
    data_mode = representative.data_mode
    if any(item.data_mode == DataMode.SYNTHETIC for item in items) or project.is_synthetic:
        data_mode = DataMode.SYNTHETIC
    elif any(item.data_mode == DataMode.HYBRID for item in items):
        data_mode = DataMode.HYBRID
    source_type = _source_type(representative, data_mode)
    extra = [representative.source_id] if representative.source_id else []
    if representative.source_url:
        extra.append(representative.source_url)
    source_ids = build_source_ids(project.internal_project_id, extra)
    extra_notes = (
        f"{explain_result(result)} Signal {signal.value}. "
        f"Publisher: {representative.publisher or 'unspecified'}. "
        f"Retrieval date: {representative.retrieval_date or 'unspecified'}."
    )
    if data_mode == DataMode.HYBRID:
        extra_notes += " HYBRID/TEST contextual fixture used where labelled. Not official MPLADS."
    provenance = build_provenance(
        project,
        data_mode=data_mode,
        source_type=source_type,
        source_ids=source_ids,
        extra_notes=extra_notes,
    )
    if representative.source_url and not provenance.source_url:
        provenance.source_url = representative.source_url
    if representative.publisher and not provenance.publisher:
        provenance.publisher = representative.publisher
    if representative.source_name:
        provenance.source_dataset = provenance.source_dataset or representative.source_name
    disposition = _disposition(items)
    explanation = " ".join(explain_observation(item) for item in items)
    return EvidenceObject(
        evidence_id=make_evidence_id(
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            project_id=project.id,
            signal_type=signal.value,
            data_mode=data_mode.value,
        ),
        project_id=project.id,
        signal_type=signal,
        finding=finding[:500],
        severity=EvidenceSeverity.INFO,
        score=None,
        confidence=max(item.confidence for item in items),
        source_type=source_type,
        source_ids=source_ids,
        evidence_facts=_facts(items, ENGINE_VERSION),
        explanation=explanation[:8000],
        engine_name=EvidenceEngine.CONTEXT.value,
        engine_version=ENGINE_VERSION,
        data_mode=data_mode,
        provenance=provenance,
        disposition=disposition,
        status=DISPOSITION_TO_STATUS[disposition],
    )


def result_to_evidence_objects(project: Project, result: ContextResult) -> list[EvidenceObject]:
    by_family: dict[SignalType, list[ContextObservation]] = {
        SignalType.DEVELOPMENT_NEED_CONTEXT: [],
        SignalType.INFRASTRUCTURE_CONTEXT: [],
        SignalType.REFERENCE_COST_CONTEXT: [],
        SignalType.CONTEXT_UNAVAILABLE: [],
        SignalType.CONTEXT_INCONCLUSIVE: [],
    }
    for item in result.observations:
        if item.indicator == INDICATOR_STATE_POPULATION:
            by_family[SignalType.DEVELOPMENT_NEED_CONTEXT].append(item)
        elif item.indicator in {
            INDICATOR_INFRASTRUCTURE,
            "household_electricity_pct",
            "improved_drinking_water_pct",
            "improved_sanitation_pct",
            "district_population",
        }:
            by_family[SignalType.INFRASTRUCTURE_CONTEXT].append(item)
        elif item.indicator in {
            "mplads_allocation",
            "mplads_expenditure",
            INDICATOR_REFERENCE_COST,
            "reference_unit_rate_hybrid_fixture",
            "allocation_vs_reference_rate",
            f"{INDICATOR_REFERENCE_COST}:ap_pwd_schedule_of_rates",
        } or (item.indicator or "").startswith(INDICATOR_REFERENCE_COST):
            by_family[SignalType.REFERENCE_COST_CONTEXT].append(item)
        elif item.status == STATUS_INCONCLUSIVE:
            by_family[SignalType.CONTEXT_INCONCLUSIVE].append(item)
        else:
            by_family[SignalType.CONTEXT_UNAVAILABLE].append(item)

    findings = {
        SignalType.DEVELOPMENT_NEED_CONTEXT: "DEVELOPMENT_NEED_CONTEXT: state-level external population context. Not a project beneficiary count.",
        SignalType.INFRASTRUCTURE_CONTEXT: "INFRASTRUCTURE_CONTEXT: verified structured infrastructure indicators are unavailable. Values were not invented.",
        SignalType.REFERENCE_COST_CONTEXT: "REFERENCE_COST_CONTEXT: allocation is a project observation; official unit rates are unavailable or test-labelled; comparison is INCONCLUSIVE when units differ.",
        SignalType.CONTEXT_UNAVAILABLE: "CONTEXT_UNAVAILABLE: requested contextual indicator is not available.",
        SignalType.CONTEXT_INCONCLUSIVE: "CONTEXT_INCONCLUSIVE: contextual indicator cannot be matched without fabricating geography or time equivalence.",
    }
    objects: list[EvidenceObject] = []
    for signal, items in by_family.items():
        obj = _object(project, result, signal=signal, items=items, finding=findings[signal])
        if obj is not None:
            objects.append(obj)
    return objects
