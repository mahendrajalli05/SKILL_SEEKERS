"""Time Intelligence V1 orchestration.

REAL mode uses observed recommendation date + status only.
HYBRID_TEST uses synthetic dates/progress for controlled testing.
Does not run cost, overlap, compliance, or risk fusion.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.domain.enums import EvidenceEngine, EvidenceSeverity, EvidenceStatus
from app.engines.cost.geography import classify_constituency
from app.engines.cost.work_type import work_type_similarity
from app.engines.time.constants import (
    ENGINE_NAME,
    ENGINE_VERSION,
    EVIDENCE_TYPE,
    MAX_DISPLAY_COMPARABLES,
    MIN_PEER_COUNT,
    REAL_OBSERVATION_DATE,
)
from app.engines.time.context import delay_context
from app.engines.time.dates import duration_days
from app.engines.time.enrichment import HybridSchedule, load_hybrid_schedules
from app.engines.time.explain import explanation_for
from app.engines.time.peers import InMemoryTimePeerSource, TimePeerSource, select_peers
from app.engines.time.quality import compute_peer_quality
from app.engines.time.repository import (
    SqlTimePeerSource,
    observation_date_from_session,
    project_to_time_record,
)
from app.engines.time.schedule import compute_schedule_metrics
from app.engines.time.scoring import (
    closed_time_score,
    evidence_confidence as compute_evidence_confidence,
    is_time_anomaly,
    open_time_score,
)
from app.engines.time.types import (
    ComparableProject,
    PeerQuality,
    PeerSelection,
    ScheduleFamily,
    TimeAssessmentOutcome,
    TimeIntelligenceResult,
    TimeMode,
    TimePeerRecord,
    TimeSignalKind,
)
from app.models.evidence import EvidenceObjectRow
from app.models.project import Project


def _empty_quality() -> PeerQuality:
    return PeerQuality(
        score=0,
        rationale="No sufficient peer group was selected, so peer quality is 0.",
        median_work_type_similarity=0.0,
        category_match_rate=0.0,
    )


def rank_comparables(
    subject: TimePeerRecord,
    peers: tuple[TimePeerRecord, ...],
    *,
    limit: int = MAX_DISPLAY_COMPARABLES,
) -> list[ComparableProject]:
    subject_planned = duration_days(subject.planned_start_date, subject.planned_completion_date) or 0
    ranked: list[tuple[tuple[float, int, int], TimePeerRecord, float]] = []
    for peer in peers:
        similarity = work_type_similarity(subject.work_description, peer.work_description)
        planned = duration_days(peer.planned_start_date, peer.planned_completion_date) or 0
        key = (-similarity, abs(planned - subject_planned), peer.project_id)
        ranked.append((key, peer, similarity))
    ranked.sort(key=lambda item: item[0])
    comparables: list[ComparableProject] = []
    for _key, peer, similarity in ranked[:limit]:
        comparables.append(
            ComparableProject(
                project_id=peer.project_id,
                internal_project_id=peer.internal_project_id,
                constituency=peer.constituency,
                category=peer.category,
                derived_work_type=peer.derived_work_type,
                status=peer.status,
                planned_duration_days=duration_days(
                    peer.planned_start_date, peer.planned_completion_date
                ),
                actual_duration_days=duration_days(
                    peer.actual_start_date, peer.actual_completion_date
                ),
                elapsed_duration_days=duration_days(peer.actual_start_date or peer.planned_start_date, peer.as_of_date),
                physical_progress_percent=peer.physical_progress_percent,
                work_type_similarity=round(similarity, 3),
                recommended_date=peer.recommended_date,
            )
        )
    return comparables


def _dataset_type(mode: TimeMode) -> str:
    return "HYBRID" if mode == TimeMode.HYBRID_TEST else "REAL"


def _base_result(
    subject: TimePeerRecord,
    *,
    outcome: TimeAssessmentOutcome,
    flagged: bool,
    status: EvidenceStatus,
    severity: EvidenceSeverity,
    signal_kind: TimeSignalKind,
    selection: PeerSelection | None,
    quality: PeerQuality,
    metrics,
    score: int | None,
    confidence: int,
    explanation: str,
    why_flagged: str | None,
    why_not_flagged: str | None,
    delay_ctx,
    score_method: str | None,
    peer_median_duration_days: float | None,
) -> TimeIntelligenceResult:
    selection = selection or PeerSelection(
        scope=None,
        peers=(),
        attempted_scopes=(),
    )
    classification = classify_constituency(subject.constituency)
    return TimeIntelligenceResult(
        project_id=subject.project_id,
        internal_project_id=subject.internal_project_id,
        engine=ENGINE_NAME,
        engine_version=ENGINE_VERSION,
        evidence_type=EVIDENCE_TYPE,
        dataset_type=_dataset_type(subject.time_mode),
        time_mode=subject.time_mode,
        outcome=outcome,
        flagged=flagged,
        status=status,
        severity=severity,
        signal_kind=signal_kind.value,
        peer_scope=selection.scope.id if selection.scope else None,
        peer_scope_label=selection.scope.label if selection.scope else None,
        peer_count=selection.peer_count,
        peer_quality=quality.score,
        similarity_rationale=quality.rationale,
        median_work_type_similarity=quality.median_work_type_similarity,
        observed_status=subject.status,
        lifecycle_stage=subject.lifecycle_stage,
        recommended_date=subject.recommended_date,
        observation_date=subject.observation_date or REAL_OBSERVATION_DATE,
        recommendation_age_days=metrics.recommendation_age_days,
        planned_start_date=subject.planned_start_date,
        planned_completion_date=subject.planned_completion_date,
        actual_start_date=subject.actual_start_date,
        actual_completion_date=subject.actual_completion_date,
        planned_duration_days=metrics.planned_duration_days,
        actual_duration_days=metrics.actual_duration_days,
        elapsed_duration_days=metrics.elapsed_duration_days,
        slippage_days=metrics.slippage_days,
        physical_progress_percent=metrics.physical_progress_percent,
        expected_progress_percent=metrics.expected_progress_percent,
        time_consumed_percent=metrics.time_consumed_percent,
        progress_mismatch_points=metrics.progress_mismatch_points,
        peer_median_duration_days=peer_median_duration_days,
        time_anomaly_score=score,
        evidence_confidence=confidence,
        explanation=explanation,
        why_flagged=why_flagged,
        why_not_flagged=why_not_flagged,
        delay_detected=delay_ctx.delay_detected,
        cause_established=delay_ctx.cause_established,
        delay_context_note=delay_ctx.context_note,
        comparable_projects=rank_comparables(subject, selection.peers) if selection.peers else [],
        peer_project_ids=[peer.project_id for peer in selection.peers],
        derived_work_type=subject.derived_work_type,
        observed_category=subject.category,
        constituency=subject.constituency,
        attempted_scopes=selection.attempted_scopes,
        best_attempt_peer_count=selection.best_attempt_peer_count,
        constituency_kind=selection.constituency_kind or classification.kind.value,
        constituency_usable=selection.constituency_usable,
        constituency_exclusion_reason=selection.constituency_exclusion_reason,
        score_method=score_method,
        schedule_family=metrics.family.value,
        date_issues=metrics.date_issues,
        as_of_date=metrics.as_of_date,
    )


def assess_time(
    subject: TimePeerRecord,
    source: TimePeerSource,
    *,
    min_peer_count: int = MIN_PEER_COUNT,
) -> TimeIntelligenceResult:
    """Pure assessment. Does not write to the database."""
    metrics = compute_schedule_metrics(subject)
    selection = select_peers(subject, source, min_peer_count=min_peer_count)
    quality = (
        compute_peer_quality(subject, selection.peers, selection.scope)
        if selection.sufficient
        else _empty_quality()
    )

    if subject.time_mode == TimeMode.REAL:
        confidence = compute_evidence_confidence(
            time_mode=TimeMode.REAL,
            valid_dates=True,
            sufficient_timing_evidence=False,
            has_recommended_date=subject.recommended_date is not None,
            scope_id=selection.scope.id if selection.scope else None,
            peer_count=selection.peer_count,
            peer_quality=quality.score,
            has_planned_dates=False,
            has_actual_dates=False,
            has_progress=False,
        )
        ctx = delay_context(delay_detected=False)
        text, why_flagged, why_not = explanation_for(
            TimeAssessmentOutcome.INSUFFICIENT_EVIDENCE,
            time_mode=TimeMode.REAL,
            recommended_date=subject.recommended_date,
            observation_date=subject.observation_date or REAL_OBSERVATION_DATE,
            recommendation_age_days=metrics.recommendation_age_days,
            observed_status=subject.status,
            evidence_confidence=confidence,
            peer_count=selection.peer_count,
            peer_scope_label=selection.scope.label if selection.scope else None,
            constituency_exclusion_reason=selection.constituency_exclusion_reason,
        )
        return _base_result(
            subject,
            outcome=TimeAssessmentOutcome.INSUFFICIENT_EVIDENCE,
            flagged=False,
            status=EvidenceStatus.INCONCLUSIVE,
            severity=EvidenceSeverity.INFO,
            signal_kind=TimeSignalKind.INSUFFICIENT_EXECUTION_TIMING,
            selection=selection,
            quality=quality,
            metrics=metrics,
            score=None,
            confidence=confidence,
            explanation=text,
            why_flagged=why_flagged,
            why_not_flagged=why_not,
            delay_ctx=ctx,
            score_method=None,
            peer_median_duration_days=None,
        )

    if metrics.family == ScheduleFamily.INVALID:
        confidence = compute_evidence_confidence(
            time_mode=TimeMode.HYBRID_TEST,
            valid_dates=False,
            sufficient_timing_evidence=False,
            has_recommended_date=subject.recommended_date is not None,
            scope_id=None,
            peer_count=0,
            peer_quality=0,
            has_planned_dates=False,
            has_actual_dates=False,
            has_progress=False,
        )
        ctx = delay_context(delay_detected=False)
        text, why_flagged, why_not = explanation_for(
            TimeAssessmentOutcome.INVALID_DATES,
            time_mode=TimeMode.HYBRID_TEST,
            date_issues=metrics.date_issues,
            evidence_confidence=confidence,
        )
        empty_selection = PeerSelection(
            scope=None,
            peers=(),
            attempted_scopes=(),
            constituency_usable=selection.constituency_usable,
            constituency_kind=selection.constituency_kind,
            constituency_exclusion_reason=selection.constituency_exclusion_reason,
        )
        return _base_result(
            subject,
            outcome=TimeAssessmentOutcome.INVALID_DATES,
            flagged=False,
            status=EvidenceStatus.INCONCLUSIVE,
            severity=EvidenceSeverity.INFO,
            signal_kind=TimeSignalKind.INVALID_DATES,
            selection=empty_selection,
            quality=_empty_quality(),
            metrics=metrics,
            score=None,
            confidence=confidence,
            explanation=text,
            why_flagged=why_flagged,
            why_not_flagged=why_not,
            delay_ctx=ctx,
            score_method=None,
            peer_median_duration_days=None,
        )

    if metrics.family == ScheduleFamily.NONE:
        confidence = compute_evidence_confidence(
            time_mode=TimeMode.HYBRID_TEST,
            valid_dates=True,
            sufficient_timing_evidence=False,
            has_recommended_date=subject.recommended_date is not None,
            scope_id=None,
            peer_count=0,
            peer_quality=0,
            has_planned_dates=False,
            has_actual_dates=False,
            has_progress=False,
        )
        ctx = delay_context(delay_detected=False)
        text, why_flagged, why_not = explanation_for(
            TimeAssessmentOutcome.INSUFFICIENT_EVIDENCE,
            time_mode=TimeMode.HYBRID_TEST,
            evidence_confidence=confidence,
        )
        return _base_result(
            subject,
            outcome=TimeAssessmentOutcome.INSUFFICIENT_EVIDENCE,
            flagged=False,
            status=EvidenceStatus.INCONCLUSIVE,
            severity=EvidenceSeverity.INFO,
            signal_kind=TimeSignalKind.INSUFFICIENT_EXECUTION_TIMING,
            selection=selection,
            quality=quality,
            metrics=metrics,
            score=None,
            confidence=confidence,
            explanation=text,
            why_flagged=why_flagged,
            why_not_flagged=why_not,
            delay_ctx=ctx,
            score_method=None,
            peer_median_duration_days=None,
        )

    if metrics.family == ScheduleFamily.CLOSED:
        score, method, peer_median = closed_time_score(metrics, selection.peers)
        signal = TimeSignalKind.SCHEDULE_SLIPPAGE
    else:
        score, method, peer_median = open_time_score(metrics, selection.peers)
        signal = TimeSignalKind.SCHEDULE_PROGRESS_MISMATCH

    if score is None:
        confidence = compute_evidence_confidence(
            time_mode=TimeMode.HYBRID_TEST,
            valid_dates=True,
            sufficient_timing_evidence=False,
            has_recommended_date=subject.recommended_date is not None,
            scope_id=selection.scope.id if selection.scope else None,
            peer_count=selection.peer_count,
            peer_quality=quality.score,
            has_planned_dates=metrics.planned_duration_days is not None,
            has_actual_dates=metrics.actual_duration_days is not None,
            has_progress=metrics.physical_progress_percent is not None,
        )
        ctx = delay_context(delay_detected=False)
        text, why_flagged, why_not = explanation_for(
            TimeAssessmentOutcome.INSUFFICIENT_EVIDENCE,
            time_mode=TimeMode.HYBRID_TEST,
            evidence_confidence=confidence,
        )
        return _base_result(
            subject,
            outcome=TimeAssessmentOutcome.INSUFFICIENT_EVIDENCE,
            flagged=False,
            status=EvidenceStatus.INCONCLUSIVE,
            severity=EvidenceSeverity.INFO,
            signal_kind=TimeSignalKind.INSUFFICIENT_EXECUTION_TIMING,
            selection=selection,
            quality=quality,
            metrics=metrics,
            score=None,
            confidence=confidence,
            explanation=text,
            why_flagged=why_flagged,
            why_not_flagged=why_not,
            delay_ctx=ctx,
            score_method=None,
            peer_median_duration_days=peer_median,
        )

    flagged = is_time_anomaly(score)
    delay_detected = False
    if metrics.family == ScheduleFamily.CLOSED:
        delay_detected = (metrics.slippage_days or 0) > 0
    elif metrics.family == ScheduleFamily.OPEN:
        mismatch = metrics.progress_mismatch_points
        overdue = (metrics.slippage_days or 0) > 0
        delay_detected = overdue or (mismatch is not None and mismatch >= 10)
    ctx = delay_context(delay_detected=delay_detected)
    outcome = (
        TimeAssessmentOutcome.TIME_ANOMALY
        if flagged
        else TimeAssessmentOutcome.WITHIN_SCHEDULE
    )
    confidence = compute_evidence_confidence(
        time_mode=TimeMode.HYBRID_TEST,
        valid_dates=True,
        sufficient_timing_evidence=True,
        has_recommended_date=subject.recommended_date is not None,
        scope_id=selection.scope.id if selection.scope else None,
        peer_count=selection.peer_count,
        peer_quality=quality.score,
        has_planned_dates=metrics.planned_duration_days is not None,
        has_actual_dates=subject.actual_start_date is not None or subject.actual_completion_date is not None,
        has_progress=metrics.physical_progress_percent is not None,
    )
    explanation, why_flagged, why_not = explanation_for(
        outcome,
        time_mode=TimeMode.HYBRID_TEST,
        planned_duration_days=metrics.planned_duration_days,
        actual_duration_days=metrics.actual_duration_days,
        elapsed_duration_days=metrics.elapsed_duration_days,
        slippage_days=metrics.slippage_days,
        time_consumed_percent=metrics.time_consumed_percent,
        physical_progress_percent=metrics.physical_progress_percent,
        expected_progress_percent=metrics.expected_progress_percent,
        score=score,
        evidence_confidence=confidence,
        peer_count=selection.peer_count,
        peer_scope_label=selection.scope.label if selection.scope else None,
        delay_detected=delay_detected,
        delay_context_note=ctx.context_note,
        schedule_family=metrics.family.value,
    )
    if flagged:
        status = EvidenceStatus.MISMATCH
        severity = EvidenceSeverity.ATTENTION if score >= 80 else EvidenceSeverity.WATCH
    else:
        status = EvidenceStatus.CONSISTENT
        severity = EvidenceSeverity.INFO
    return _base_result(
        subject,
        outcome=outcome,
        flagged=flagged,
        status=status,
        severity=severity,
        signal_kind=signal,
        selection=selection,
        quality=quality,
        metrics=metrics,
        score=score,
        confidence=confidence,
        explanation=explanation,
        why_flagged=why_flagged,
        why_not_flagged=why_not,
        delay_ctx=ctx,
        score_method=method,
        peer_median_duration_days=peer_median,
    )


def persist_time_evidence(session: Session, result: TimeIntelligenceResult) -> EvidenceObjectRow:
    from app.evidence.adapters.time import time_result_to_evidence
    from app.evidence.repository import persist_evidence_object

    project = session.get(Project, result.project_id)
    if project is None:
        raise KeyError(f"Project {result.project_id} was not found.")
    obj = time_result_to_evidence(result, project, snapshot=project.snapshot)
    return persist_evidence_object(session, obj, replace_engine=EvidenceEngine.TIME)


def assess_project_time(
    session: Session,
    project_id: int,
    *,
    mode: TimeMode = TimeMode.REAL,
    persist: bool = True,
    min_peer_count: int = MIN_PEER_COUNT,
    schedules: dict[str, HybridSchedule] | None = None,
    observation_date: date | None = None,
) -> TimeIntelligenceResult:
    project = session.get(Project, project_id)
    if project is None:
        raise KeyError(f"Project {project_id} was not found.")
    obs = observation_date or observation_date_from_session(session)
    schedule = None
    catalog = schedules
    if mode == TimeMode.HYBRID_TEST:
        catalog = catalog if catalog is not None else load_hybrid_schedules()
        schedule = catalog.get(project.internal_project_id)
        if schedule is None:
            subject = project_to_time_record(
                project,
                time_mode=TimeMode.HYBRID_TEST,
                observation_date=obs,
            )
            return assess_time(subject, InMemoryTimePeerSource([subject]), min_peer_count=min_peer_count)
    subject = project_to_time_record(
        project,
        time_mode=mode,
        schedule=schedule,
        observation_date=obs,
    )
    source = SqlTimePeerSource(
        session,
        time_mode=mode,
        schedules=catalog if mode == TimeMode.HYBRID_TEST else None,
        observation_date=obs,
    )
    result = assess_time(subject, source, min_peer_count=min_peer_count)
    if persist:
        persist_time_evidence(session, result)
        session.commit()
    return result
