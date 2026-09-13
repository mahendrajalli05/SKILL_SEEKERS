from __future__ import annotations

from datetime import date

from app.engines.overlap.candidates import OverlapIndex, count_all_pairs, generate_candidate_pairs
from app.engines.overlap.constants import MAX_CANDIDATES_PER_SUBJECT
from app.engines.overlap.text import combine_place_text, constituency_fields, embedding_text, rare_block_tokens
from app.engines.overlap.types import OverlapRecord


def _record(
    project_id: int,
    *,
    work: str = "NA - Construction of water tanks",
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


def test_candidates_stay_inside_constituency_block() -> None:
    rows = [
        _record(1, constituency="KURNOOL", work="NA - Construction of water tanks"),
        _record(2, constituency="KURNOOL", work="NA - Construction of water tanks"),
        _record(3, constituency="ELURU", work="NA - Construction of water tanks", state="Telangana"),
    ]
    index = OverlapIndex(rows)
    ids = {item.project_id for item in index.candidates_for(rows[0])}
    assert 2 in ids
    assert 3 not in ids


def test_candidate_generation_is_not_all_pairs() -> None:
    rows: list[OverlapRecord] = []
    project_id = 1
    for const_i in range(40):
        constituency = f"PC{const_i:02d}"
        for work_i in range(5):
            rows.append(
                _record(
                    project_id,
                    constituency=constituency,
                    work=f"NA - Unique {constituency} asset {work_i} zz{project_id}",
                    rec_date=date(2023, 6, 1),
                )
            )
            project_id += 1
    pairs = generate_candidate_pairs(rows)
    n = len(rows)
    assert n == 200
    assert count_all_pairs(n) == 19900
    assert len(pairs) < 800
    assert len(pairs) < count_all_pairs(n) / 10


def test_large_block_requires_token_or_title_overlap() -> None:
    rows = [
        _record(i, work=f"NA - Uniqueasset{i} widget{i}")
        for i in range(1, 121)
    ]
    index = OverlapIndex(rows)
    candidates = index.candidates_for(rows[0])
    assert len(candidates) <= MAX_CANDIDATES_PER_SUBJECT
    assert len(candidates) < 50


def test_gps_cells_create_candidates_across_titles() -> None:
    left = _record(1, work="NA - Construction of water tanks", lat=15.8281, lon=78.0373)
    right = _record(2, work="NA - Construction of community halls", lat=15.8282, lon=78.0374)
    far = _record(
        3,
        constituency="VIZIANAGARAM",
        work="NA - Construction of community halls",
        lat=18.1067,
        lon=83.3956,
    )
    index = OverlapIndex([left, right, far])
    ids = {item.project_id for item in index.candidates_for(left)}
    assert 2 in ids
    assert 3 not in ids


def test_missing_dates_are_not_dropped_from_candidates() -> None:
    left = _record(1, rec_date=None)
    right = _record(2, rec_date=date(2023, 6, 1))
    index = OverlapIndex([left, right])
    assert [item.project_id for item in index.candidates_for(left)] == [2]


def test_date_window_excludes_far_apart_recommendations() -> None:
    left = _record(1, rec_date=date(2023, 5, 1))
    right = _record(2, rec_date=date(2024, 2, 1))
    index = OverlapIndex([left, right])
    assert index.candidates_for(left) == []
