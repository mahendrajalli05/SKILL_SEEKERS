"""Time Intelligence V1 → canonical Evidence Object.

Does not change Time scoring. Scenario labels are not copied.
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
from app.engines.time.constants import ENGINE_NAME, ENGINE_VERSION, SIGNAL_KIND
from app.engines.time.types import TimeAssessmentOutcome, TimeIntelligenceResult, TimeMode
from app.evidence.constants import DISPOSITION_TO_STATUS
from app.evidence.facts import confidence_unit, make_fact
from app.evidence.ids import make_evidence_id
from app.evidence.provenance import build_provenance, build_source_ids, resolve_data_mode
from app.models.project import Project
from app.models.snapshot import DatasetSnapshot


def _date_source(data_mode: DataMode) -> str:
    if data_mode == DataMode.HYBRID:
        return "hybrid_enrichment"
    if data_mode == DataMode.SYNTHETIC:
        return "synthetic_test_record"
    return ENGINE_VERSION


def _disposition(result: TimeIntelligenceResult) -> EvidenceDisposition:
    if result.outcome == TimeAssessmentOutcome.TIME_ANOMALY:
        return EvidenceDisposition.WHY_FLAGGED
    if result.outcome == TimeAssessmentOutcome.WITHIN_SCHEDULE:
        return EvidenceDisposition.WHY_NOT_FLAGGED
    if result.outcome == TimeAssessmentOutcome.INVALID_DATES:
        return EvidenceDisposition.NOT_ASSESSABLE
    if result.time_mode == TimeMode.REAL:
        return EvidenceDisposition.NOT_ASSESSABLE
    return EvidenceDisposition.INCONCLUSIVE


def _finding(result: TimeIntelligenceResult) -> str:
    if result.outcome == TimeAssessmentOutcome.INVALID_DATES:
        return "Time Anomaly is not assessable: planned or actual dates are internally inconsistent."
    if result.outcome == TimeAssessmentOutcome.INSUFFICIENT_EVIDENCE:
        if result.time_mode == TimeMode.REAL:
            return (
                "Time Anomaly is not assessable: the real extract has recommendation "
                "date and status only. Execution duration is not fabricated."
            )
        return "Time Anomaly is inconclusive: sufficient timing evidence is not available."
    if result.outcome == TimeAssessmentOutcome.TIME_ANOMALY:
        if result.time_consumed_percent is not None and result.physical_progress_percent is not None:
            return (
                f"Schedule is behind plan: {result.time_consumed_percent:.1f}% of planned "
                f"time consumed versus {result.physical_progress_percent}% physical progress"
            )
        if result.slippage_days is not None:
            return f"Schedule slippage of {result.slippage_days} days versus the planned duration"
        return "Time Anomaly is above the review flag versus the available plan and peers"
    return "Schedule is within the mapped review flag versus the available plan"


def time_result_to_evidence(
    result: TimeIntelligenceResult,
    project: Project,
    *,
    snapshot: DatasetSnapshot | None = None,
) -> EvidenceObject:
    data_mode = resolve_data_mode(
        is_synthetic=bool(project.is_synthetic),
        engine_mode=result.time_mode.value,
    )
    source_type = (
        SourceType.SYNTHETIC_TEST_RECORD
        if data_mode == DataMode.SYNTHETIC
        else SourceType.HYBRID_ENRICHMENT
        if data_mode == DataMode.HYBRID
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
    date_source = _date_source(data_mode)
    facts = [
        make_fact("observed_status", result.observed_status, "project.status"),
        make_fact("lifecycle_stage", result.lifecycle_stage, "project.lifecycle_stage"),
        make_fact(
            "recommended_date",
            result.recommended_date.isoformat() if result.recommended_date else None,
            "project.recommended_date",
        ),
        make_fact("observed_category", result.observed_category, "project.category"),
        make_fact("constituency", result.constituency, "project.constituency"),
        make_fact("planned_duration_days", result.planned_duration_days, date_source),
        make_fact("actual_duration_days", result.actual_duration_days, date_source),
        make_fact("elapsed_duration_days", result.elapsed_duration_days, date_source),
        make_fact("physical_progress_percent", result.physical_progress_percent, date_source),
        make_fact("dataset_type", result.dataset_type, derived),
        make_fact("time_mode", result.time_mode.value, derived),
        make_fact("signal_kind", result.signal_kind, derived),
        make_fact("peer_scope", result.peer_scope, derived),
        make_fact("peer_scope_label", result.peer_scope_label, derived),
        make_fact("peer_count", result.peer_count, derived),
        make_fact("peer_quality", result.peer_quality, derived),
        make_fact("slippage_days", result.slippage_days, derived),
        make_fact("time_consumed_percent", result.time_consumed_percent, derived),
        make_fact("time_anomaly_score", result.time_anomaly_score, derived),
        make_fact("evidence_confidence", result.evidence_confidence, derived),
        make_fact("flagged", result.flagged, derived),
        make_fact("outcome", result.outcome.value, derived),
        make_fact("why_flagged", result.why_flagged, derived),
        make_fact("why_not_flagged", result.why_not_flagged, derived),
        make_fact("delay_detected", result.delay_detected, derived),
        make_fact("delay_context_note", result.delay_context_note, derived),
        make_fact("recommendation_age_days", result.recommendation_age_days, derived),
        make_fact("score_method", result.score_method, derived),
        make_fact("schedule_family", result.schedule_family, derived),
        make_fact("data_mode", data_mode.value, derived),
    ]
    comparables = [
        {
            "project_id": item.project_id,
            "internal_project_id": item.internal_project_id,
            "constituency": item.constituency,
            "category": item.category,
            "derived_work_type": item.derived_work_type,
            "status": item.status,
            "planned_duration_days": item.planned_duration_days,
            "actual_duration_days": item.actual_duration_days,
            "work_type_similarity": item.work_type_similarity,
        }
        for item in result.comparable_projects
    ]
    disposition = _disposition(result)
    return EvidenceObject(
        evidence_id=make_evidence_id(
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            project_id=result.project_id,
            signal_type=SIGNAL_KIND,
            data_mode=data_mode.value,
        ),
        project_id=result.project_id,
        signal_type=SignalType.TIME_ANOMALY,
        finding=_finding(result),
        severity=result.severity,
        score=result.time_anomaly_score,
        confidence=confidence_unit(result.evidence_confidence),
        source_type=source_type,
        source_ids=source_ids,
        evidence_facts=facts,
        explanation=result.explanation,
        engine_name=EvidenceEngine.TIME,
        engine_version=ENGINE_VERSION,
        data_mode=data_mode,
        provenance=provenance,
        disposition=disposition,
        status=DISPOSITION_TO_STATUS[disposition],
        comparables=comparables,
    )
