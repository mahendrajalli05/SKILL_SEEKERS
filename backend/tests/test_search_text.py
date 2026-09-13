from __future__ import annotations

from datetime import date

from app.db import get_session_factory
from app.identity.scheme_id import reset_scheme_id_cache, scheme_id_for_project
from app.search.service import MAX_QUERY_LENGTH, normalize_search_query
from tests.test_search_api import insert_project


def _seed_search_corpus(session) -> dict[str, object]:
    tanks = insert_project(
        session,
        internal_project_id="internal:synthetic:text:tanks",
        work_description="NA - Construction of water tanks",
        mp_name="Y. S. JALLI",
        constituency="ONGOLE",
        category="Normal/Others",
        status="Ongoing",
    )
    school = insert_project(
        session,
        internal_project_id="internal:synthetic:text:school",
        work_description="NA - Construction of school building",
        mp_name="School MP",
        constituency="ELURU",
        category="Education",
        status="Completed",
        recommended_date=date(2023, 7, 1),
    )
    roads = insert_project(
        session,
        internal_project_id="internal:synthetic:text:roads",
        work_description="Construction of roads in rural area",
        mp_name="Road MP",
        constituency="ONGOLE",
        category="Roads",
        status="Ongoing",
        recommended_date=date(2023, 8, 1),
    )
    mh = insert_project(
        session,
        internal_project_id="internal:synthetic:text:mh",
        state="Maharashtra",
        constituency="MUMBAI NORTH",
        work_description="NA - Construction of school building",
        mp_name="JALLI MH",
        category="Education",
        status="Completed",
    )
    session.commit()
    reset_scheme_id_cache()
    tanks_scheme = scheme_id_for_project(session, tanks)
    return {
        "tanks": tanks,
        "school": school,
        "roads": roads,
        "mh": mh,
        "tanks_scheme": tanks_scheme,
    }


def test_normalize_search_query_trims_and_collapses_whitespace() -> None:
    assert normalize_search_query(None) is None
    assert normalize_search_query("") is None
    assert normalize_search_query("   ") is None
    assert normalize_search_query(" road ") == "road"
    assert normalize_search_query("Construction   Of   Roads") == "Construction Of Roads"
    assert len(normalize_search_query("x" * (MAX_QUERY_LENGTH + 50)) or "") == MAX_QUERY_LENGTH


def test_exact_and_partial_scheme_id_search(client) -> None:
    session = get_session_factory()()
    try:
        seeded = _seed_search_corpus(session)
        scheme_id = str(seeded["tanks_scheme"])
        tanks_id = seeded["tanks"].id
    finally:
        session.close()

    exact = client.get("/api/v1/projects", params={"q": scheme_id})
    assert exact.status_code == 200
    assert exact.json()["total"] == 1
    assert exact.json()["items"][0]["id"] == tanks_id
    assert exact.json()["items"][0]["scheme_id"] == scheme_id

    rank = scheme_id.rsplit("-", 1)[1]
    partial = client.get("/api/v1/projects", params={"q": rank})
    assert partial.status_code == 200
    ids = {item["id"] for item in partial.json()["items"]}
    assert tanks_id in ids

    mixed = client.get("/api/v1/projects", params={"q": scheme_id.lower()})
    assert mixed.json()["total"] == 1
    assert mixed.json()["items"][0]["id"] == tanks_id


def test_internal_project_id_full_and_partial_search(client) -> None:
    session = get_session_factory()()
    try:
        _seed_search_corpus(session)
    finally:
        session.close()

    full = client.get(
        "/api/v1/projects",
        params={"q": "internal:synthetic:text:school"},
    )
    assert full.json()["total"] == 1
    assert full.json()["items"][0]["internal_project_id"] == "internal:synthetic:text:school"

    partial = client.get("/api/v1/projects", params={"q": "internal:"})
    assert partial.status_code == 200
    internals = {item["internal_project_id"] for item in partial.json()["items"]}
    assert "internal:synthetic:text:school" in internals
    assert "internal:synthetic:text:tanks" in internals
    assert "internal:synthetic:text:mh" not in internals


def test_work_description_full_and_partial_and_case(client) -> None:
    session = get_session_factory()()
    try:
        _seed_search_corpus(session)
    finally:
        session.close()

    phrase = client.get("/api/v1/projects", params={"q": "construction of roads"})
    assert phrase.json()["total"] == 1
    assert "roads" in (phrase.json()["items"][0]["work_description"] or "").lower()

    padded = client.get("/api/v1/projects", params={"q": "  Construction Of Roads  "})
    assert padded.json()["total"] == 1

    school = client.get("/api/v1/projects", params={"q": "school"})
    assert school.json()["total"] == 1
    assert school.json()["items"][0]["internal_project_id"] == "internal:synthetic:text:school"


def test_mp_name_case_insensitive_search(client) -> None:
    session = get_session_factory()()
    try:
        _seed_search_corpus(session)
    finally:
        session.close()

    body = client.get("/api/v1/projects", params={"q": "JALLI"}).json()
    assert body["total"] == 1
    assert body["items"][0]["mp_name"] == "Y. S. JALLI"

    lower = client.get("/api/v1/projects", params={"q": "jalli"}).json()
    assert lower["total"] == 1


def test_empty_and_whitespace_query_is_not_an_error(client) -> None:
    session = get_session_factory()()
    try:
        _seed_search_corpus(session)
    finally:
        session.close()

    empty = client.get("/api/v1/projects", params={"q": ""})
    assert empty.status_code == 200
    assert empty.json()["total"] == 3

    whitespace = client.get("/api/v1/projects", params={"q": "   "})
    assert whitespace.status_code == 200
    assert whitespace.json()["total"] == 3


def test_zero_result_query_does_not_fall_back_to_unfiltered_list(client) -> None:
    session = get_session_factory()()
    try:
        _seed_search_corpus(session)
    finally:
        session.close()

    body = client.get("/api/v1/projects", params={"q": "zzzz-no-such-project"}).json()
    assert body["total"] == 0
    assert body["items"] == []


def test_search_combines_with_state_constituency_category_status(client) -> None:
    session = get_session_factory()()
    try:
        _seed_search_corpus(session)
    finally:
        session.close()

    with_state = client.get(
        "/api/v1/projects",
        params={"q": "school", "state": "Andhra Pradesh"},
    )
    assert with_state.json()["total"] == 1
    assert with_state.json()["items"][0]["state"] == "Andhra Pradesh"

    with_constituency = client.get(
        "/api/v1/projects",
        params={"q": "road", "state": "Andhra Pradesh", "constituency": "ONGOLE"},
    )
    assert with_constituency.json()["total"] == 1
    assert with_constituency.json()["items"][0]["constituency"] == "ONGOLE"

    with_category = client.get(
        "/api/v1/projects",
        params={"q": "construction", "state": "Andhra Pradesh", "category": "Education"},
    )
    assert with_category.json()["total"] == 1
    assert with_category.json()["items"][0]["category"] == "Education"

    with_status = client.get(
        "/api/v1/projects",
        params={"q": "construction", "state": "Andhra Pradesh", "status": "Completed"},
    )
    assert with_status.json()["total"] == 1
    assert with_status.json()["items"][0]["status"] == "Completed"

    combined = client.get(
        "/api/v1/projects",
        params={
            "q": "road",
            "state": "Andhra Pradesh",
            "constituency": "ONGOLE",
            "category": "Roads",
            "status": "Ongoing",
        },
    )
    assert combined.json()["total"] == 1
    item = combined.json()["items"][0]
    assert item["state"] == "Andhra Pradesh"
    assert item["constituency"] == "ONGOLE"
    assert item["category"] == "Roads"
    assert item["status"] == "Ongoing"
    assert item["scheme_id"]


def test_pagination_with_search_and_clearing_query(client) -> None:
    session = get_session_factory()()
    try:
        _seed_search_corpus(session)
    finally:
        session.close()

    first = client.get(
        "/api/v1/projects",
        params={"q": "construction", "page": 1, "page_size": 1},
    )
    assert first.status_code == 200
    assert first.json()["total"] == 3
    assert len(first.json()["items"]) == 1
    first_id = first.json()["items"][0]["id"]

    second = client.get(
        "/api/v1/projects",
        params={"q": "construction", "page": 2, "page_size": 1},
    )
    assert len(second.json()["items"]) == 1
    assert second.json()["items"][0]["id"] != first_id
    assert second.json()["page"] == 2

    cleared = client.get("/api/v1/projects", params={"q": "", "page": 1, "page_size": 20})
    assert cleared.json()["total"] == 3


def test_non_ap_records_excluded_from_ap_pilot_text_search(client) -> None:
    session = get_session_factory()()
    try:
        _seed_search_corpus(session)
    finally:
        session.close()

    jalli = client.get("/api/v1/projects", params={"q": "JALLI"})
    assert jalli.json()["total"] == 1
    assert jalli.json()["items"][0]["state"] == "Andhra Pradesh"

    school = client.get("/api/v1/projects", params={"q": "school"})
    assert all(item["state"] == "Andhra Pradesh" for item in school.json()["items"])

    mh_only = client.get(
        "/api/v1/projects",
        params={"q": "school", "state": "Maharashtra"},
    )
    assert mh_only.json()["total"] == 1
    assert mh_only.json()["items"][0]["state"] == "Maharashtra"


def test_special_characters_colon_and_long_query(client) -> None:
    session = get_session_factory()()
    try:
        _seed_search_corpus(session)
    finally:
        session.close()

    colon = client.get("/api/v1/projects", params={"q": "internal:synthetic:text:roads"})
    assert colon.json()["total"] == 1

    percent = client.get("/api/v1/projects", params={"q": "100% sure missing"})
    assert percent.status_code == 200
    assert percent.json()["total"] == 0

    underscore = client.get("/api/v1/projects", params={"q": "school_building_absent"})
    assert underscore.json()["total"] == 0

    long_q = "no-such-" + ("x" * 250)
    long_resp = client.get("/api/v1/projects", params={"q": long_q})
    assert long_resp.status_code == 200
    assert long_resp.json()["total"] == 0
