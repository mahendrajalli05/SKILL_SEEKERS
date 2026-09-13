"""SIMILAR_TO relationships via Overlap Intelligence V1.

Does not reimplement embeddings, blocking, or overlap scoring.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.engines.graph.constants import AMOUNT_SIMILAR_THRESHOLD, CLOSE_DATE_DAYS, MAX_SIMILAR_EDGES
from app.engines.graph.types import GraphMode, GraphRecord, SimilarRelation
from app.engines.overlap.candidates import OverlapIndex
from app.engines.overlap.embeddings import EmbeddingBackend, HashedTokenEmbedder
from app.engines.overlap.enrichment import HybridGps
from app.engines.overlap.scoring import score_pair
from app.engines.overlap.similarity import cosine_similarity
from app.engines.overlap.text import (
    combine_place_text,
    embedding_text,
    preserve_source_text,
    rare_block_tokens,
)
from app.engines.overlap.types import OverlapAssessmentOutcome, OverlapMode, OverlapRecord


def to_overlap_record(
    record: GraphRecord,
    *,
    gps: HybridGps | None = None,
) -> OverlapRecord:
    lat = gps.latitude if gps is not None else None
    lon = gps.longitude if gps is not None else None
    return OverlapRecord(
        project_id=record.project_id,
        internal_project_id=record.internal_project_id,
        source_work=preserve_source_text(record.source_work) or record.work_description,
        work_description=record.work_description,
        embedding_text=embedding_text(record.work_description),
        category=record.category,
        constituency=record.constituency,
        constituency_usable=record.constituency_usable,
        constituency_kind=record.constituency_kind,
        state=record.state,
        allocation_amount=record.allocation_amount,
        recommended_date=record.recommended_date,
        city=record.city,
        ward=record.ward,
        block=record.block,
        village=record.village,
        place_text=combine_place_text(
            city=record.city,
            ward=record.ward,
            block=record.block,
            village=record.village,
        ),
        rare_tokens=rare_block_tokens(record.work_description),
        latitude=lat,
        longitude=lon,
        gps_is_synthetic=bool(gps is not None and lat is not None and lon is not None),
    )


def _overlap_mode(mode: GraphMode) -> OverlapMode:
    return OverlapMode.HYBRID_TEST if mode == GraphMode.HYBRID_TEST else OverlapMode.REAL


def same_ida(left: GraphRecord, right: GraphRecord) -> bool:
    a = left.ida.strip().casefold()
    b = right.ida.strip().casefold()
    if not a or not b:
        return False
    return a == b


def close_dates(left: GraphRecord, right: GraphRecord) -> tuple[bool, int | None]:
    if left.recommended_date is None or right.recommended_date is None:
        return False, None
    gap = abs((left.recommended_date - right.recommended_date).days)
    return gap <= CLOSE_DATE_DAYS, gap


def similar_allocation_flag(amount_similarity: float | None) -> bool | None:
    if amount_similarity is None:
        return None
    return amount_similarity >= AMOUNT_SIMILAR_THRESHOLD


def similar_relations_for(
    subject: GraphRecord,
    records: Sequence[GraphRecord],
    *,
    mode: GraphMode = GraphMode.REAL,
    embedder: EmbeddingBackend | None = None,
    gps_by_id: dict[str, HybridGps] | None = None,
) -> list[SimilarRelation]:
    """Reuse Overlap blocking + scoring. Keep Potential Overlap / Duplicate pairs."""
    backend = embedder or HashedTokenEmbedder()
    overlap_mode = _overlap_mode(mode)
    gps_map = gps_by_id if mode == GraphMode.HYBRID_TEST else None

    def gps_for(item: GraphRecord) -> HybridGps | None:
        if not gps_map:
            return None
        return gps_map.get(item.internal_project_id)

    overlap_records = [to_overlap_record(item, gps=gps_for(item)) for item in records]
    subject_overlap = to_overlap_record(subject, gps=gps_for(subject))
    index = OverlapIndex(overlap_records)
    candidates = index.candidates_for(subject_overlap)
    if not candidates:
        return []
    texts = [subject_overlap.embedding_text, *[item.embedding_text for item in candidates]]
    vectors = backend.embed(texts)
    subject_vec = vectors[0]
    by_id = {item.project_id: item for item in records}
    relations: list[SimilarRelation] = []
    for other, vector in zip(candidates, vectors[1:], strict=True):
        semantic = cosine_similarity(subject_vec, vector)
        signals = score_pair(subject_overlap, other, semantic, mode=overlap_mode)
        if signals.outcome not in {
            OverlapAssessmentOutcome.POTENTIAL_DUPLICATE,
            OverlapAssessmentOutcome.POTENTIAL_OVERLAP,
        }:
            continue
        peer = by_id[other.project_id]
        close, gap = close_dates(subject, peer)
        amount_flag = similar_allocation_flag(signals.amount_similarity)
        gps_distance = signals.gps_distance_m if mode == GraphMode.HYBRID_TEST else None
        relations.append(
            SimilarRelation(
                linked_project_id=peer.project_id,
                linked_internal_project_id=peer.internal_project_id,
                similarity_score=float(signals.overlap_score),
                semantic_similarity=signals.semantic_similarity,
                same_constituency=signals.constituency_match,
                same_category=signals.category_match,
                same_ida=same_ida(subject, peer),
                similar_allocation=amount_flag,
                close_recommendation_dates=close,
                date_gap_days=gap if gap is not None else signals.date_gap_days,
                overlap_outcome=signals.outcome.value,
                gps_distance_m=gps_distance,
            )
        )
    relations.sort(
        key=lambda item: (
            -item.similarity_score,
            -(item.semantic_similarity or 0.0),
            item.linked_project_id,
        )
    )
    return relations[:MAX_SIMILAR_EDGES]
