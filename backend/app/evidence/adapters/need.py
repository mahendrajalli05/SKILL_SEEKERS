"""Need & Impact V1 → canonical Evidence Object V1.

Does not change Evidence Object validation or frozen engine scoring.
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
from app.engines.need.constants import ENGINE_NAME, ENGINE_VERSION, INCONCLUSIVE
from app.engines.need.types import NeedImpactResult
from app.evidence.constants import DISPOSITION_TO_STATUS
from app.evidence.facts import make_fact
from app.evidence.ids import make_evidence_id
from app.evidence.provenance import build_provenance, build_source_ids
from app.models.project import Project
from app.models.snapshot import DatasetSnapshot


def _source_type(data_mode: DataMode) -> SourceType:
    if data_mode == DataMode.SYNTHETIC:
        return SourceType.SYNTHETIC_TEST_RECORD
    if data_mode == DataMode.HYBRID:
        return SourceType.HYBRID_ENRICHMENT
    return SourceType.MPLADS_PROJECT_RECORD


def _disposition(priority_class: str) -> EvidenceDisposition:
    if priority_class == INCONCLUSIVE:
        return EvidenceDisposition.INCONCLUSIVE
    return EvidenceDisposition.WHY_NOT_FLAGGED


def _severity(priority_class: str) -> EvidenceSeverity:
    if priority_class == "HIGH PRIORITY":
        return EvidenceSeverity.ATTENTION
    if priority_class == "MEDIUM PRIORITY":
        return EvidenceSeverity.WATCH
    return EvidenceSeverity.INFO


def _dimension_disposition(available: bool) -> EvidenceDisposition:
    if not available:
        return EvidenceDisposition.INCONCLUSIVE
    return EvidenceDisposition.WHY_NOT_FLAGGED


def result_to_evidence_objects(
    project: Project,
    result: NeedImpactResult,
    *,
    snapshot: DatasetSnapshot | None = None,
) -> list[EvidenceObject]:
    source_type = _source_type(result.data_mode)
    extra = []
    if result.enrichment_used:
        extra.append("need-impact:TEST/SYNTHETIC")
    source_ids = build_source_ids(project.internal_project_id, extra)
    extra_notes = (
        "Need & Impact V1 is a priority recommendation only. Authorized officials "
        "make final administrative decisions. Prototype weighting — not an "
        "official MPLADS sanction formula. Historical project counts are not used "
        "as Need Score."
    )
    if result.data_mode != DataMode.REAL:
        extra_notes = (
            f"{extra_notes} TEST/SYNTHETIC need/impact enrichment is labelled and "
            "is not a government fact. Values were not presented as official statistics."
        )
    provenance = build_provenance(
        project,
        data_mode=result.data_mode,
        source_type=source_type,
        source_ids=source_ids,
        snapshot=snapshot,
        extra_notes=extra_notes,
    )
    derived = ENGINE_VERSION
    shared = [
        make_fact("project_id", result.project_id, "project.id", kind=EvidenceFactKind.OBSERVATION),
        make_fact("constituency", result.constituency, "project.constituency"),
        make_fact("observed_category", result.category, "project.category"),
        make_fact("work_description", result.work_description, "project.work_description"),
        make_fact("allocation_amount", result.requested_amount, "project.allocation_amount"),
        make_fact("lifecycle_stage", result.lifecycle_stage, "project.lifecycle_stage"),
        make_fact("data_mode", result.data_mode.value, derived, kind=EvidenceFactKind.OBSERVATION),
        make_fact("priority_class", result.priority_class, derived),
        make_fact("automatic_sanction", False, derived),
        make_fact("weight_note", result.weight_note, derived),
        make_fact("unavailable_inputs", result.unavailable_inputs, derived),
    ]

    objects: list[EvidenceObject] = []
    specs = (
        (
            SignalType.NEED_ASSESSMENT,
            result.need.finding,
            result.need.score,
            result.need.confidence if result.need.available else result.evidence_confidence,
            result.need.explanation,
            _dimension_disposition(result.need.available),
            [
                make_fact("need_score", result.need.score, derived),
                make_fact("need_components", [item.as_dict() for item in result.need.components], derived),
            ],
        ),
        (
            SignalType.IMPACT_ASSESSMENT,
            result.impact.finding,
            result.impact.score,
            result.impact.confidence if result.impact.available else result.evidence_confidence,
            result.impact.explanation,
            _dimension_disposition(result.impact.available),
            [
                make_fact("impact_score", result.impact.score, derived),
                make_fact("impact_components", [item.as_dict() for item in result.impact.components], derived),
            ],
        ),
        (
            SignalType.PRIORITY_ASSESSMENT,
            result.finding,
            result.priority_score,
            result.evidence_confidence,
            result.explanation,
            _disposition(result.priority_class),
            [
                make_fact("priority_score", result.priority_score, derived),
                make_fact("priority_class", result.priority_class, derived),
                make_fact("evidence_confidence", result.evidence_confidence, derived),
                make_fact("weights", result.weights, derived),
                make_fact("top_reasons", result.top_reasons, derived),
            ],
        ),
    )
    for signal, finding, score, confidence, explanation, disposition, extra_facts in specs:
        objects.append(
            EvidenceObject(
                evidence_id=make_evidence_id(
                    engine_name=ENGINE_NAME,
                    engine_version=ENGINE_VERSION,
                    project_id=result.project_id,
                    signal_type=signal.value,
                    data_mode=result.data_mode.value,
                ),
                project_id=result.project_id,
                signal_type=signal,
                finding=finding,
                severity=_severity(result.priority_class),
                score=score,
                confidence=min(1.0, max(0.0, float(confidence))),
                source_type=source_type,
                source_ids=source_ids,
                evidence_facts=shared + extra_facts,
                explanation=explanation,
                engine_name=EvidenceEngine.NEED.value,
                engine_version=ENGINE_VERSION,
                data_mode=result.data_mode,
                provenance=provenance,
                disposition=disposition,
                status=DISPOSITION_TO_STATUS[disposition],
            )
        )
    return objects
