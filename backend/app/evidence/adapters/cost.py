"""Cost Intelligence V1.1 → canonical Evidence Object.

Does not change Cost scoring. Held-out HYBRID labels are not copied.
"""

from __future__ import annotations

from app.domain.enums import (
    DataMode,
    EvidenceDisposition,
    EvidenceEngine,
    EvidenceFactKind,
    SignalType,
    SourceType,
)
from app.domain.schemas.evidence import EvidenceObject
from app.engines.cost.constants import ENGINE_NAME, ENGINE_VERSION
from app.engines.cost.types import CostAssessmentOutcome, CostIntelligenceResult
from app.evidence.constants import DISPOSITION_TO_STATUS
from app.evidence.facts import confidence_unit, format_amount_statement, make_fact
from app.evidence.ids import make_evidence_id
from app.evidence.provenance import build_provenance, build_source_ids, resolve_data_mode
from app.models.project import Project
from app.models.snapshot import DatasetSnapshot


def _disposition(outcome: CostAssessmentOutcome) -> EvidenceDisposition:
    if outcome == CostAssessmentOutcome.COST_ANOMALY:
        return EvidenceDisposition.WHY_FLAGGED
    if outcome == CostAssessmentOutcome.WITHIN_PEER_RANGE:
        return EvidenceDisposition.WHY_NOT_FLAGGED
    if outcome == CostAssessmentOutcome.INVALID_AMOUNT:
        return EvidenceDisposition.NOT_ASSESSABLE
    return EvidenceDisposition.INCONCLUSIVE


def _finding(result: CostIntelligenceResult) -> str:
    if result.outcome == CostAssessmentOutcome.INVALID_AMOUNT:
        return (
            "Allocation Cost Anomaly is not assessable: recorded allocation is "
            "missing, zero, or not a positive value."
        )
    if result.outcome == CostAssessmentOutcome.INSUFFICIENT_EVIDENCE:
        return (
            "Allocation Cost Anomaly is inconclusive: fewer than 5 comparable "
            "works after constituency-first peer selection."
        )
    deviation = result.deviation_percentage
    if deviation is None:
        return "Allocation was compared with peer works."
    if deviation > 0:
        return f"Allocation is {deviation:.1f}% above peer median"
    if deviation < 0:
        return f"Allocation is {abs(deviation):.1f}% below peer median"
    return "Allocation is equal to the peer median"


def cost_result_to_evidence(
    result: CostIntelligenceResult,
    project: Project,
    *,
    snapshot: DatasetSnapshot | None = None,
) -> EvidenceObject:
    data_mode = resolve_data_mode(is_synthetic=bool(project.is_synthetic))
    source_type = (
        SourceType.SYNTHETIC_TEST_RECORD
        if data_mode == DataMode.SYNTHETIC
        else SourceType.MPLADS_PROJECT_RECORD
    )
    extra_ids = [f"project:{pid}" for pid in result.peer_project_ids]
    source_ids = build_source_ids(result.internal_project_id, extra_ids)
    provenance = build_provenance(
        project,
        data_mode=data_mode,
        source_type=source_type,
        source_ids=source_ids,
        snapshot=snapshot,
    )
    derived = ENGINE_VERSION
    facts = [
        make_fact(
            "actual_amount",
            result.actual_amount,
            "project.allocation_amount",
            kind=EvidenceFactKind.OBSERVATION,
            statement=format_amount_statement(result.actual_amount),
        ),
        make_fact("observed_category", result.observed_category, "project.category"),
        make_fact("constituency", result.constituency, "project.constituency"),
        make_fact("derived_work_type", result.derived_work_type, "derived from project.work_description"),
        make_fact("signal_kind", result.signal_kind, derived),
        make_fact("peer_scope", result.peer_scope, derived),
        make_fact("peer_scope_label", result.peer_scope_label, derived),
        make_fact("peer_count", result.peer_count, derived),
        make_fact("peer_quality", result.peer_quality, derived),
        make_fact("similarity_rationale", result.similarity_rationale, derived),
        make_fact("baseline", result.baseline, derived),
        make_fact("deviation_percentage", result.deviation_percentage, derived),
        make_fact("cost_anomaly_score", result.cost_anomaly_score, derived),
        make_fact("score_method", result.score_method, derived),
        make_fact("evidence_confidence", result.evidence_confidence, derived),
        make_fact(
            "expected_range",
            {"low": result.expected_range_low, "high": result.expected_range_high},
            derived,
        ),
        make_fact("flagged", result.flagged, derived),
        make_fact("outcome", result.outcome.value, derived),
        make_fact("why_flagged", result.why_flagged, derived),
        make_fact("why_not_flagged", result.why_not_flagged, derived),
        make_fact("peer_project_ids", result.peer_project_ids, derived),
        make_fact("mad", result.mad, derived),
        make_fact("log_mad", result.log_mad, derived),
        make_fact("percentile_25", result.percentile_25, derived),
        make_fact("percentile_75", result.percentile_75, derived),
        make_fact("constituency_kind", result.constituency_kind, derived),
        make_fact("constituency_usable", result.constituency_usable, derived),
        make_fact(
            "constituency_exclusion_reason",
            result.constituency_exclusion_reason,
            derived,
        ),
        make_fact("amount_unit_note", result.amount_unit_note, derived),
        make_fact("data_mode", data_mode.value, derived),
    ]
    comparables = [
        {
            "project_id": item.project_id,
            "internal_project_id": item.internal_project_id,
            "constituency": item.constituency,
            "category": item.category,
            "derived_work_type": item.derived_work_type,
            "allocation_amount": item.allocation_amount,
            "work_type_similarity": item.work_type_similarity,
            "recommended_date": (
                item.recommended_date.isoformat() if item.recommended_date else None
            ),
        }
        for item in result.comparable_projects
    ]
    disposition = _disposition(result.outcome)
    return EvidenceObject(
        evidence_id=make_evidence_id(
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            project_id=result.project_id,
            signal_type=result.signal_kind,
            data_mode=data_mode.value,
        ),
        project_id=result.project_id,
        signal_type=SignalType.ALLOCATION_COST_ANOMALY,
        finding=_finding(result),
        severity=result.severity,
        score=result.cost_anomaly_score,
        confidence=confidence_unit(result.evidence_confidence),
        source_type=source_type,
        source_ids=source_ids,
        evidence_facts=facts,
        explanation=result.explanation,
        engine_name=EvidenceEngine.COST,
        engine_version=ENGINE_VERSION,
        data_mode=data_mode,
        provenance=provenance,
        disposition=disposition,
        status=DISPOSITION_TO_STATUS[disposition],
        comparables=comparables,
    )
