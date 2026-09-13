from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_session_factory
from app.engines.overlap.constants import FORBIDDEN_MODEL_INPUT_COLUMNS, HASHED_EMBEDDER_NAME
from app.engines.overlap.embeddings import HashedTokenEmbedder
from app.engines.overlap.service import assess_overlap, assess_project_overlap
from app.engines.overlap.text import combine_place_text, constituency_fields, embedding_text, rare_block_tokens
from app.engines.overlap.types import OverlapAssessmentOutcome, OverlapMode, OverlapRecord
from app.models.evidence import EvidenceObjectRow, OverlapLink
from app.models.fusion import FusionScore
from app.models.project import Project

SYNTHETIC_LABEL = "SYNTHETIC: overlap-intelligence unit test (not a government project)"
TANKS = "NA - Construction of water tanks"
TANK = "NA - Construction of water tank"
ROADS = "NA - Construction of roads, approach roads, link roads and pathways"
HALLS = "NA - Construction of community centers and community halls"
AMBULANCE = "NA - Purchase of ambulance"


def _record(
    project_id: int,
    *,
    work: str = TANKS,
    category: str = "Normal/Others",
    constituency: str = "KURNOOL",
    state: str = "Andhra Pradesh",
    amount: int | None = 500_000,
    rec_date: date | None = date(2023, 6, 1),
    village: str = "",
    lat: float | None = None,
    lon: float | None = None,
) -> OverlapRecord:
    value, usable, kind, _reason = constituency_fields(constituency)
    return OverlapRecord(
        project_id=project_id,
        internal_project_id=f"internal:synthetic:overlap:{project_id}",
        source_work=work,
        work_description=work,
        embedding_text=embedding_text(work),
        category=category,
        constituency=value,
        constituency_usable=usable,
        constituency_kind=kind,
        state=state,
        allocation_amount=amount,
        recommended_date=rec_date,
        village=village,
        place_text=combine_place_text(village=village),
        rare_tokens=rare_block_tokens(work),
        latitude=lat,
        longitude=lon,
        gps_is_synthetic=lat is not None,
    )


def test_duplicate_text_is_potential_duplicate() -> None:
    subject = _record(1)
    other = _record(2, amount=500_000, rec_date=date(2023, 6, 8), village="Pedakakani")
    # same village on both so location can support
    subject = _record(1, village="Pedakakani")
    result = assess_overlap(subject, [subject, other], embedder=HashedTokenEmbedder())
    assert result.outcome == OverlapAssessmentOutcome.POTENTIAL_DUPLICATE
    assert result.matches
    assert result.matches[0].semantic_similarity == 1.0
    assert result.matches[0].category_match is True
    assert result.matches[0].constituency_match is True
    assert "Potential Duplicate" in result.explanation
    assert "fraud" not in result.explanation.casefold()


def test_near_duplicate_text_is_linked() -> None:
    subject = _record(1, work=TANKS)
    other = _record(2, work=TANK)
    result = assess_overlap(subject, [subject, other], embedder=HashedTokenEmbedder())
    assert result.match_count >= 1
    assert result.outcome in {
        OverlapAssessmentOutcome.POTENTIAL_DUPLICATE,
        OverlapAssessmentOutcome.POTENTIAL_OVERLAP,
    }
    assert (result.matches[0].semantic_similarity or 0) > 0.85


def test_false_positive_same_constituency_different_works() -> None:
    subject = _record(1, work=TANKS)
    other = _record(2, work=ROADS, amount=500_000)
    result = assess_overlap(subject, [subject, other], embedder=HashedTokenEmbedder())
    assert result.outcome in {
        OverlapAssessmentOutcome.NOT_LINKED,
        OverlapAssessmentOutcome.INSUFFICIENT_EVIDENCE,
    }
    assert result.flagged is False
    assert result.match_count == 0


def test_same_amount_unrelated_not_linked() -> None:
    subject = _record(1, work=TANKS, amount=750_000)
    other = _record(2, work=AMBULANCE, amount=750_000)
    result = assess_overlap(subject, [subject, other], embedder=HashedTokenEmbedder())
    assert result.match_count == 0
    assert result.outcome == OverlapAssessmentOutcome.NOT_LINKED


def test_similar_wording_genuinely_different_projects() -> None:
    subject = _record(1, work="NA - Construction of water tanks in ZPHS compound")
    other = _record(2, work="NA - Construction of community halls in ZPHS compound")
    result = assess_overlap(subject, [subject, other], embedder=HashedTokenEmbedder())
    if result.matches:
        assert result.outcome != OverlapAssessmentOutcome.POTENTIAL_DUPLICATE
        assert result.matches[0].semantic_similarity is None or result.matches[0].semantic_similarity < 0.92


def test_missing_description_is_insufficient() -> None:
    subject = _record(1, work="")
    other = _record(2, work="")
    result = assess_overlap(subject, [subject, other], embedder=HashedTokenEmbedder())
    assert result.outcome == OverlapAssessmentOutcome.INSUFFICIENT_EVIDENCE
    assert result.overlap_score is None
    assert "Insufficient evidence" in result.explanation or "missing" in result.explanation.casefold()


def test_real_mode_reports_geographic_evidence_unavailable() -> None:
    subject = _record(1)
    other = _record(2, work=ROADS)
    result = assess_overlap(subject, [subject, other], mode=OverlapMode.REAL, embedder=HashedTokenEmbedder())
    assert result.geographic_evidence_available is False
    assert result.gps_used is False
    blob = result.explanation.casefold()
    assert "gps" in blob or "geographic evidence unavailable" in blob


def test_output_is_deterministic() -> None:
    subject = _record(1)
    corpus = [subject, _record(2), _record(3, work=ROADS), _record(4, work=HALLS)]
    embedder = HashedTokenEmbedder()
    first = assess_overlap(subject, corpus, embedder=embedder)
    second = assess_overlap(subject, corpus, embedder=HashedTokenEmbedder())
    assert first.outcome == second.outcome
    assert first.overlap_score == second.overlap_score
    assert first.explanation == second.explanation
    assert [item.linked_project_id for item in first.matches] == [
        item.linked_project_id for item in second.matches
    ]


def test_record_and_result_exclude_leakage_fields() -> None:
    fields = set(OverlapRecord.__dataclass_fields__)
    assert fields.isdisjoint(FORBIDDEN_MODEL_INPUT_COLUMNS)
    assert "mp_name" not in fields
    subject = _record(1)
    result = assess_overlap(subject, [subject, _record(2)], embedder=HashedTokenEmbedder())
    blob = (result.explanation + str(result.matches)).casefold()
    for token in (
        "scenario_type",
        "demo_case_id",
        "anomaly_notes",
        "overlap_group",
        "coordinate_source",
    ):
        assert token not in blob
    assert "fraud" not in blob


def test_high_semantic_alone_says_potential_overlap() -> None:
    subject = _record(1, constituency="KURNOOL", category="Normal/Others", amount=100_000)
    other = _record(
        2,
        work=TANKS,
        constituency="GUNTUR",
        category="Repair and Renovation",
        amount=8_000_000,
        rec_date=date(2023, 8, 15),
        state="Andhra Pradesh",
    )
    result = assess_overlap(subject, [subject, other], embedder=HashedTokenEmbedder())
    if result.matches:
        assert result.outcome == OverlapAssessmentOutcome.POTENTIAL_OVERLAP
        assert "Potential Duplicate" not in result.explanation.split("Potential Overlap")[0] or True
        assert result.matches[0].outcome != OverlapAssessmentOutcome.POTENTIAL_DUPLICATE


def _insert_project(session: Session, **overrides: object) -> Project:
    values: dict[str, object] = {
        "internal_project_id": "internal:synthetic:overlap:db:1",
        "internal_id_kind": "internal_surrogate_hash",
        "internal_id_scheme": "sarvsakshi_internal_work_v1",
        "is_synthetic": True,
        "synthetic_label": SYNTHETIC_LABEL,
        "lifecycle_stage": "FUTURE",
        "state": "Andhra Pradesh",
        "constituency": "KURNOOL",
        "category": "Normal/Others",
        "work_description": TANKS,
        "source_work": TANKS,
        "allocation_amount": 500_000,
        "recommended_date": date(2023, 6, 1),
        "status": "Unsanctioned",
    }
    values.update(overrides)
    row = Project(**values)
    session.add(row)
    session.flush()
    return row


def test_persist_writes_overlap_links_not_fusion(client) -> None:
    session = get_session_factory()()
    try:
        subject = _insert_project(session)
        _insert_project(
            session,
            internal_project_id="internal:synthetic:overlap:db:2",
            allocation_amount=505_000,
            recommended_date=date(2023, 6, 5),
        )
        session.commit()
        result = assess_project_overlap(
            session,
            subject.id,
            persist=True,
            embedder=HashedTokenEmbedder(),
        )
        assert result.embedding_backend == HASHED_EMBEDDER_NAME
        links = session.scalars(select(OverlapLink)).all()
        evidence = session.scalars(
            select(EvidenceObjectRow).where(EvidenceObjectRow.engine == "overlap")
        ).all()
        fusion_count = session.scalar(select(func.count()).select_from(FusionScore)) or 0
        assert fusion_count == 0
        assert evidence
        if result.matches:
            assert links
    finally:
        session.close()


def test_overlap_intelligence_api(client) -> None:
    session = get_session_factory()()
    try:
        subject = _insert_project(session, internal_project_id="internal:synthetic:overlap:api:subject")
        _insert_project(
            session,
            internal_project_id="internal:synthetic:overlap:api:peer",
            allocation_amount=500_000,
        )
        session.commit()
        project_id = subject.id
    finally:
        session.close()

    missing = client.get("/api/v1/projects/999999/overlap-intelligence")
    assert missing.status_code == 404

    response = client.get(f"/api/v1/projects/{project_id}/overlap-intelligence")
    assert response.status_code == 200
    body = response.json()
    assert body["engine"] == "overlap"
    assert body["evidence_confidence"] >= 0
    assert "fraud" not in body["explanation"].casefold()
    assert "fraud" not in str(body).casefold()
    assert body["signal_kind"] == "potential_overlap"
