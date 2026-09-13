"""Cost Intelligence V1.1 orchestration.

Produces an Allocation Cost Anomaly evidence object. Does not run risk fusion,
Time Intelligence, overlap, compliance, or Isolation Forest.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.domain.enums import EvidenceEngine, EvidenceSeverity, EvidenceStatus
from app.engines.cost.constants import (
    AMOUNT_UNIT_NOTE,
    ENGINE_NAME,
    ENGINE_VERSION,
    EVIDENCE_TYPE,
    MAX_DISPLAY_COMPARABLES,
    MIN_PEER_COUNT,
    SIGNAL_KIND,
)
from app.engines.cost.explain import explanation_for
from app.engines.cost.geography import classify_constituency
from app.engines.cost.peers import PeerSource, is_usable_amount, select_peers
from app.engines.cost.quality import compute_peer_quality
from app.engines.cost.repository import SqlPeerSource, project_to_peer_record
from app.engines.cost.scoring import (
    cost_anomaly_score,
    evidence_confidence as compute_evidence_confidence,
    is_cost_anomaly,
)
from app.engines.cost.stats import compute_peer_statistics
from app.engines.cost.types import (
    ComparableProject,
    CostAssessmentOutcome,
    CostIntelligenceResult,
    PeerQuality,
    PeerRecord,
    PeerSelection,
)
from app.engines.cost.work_type import work_type_similarity
from app.models.evidence import EvidenceObjectRow
from app.models.project import Project


def _date_distance(left: date | None, right: date | None) -> int:
    if left is None or right is None:
        return 10**9
    return abs((left - right).days)


def rank_comparables(
    subject: PeerRecord,
    peers: tuple[PeerRecord, ...],
    *,
    limit: int = MAX_DISPLAY_COMPARABLES,
) -> list[ComparableProject]:
    """Higher work-title similarity, then nearer amount, then date, then id."""
    actual = subject.allocation_amount or 0
    ranked: list[tuple[tuple[float, int, int, int], PeerRecord, float]] = []
    for peer in peers:
        amount = peer.allocation_amount or 0
        similarity = work_type_similarity(subject.work_description, peer.work_description)
        key = (
            -similarity,
            abs(amount - actual),
            _date_distance(subject.recommended_date, peer.recommended_date),
            peer.project_id,
        )
        ranked.append((key, peer, similarity))
    ranked.sort(key=lambda item: item[0])
    comparables: list[ComparableProject] = []
    for _key, peer, similarity in ranked[:limit]:
        amount = peer.allocation_amount or 0
        comparables.append(
            ComparableProject(
                project_id=peer.project_id,
                internal_project_id=peer.internal_project_id,
                constituency=peer.constituency,
                category=peer.category,
                derived_work_type=peer.derived_work_type,
                allocation_amount=amount,
                recommended_date=peer.recommended_date,
                amount_distance=abs(amount - actual),
                work_type_similarity=round(similarity, 3),
            )
        )
    return comparables


def _empty_quality() -> PeerQuality:
    return PeerQuality(
        score=0,
        rationale="No sufficient peer group was selected, so peer quality is 0.",
        median_work_type_similarity=0.0,
        category_match_rate=0.0,
    )


def _invalid_result(subject: PeerRecord) -> CostIntelligenceResult:
    classification = classify_constituency(subject.constituency)
    quality = _empty_quality()
    confidence = compute_evidence_confidence(
        scope_id=None,
        peer_count=0,
        mad=None,
        valid_amount=False,
        peer_quality=0,
        constituency_usable=classification.usable_as_geography,
    )
    text, why_flagged, why_not = explanation_for(
        CostAssessmentOutcome.INVALID_AMOUNT,
        evidence_confidence=confidence,
        peer_quality=0,
        constituency_exclusion_reason=(
            None if classification.usable_as_geography else classification.reason
        ),
    )
    return CostIntelligenceResult(
        project_id=subject.project_id,
        internal_project_id=subject.internal_project_id,
        engine=ENGINE_NAME,
        engine_version=ENGINE_VERSION,
        evidence_type=EVIDENCE_TYPE,
        outcome=CostAssessmentOutcome.INVALID_AMOUNT,
        flagged=False,
        status=EvidenceStatus.INCONCLUSIVE,
        severity=EvidenceSeverity.INFO,
        peer_scope=None,
        peer_scope_label=None,
        peer_count=0,
        baseline=None,
        actual_amount=subject.allocation_amount,
        deviation_percentage=None,
        percentile_25=None,
        percentile_75=None,
        percentile_10=None,
        percentile_90=None,
        mad=None,
        modified_z=None,
        cost_anomaly_score=None,
        evidence_confidence=confidence,
        explanation=text,
        why_flagged=why_flagged,
        why_not_flagged=why_not,
        comparable_projects=[],
        peer_project_ids=[],
        derived_work_type=subject.derived_work_type,
        observed_category=subject.category,
        constituency=subject.constituency,
        amount_unit_note=AMOUNT_UNIT_NOTE,
        attempted_scopes=(),
        expected_range_low=None,
        expected_range_high=None,
        best_attempt_peer_count=0,
        peer_quality=quality.score,
        similarity_rationale=quality.rationale,
        median_work_type_similarity=quality.median_work_type_similarity,
        constituency_kind=classification.kind.value,
        constituency_usable=classification.usable_as_geography,
        constituency_exclusion_reason=(
            None if classification.usable_as_geography else classification.reason
        ),
        signal_kind=SIGNAL_KIND,
        score_method=None,
        log_mad=None,
    )


def _insufficient_result(
    subject: PeerRecord,
    selection: PeerSelection,
) -> CostIntelligenceResult:
    quality = _empty_quality()
    confidence = compute_evidence_confidence(
        scope_id=None,
        peer_count=selection.best_attempt_peer_count,
        mad=None,
        valid_amount=True,
        peer_quality=0,
        constituency_usable=selection.constituency_usable,
    )
    text, why_flagged, why_not = explanation_for(
        CostAssessmentOutcome.INSUFFICIENT_EVIDENCE,
        peer_count=selection.best_attempt_peer_count,
        attempted_scopes=selection.attempted_scopes,
        evidence_confidence=confidence,
        peer_quality=0,
        constituency_exclusion_reason=selection.constituency_exclusion_reason,
    )
    return CostIntelligenceResult(
        project_id=subject.project_id,
        internal_project_id=subject.internal_project_id,
        engine=ENGINE_NAME,
        engine_version=ENGINE_VERSION,
        evidence_type=EVIDENCE_TYPE,
        outcome=CostAssessmentOutcome.INSUFFICIENT_EVIDENCE,
        flagged=False,
        status=EvidenceStatus.INCONCLUSIVE,
        severity=EvidenceSeverity.INFO,
        peer_scope=None,
        peer_scope_label=None,
        peer_count=selection.peer_count,
        baseline=None,
        actual_amount=subject.allocation_amount,
        deviation_percentage=None,
        percentile_25=None,
        percentile_75=None,
        percentile_10=None,
        percentile_90=None,
        mad=None,
        modified_z=None,
        cost_anomaly_score=None,
        evidence_confidence=confidence,
        explanation=text,
        why_flagged=why_flagged,
        why_not_flagged=why_not,
        comparable_projects=[],
        peer_project_ids=[],
        derived_work_type=subject.derived_work_type,
        observed_category=subject.category,
        constituency=subject.constituency,
        amount_unit_note=AMOUNT_UNIT_NOTE,
        attempted_scopes=selection.attempted_scopes,
        expected_range_low=None,
        expected_range_high=None,
        best_attempt_peer_count=selection.best_attempt_peer_count,
        peer_quality=quality.score,
        similarity_rationale=quality.rationale,
        median_work_type_similarity=quality.median_work_type_similarity,
        constituency_kind=selection.constituency_kind,
        constituency_usable=selection.constituency_usable,
        constituency_exclusion_reason=selection.constituency_exclusion_reason,
        signal_kind=SIGNAL_KIND,
        score_method=None,
        log_mad=None,
    )


def assess_cost(
    subject: PeerRecord,
    source: PeerSource,
    *,
    min_peer_count: int = MIN_PEER_COUNT,
) -> CostIntelligenceResult:
    """Pure assessment against a peer source. Does not write to the database."""
    if not is_usable_amount(subject.allocation_amount):
        return _invalid_result(subject)

    selection = select_peers(subject, source, min_peer_count=min_peer_count)
    if not selection.sufficient or selection.scope is None:
        return _insufficient_result(subject, selection)

    amounts = [int(peer.allocation_amount or 0) for peer in selection.peers]
    stats = compute_peer_statistics(amounts)
    actual = int(subject.allocation_amount or 0)
    quality = compute_peer_quality(subject, selection.peers, selection.scope)
    score, deviation, modified_z, score_method = cost_anomaly_score(
        actual,
        stats,
        median_work_type_similarity=quality.median_work_type_similarity,
    )
    flagged = is_cost_anomaly(score)
    outcome = (
        CostAssessmentOutcome.COST_ANOMALY
        if flagged
        else CostAssessmentOutcome.WITHIN_PEER_RANGE
    )
    confidence = compute_evidence_confidence(
        scope_id=selection.scope.id,
        peer_count=stats.peer_count,
        mad=stats.mad,
        valid_amount=True,
        peer_quality=quality.score,
        constituency_usable=selection.constituency_usable,
    )
    explanation, why_flagged, why_not = explanation_for(
        outcome,
        deviation_percentage=deviation,
        peer_count=stats.peer_count,
        peer_scope_label=selection.scope.label,
        baseline=stats.median,
        actual_amount=actual,
        score=score,
        percentile_25=stats.percentile_25,
        percentile_75=stats.percentile_75,
        attempted_scopes=selection.attempted_scopes,
        evidence_confidence=confidence,
        peer_quality=quality.score,
        similarity_rationale=quality.rationale,
        constituency_exclusion_reason=selection.constituency_exclusion_reason,
    )
    if flagged:
        status = EvidenceStatus.MISMATCH
        severity = (
            EvidenceSeverity.ATTENTION if score >= 80 else EvidenceSeverity.WATCH
        )
    else:
        status = EvidenceStatus.CONSISTENT
        severity = EvidenceSeverity.INFO

    peer_ids = [peer.project_id for peer in selection.peers]
    return CostIntelligenceResult(
        project_id=subject.project_id,
        internal_project_id=subject.internal_project_id,
        engine=ENGINE_NAME,
        engine_version=ENGINE_VERSION,
        evidence_type=EVIDENCE_TYPE,
        outcome=outcome,
        flagged=flagged,
        status=status,
        severity=severity,
        peer_scope=selection.scope.id,
        peer_scope_label=selection.scope.label,
        peer_count=stats.peer_count,
        baseline=stats.median,
        actual_amount=actual,
        deviation_percentage=deviation,
        percentile_25=stats.percentile_25,
        percentile_75=stats.percentile_75,
        percentile_10=stats.percentile_10,
        percentile_90=stats.percentile_90,
        mad=stats.mad,
        modified_z=modified_z,
        cost_anomaly_score=score,
        evidence_confidence=confidence,
        explanation=explanation,
        why_flagged=why_flagged,
        why_not_flagged=why_not,
        comparable_projects=rank_comparables(subject, selection.peers),
        peer_project_ids=peer_ids,
        derived_work_type=subject.derived_work_type,
        observed_category=subject.category,
        constituency=subject.constituency,
        amount_unit_note=AMOUNT_UNIT_NOTE,
        attempted_scopes=selection.attempted_scopes,
        expected_range_low=stats.percentile_25,
        expected_range_high=stats.percentile_75,
        best_attempt_peer_count=selection.best_attempt_peer_count,
        peer_quality=quality.score,
        similarity_rationale=quality.rationale,
        median_work_type_similarity=quality.median_work_type_similarity,
        constituency_kind=selection.constituency_kind,
        constituency_usable=selection.constituency_usable,
        constituency_exclusion_reason=selection.constituency_exclusion_reason,
        signal_kind=SIGNAL_KIND,
        score_method=score_method,
        log_mad=stats.log_mad,
    )


def persist_cost_evidence(session: Session, result: CostIntelligenceResult) -> EvidenceObjectRow:
    """Replace the current cost evidence object for this project."""
    from app.evidence.adapters.cost import cost_result_to_evidence
    from app.evidence.repository import persist_evidence_object

    project = session.get(Project, result.project_id)
    if project is None:
        raise KeyError(f"Project {result.project_id} was not found.")
    obj = cost_result_to_evidence(result, project, snapshot=project.snapshot)
    return persist_evidence_object(session, obj, replace_engine=EvidenceEngine.COST)


def assess_project_cost(
    session: Session,
    project_id: int,
    *,
    persist: bool = True,
    min_peer_count: int = MIN_PEER_COUNT,
) -> CostIntelligenceResult:
    project = session.get(Project, project_id)
    if project is None:
        raise KeyError(f"Project {project_id} was not found.")
    subject = project_to_peer_record(project)
    source = SqlPeerSource(session, subject_is_synthetic=subject.is_synthetic)
    result = assess_cost(subject, source, min_peer_count=min_peer_count)
    if persist:
        persist_cost_evidence(session, result)
        session.commit()
    return result
