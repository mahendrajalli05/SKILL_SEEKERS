"""Overlap / Duplicate Intelligence V1 orchestration.

Produces Potential Overlap / Potential Duplicate evidence. Does not run
cost, time, compliance, risk fusion, graph, copilot, or frontend.
"""

from __future__ import annotations

import json
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import EvidenceEngine, EvidenceSeverity, EvidenceStatus
from app.engines.overlap.candidates import OverlapIndex, blocking_strategy_label
from app.engines.overlap.constants import (
    ENGINE_NAME,
    ENGINE_VERSION,
    EVIDENCE_TYPE,
    MAX_DISPLAY_MATCHES,
    MISSING_DESCRIPTION_CONFIDENCE,
    SIGNAL_KIND,
)
from app.engines.overlap.embeddings import EmbeddingBackend, HashedTokenEmbedder, get_default_embedder
from app.engines.overlap.enrichment import load_hybrid_gps
from app.engines.overlap.explain import (
    missing_description_explanation,
    pair_reasons,
    project_explanation,
    why_linked_text,
    why_not_linked_text,
)
from app.engines.overlap.repository import load_overlap_records, load_subject_record
from app.engines.overlap.scoring import is_review_match, score_pair
from app.engines.overlap.similarity import cosine_similarity
from app.engines.overlap.text import constituency_fields, description_is_usable
from app.engines.overlap.types import (
    OverlapAssessmentOutcome,
    OverlapIntelligenceResult,
    OverlapMatch,
    OverlapMode,
    OverlapRecord,
    PairSignals,
)
from app.models.evidence import EvidenceObjectRow, OverlapLink
from app.models.project import Project


def _match_from_pair(
    subject: OverlapRecord,
    other: OverlapRecord,
    signals: PairSignals,
    *,
    mode: OverlapMode,
) -> OverlapMatch:
    flagged = is_review_match(signals)
    why_linked = None
    why_not = None
    if signals.outcome in {
        OverlapAssessmentOutcome.POTENTIAL_DUPLICATE,
        OverlapAssessmentOutcome.POTENTIAL_OVERLAP,
    }:
        why_linked = why_linked_text(signals, mode=mode)
    else:
        why_not = why_not_linked_text(signals, mode=mode, candidate_count=1)
    explanation = why_linked or why_not or ""
    return OverlapMatch(
        project_id=subject.project_id,
        internal_project_id=subject.internal_project_id,
        linked_project_id=other.project_id,
        linked_internal_project_id=other.internal_project_id,
        linked_source_work=other.source_work,
        linked_work_description=other.work_description,
        linked_category=other.category,
        linked_constituency=other.constituency,
        linked_allocation_amount=other.allocation_amount,
        linked_recommended_date=other.recommended_date,
        semantic_similarity=signals.semantic_similarity,
        category_match=signals.category_match,
        constituency_match=signals.constituency_match,
        amount_similarity=signals.amount_similarity,
        date_proximity=signals.date_proximity,
        date_gap_days=signals.date_gap_days,
        location_similarity=signals.location_similarity,
        gps_similarity=signals.gps_similarity,
        gps_distance_m=signals.gps_distance_m,
        overall_overlap_score=signals.overlap_score,
        evidence_confidence=signals.evidence_confidence,
        outcome=signals.outcome,
        flagged=flagged,
        geographic_evidence_available=signals.geographic_evidence_available,
        supporting_signals=signals.supporting_signals,
        unavailable_signals=signals.unavailable_signals,
        reasons=pair_reasons(signals, mode=mode),
        why_linked=why_linked,
        why_not_linked=why_not,
        explanation=explanation,
    )


def _status_for(outcome: OverlapAssessmentOutcome) -> tuple[EvidenceStatus, EvidenceSeverity]:
    if outcome == OverlapAssessmentOutcome.POTENTIAL_DUPLICATE:
        return EvidenceStatus.INCONCLUSIVE, EvidenceSeverity.ATTENTION
    if outcome == OverlapAssessmentOutcome.POTENTIAL_OVERLAP:
        return EvidenceStatus.INCONCLUSIVE, EvidenceSeverity.WATCH
    if outcome == OverlapAssessmentOutcome.INSUFFICIENT_EVIDENCE:
        return EvidenceStatus.INCONCLUSIVE, EvidenceSeverity.INFO
    return EvidenceStatus.CONSISTENT, EvidenceSeverity.INFO


def assess_overlap(
    subject: OverlapRecord,
    records: Sequence[OverlapRecord],
    *,
    mode: OverlapMode = OverlapMode.REAL,
    embedder: EmbeddingBackend | None = None,
) -> OverlapIntelligenceResult:
    """Pure assessment against an in-memory corpus. Does not write to the database."""
    backend = embedder or HashedTokenEmbedder()
    _value, usable, kind, exclusion = constituency_fields(subject.constituency)
    gps_used = any(
        item.latitude is not None and item.longitude is not None for item in (subject, *records)
    )
    blocking = blocking_strategy_label(gps_used=gps_used, constituency_usable=subject.constituency_usable)
    dataset_type = "HYBRID" if mode == OverlapMode.HYBRID_TEST else "REAL"

    if not description_is_usable(subject.work_description) and (
        subject.latitude is None or subject.longitude is None
    ):
        text = missing_description_explanation(mode=mode)
        status, severity = _status_for(OverlapAssessmentOutcome.INSUFFICIENT_EVIDENCE)
        return OverlapIntelligenceResult(
            project_id=subject.project_id,
            internal_project_id=subject.internal_project_id,
            engine=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            evidence_type=EVIDENCE_TYPE,
            dataset_type=dataset_type,
            overlap_mode=mode,
            outcome=OverlapAssessmentOutcome.INSUFFICIENT_EVIDENCE,
            flagged=False,
            status=status,
            severity=severity,
            signal_kind=SIGNAL_KIND,
            candidate_count=0,
            match_count=0,
            overlap_score=None,
            evidence_confidence=MISSING_DESCRIPTION_CONFIDENCE,
            embedding_backend=backend.name,
            geographic_evidence_available=False,
            explanation=text,
            why_linked=None,
            why_not_linked=text,
            matches=[],
            source_work=subject.source_work,
            work_description=subject.work_description,
            observed_category=subject.category,
            constituency=subject.constituency,
            constituency_kind=kind,
            constituency_usable=usable,
            constituency_exclusion_reason=exclusion,
            blocking_strategy=blocking,
            gps_used=False,
        )

    index = OverlapIndex(records)
    candidates = index.candidates_for(subject)
    texts = [subject.embedding_text, *[item.embedding_text for item in candidates]]
    vectors = backend.embed(texts)
    subject_vec = vectors[0]
    scored_matches: list[OverlapMatch] = []
    rejected: list[tuple[PairSignals, OverlapMatch]] = []
    for other, vector in zip(candidates, vectors[1:], strict=True):
        semantic = cosine_similarity(subject_vec, vector)
        signals = score_pair(subject, other, semantic, mode=mode)
        match = _match_from_pair(subject, other, signals, mode=mode)
        if signals.outcome in {
            OverlapAssessmentOutcome.POTENTIAL_DUPLICATE,
            OverlapAssessmentOutcome.POTENTIAL_OVERLAP,
        }:
            scored_matches.append(match)
        else:
            rejected.append((signals, match))

    scored_matches.sort(
        key=lambda item: (
            item.outcome == OverlapAssessmentOutcome.POTENTIAL_DUPLICATE,
            item.overall_overlap_score,
            item.semantic_similarity or 0.0,
            -item.linked_project_id,
        ),
        reverse=True,
    )
    display = scored_matches[:MAX_DISPLAY_MATCHES]
    if display:
        outcome = display[0].outcome
        overlap_score = display[0].overall_overlap_score
        confidence = display[0].evidence_confidence
        why_linked = display[0].why_linked
        why_not = None
        flagged = any(item.flagged for item in display)
        geo = any(item.geographic_evidence_available for item in display)
    else:
        best_rejected = max(rejected, key=lambda item: item[0].overlap_score, default=None)
        if not description_is_usable(subject.work_description) and not candidates:
            outcome = OverlapAssessmentOutcome.INSUFFICIENT_EVIDENCE
            overlap_score = None
            confidence = MISSING_DESCRIPTION_CONFIDENCE
            why_linked = None
            why_not = missing_description_explanation(mode=mode)
        else:
            outcome = OverlapAssessmentOutcome.NOT_LINKED
            overlap_score = best_rejected[0].overlap_score if best_rejected else None
            confidence = best_rejected[0].evidence_confidence if best_rejected else 16
            why_linked = None
            why_not = why_not_linked_text(
                best_rejected[0] if best_rejected else None,
                mode=mode,
                candidate_count=len(candidates),
            )
        flagged = False
        geo = best_rejected[1].geographic_evidence_available if best_rejected else False

    status, severity = _status_for(outcome)
    explanation = project_explanation(
        outcome=outcome,
        matches=display,
        why_linked=why_linked,
        why_not_linked=why_not,
        candidate_count=len(candidates),
        mode=mode,
        geographic_evidence_available=geo,
    )
    return OverlapIntelligenceResult(
        project_id=subject.project_id,
        internal_project_id=subject.internal_project_id,
        engine=ENGINE_NAME,
        engine_version=ENGINE_VERSION,
        evidence_type=EVIDENCE_TYPE,
        dataset_type=dataset_type,
        overlap_mode=mode,
        outcome=outcome,
        flagged=flagged,
        status=status,
        severity=severity,
        signal_kind=SIGNAL_KIND,
        candidate_count=len(candidates),
        match_count=len(display),
        overlap_score=overlap_score,
        evidence_confidence=confidence,
        embedding_backend=backend.name,
        geographic_evidence_available=geo,
        explanation=explanation,
        why_linked=why_linked,
        why_not_linked=why_not,
        matches=display,
        source_work=subject.source_work,
        work_description=subject.work_description,
        observed_category=subject.category,
        constituency=subject.constituency,
        constituency_kind=kind,
        constituency_usable=usable,
        constituency_exclusion_reason=exclusion,
        blocking_strategy=blocking,
        gps_used=gps_used,
    )


def persist_overlap_evidence(session: Session, result: OverlapIntelligenceResult) -> EvidenceObjectRow:
    from app.evidence.adapters.overlap import overlap_result_to_evidence
    from app.evidence.repository import persist_evidence_object

    project = session.get(Project, result.project_id)
    if project is None:
        raise KeyError(f"Project {result.project_id} was not found.")
    obj = overlap_result_to_evidence(result, project, snapshot=project.snapshot)
    row = persist_evidence_object(session, obj, replace_engine=EvidenceEngine.OVERLAP)
    links = session.scalars(
        select(OverlapLink).where(OverlapLink.from_project_id == result.project_id)
    ).all()
    for link in links:
        session.delete(link)
    for item in result.matches:
        session.add(
            OverlapLink(
                from_project_id=result.project_id,
                to_project_id=item.linked_project_id,
                score=float(item.overall_overlap_score),
                reasons=json.dumps(list(item.reasons), sort_keys=True),
            )
        )
    session.flush()
    return row


def assess_project_overlap(
    session: Session,
    project_id: int,
    *,
    mode: OverlapMode = OverlapMode.REAL,
    persist: bool = True,
    embedder: EmbeddingBackend | None = None,
) -> OverlapIntelligenceResult:
    gps_map = load_hybrid_gps() if mode == OverlapMode.HYBRID_TEST else None
    subject = load_subject_record(session, project_id, mode=mode, gps_by_id=gps_map)
    project = session.get(Project, project_id)
    if project is None:
        raise KeyError(f"Project {project_id} was not found.")
    records = load_overlap_records(
        session,
        mode=mode,
        gps_by_id=gps_map,
        subject_is_synthetic=bool(project.is_synthetic),
    )
    backend = embedder or get_default_embedder()
    result = assess_overlap(subject, records, mode=mode, embedder=backend)
    if persist:
        persist_overlap_evidence(session, result)
        session.commit()
    return result
