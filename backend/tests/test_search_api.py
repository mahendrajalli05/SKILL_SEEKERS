from __future__ import annotations

from datetime import date

from app.db import get_session_factory
from app.models.project import Project

SYNTHETIC_LABEL = "SYNTHETIC: search unit test (not a government project)"


def insert_project(session, **overrides: object) -> Project:
    values: dict[str, object] = {
        "internal_project_id": "internal:synthetic:search:subject",
        "internal_id_kind": "internal_surrogate_hash",
        "internal_id_scheme": "sarvsakshi_internal_work_v1",
        "source_dataset": "github_vonter_india-mplads-works_MPLADS.csv",
        "is_synthetic": True,
        "synthetic_label": SYNTHETIC_LABEL,
        "lifecycle_stage": "ONGOING",
        "state": "Andhra Pradesh",
        "constituency": "KURNOOL",
        "category": "Normal/Others",
        "work_description": "NA - Construction of water tanks",
        "mp_name": "Test MP",
        "allocation_amount": 500_000,
        "recommended_date": date(2023, 6, 1),
        "status": "Ongoing",
        "ida": "Kurnool_IDA",
        "house": "Lok Sabha",
    }
    values.update(overrides)
    row = Project(**values)
    session.add(row)
    session.flush()
    return row


def test_projects_list_supports_pagination(client) -> None:
    session = get_session_factory()()
    try:
        insert_project(session, internal_project_id="internal:synthetic:search:a")
        insert_project(
            session,
            internal_project_id="internal:synthetic:search:b",
            work_description="NA - Construction of school building",
            constituency="ELURU",
            category="Education",
            status="Completed",
            recommended_date=date(2023, 7, 1),
        )
        insert_project(
            session,
            internal_project_id="internal:synthetic:search:c",
            work_description="Repair and Renovation of community hall",
            constituency="KADAPA",
            mp_name="Another MP",
            recommended_date=date(2022, 1, 1),
        )
        session.commit()
    finally:
        session.close()

    first = client.get("/api/v1/projects", params={"page": 1, "page_size": 2})
    assert first.status_code == 200
    body = first.json()
    assert body["total"] == 3
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert len(body["items"]) == 2
    assert body["effective_state"] == "Andhra Pradesh"
    assert body["pilot_label"] == "Current Pilot: Andhra Pradesh"
    assert "district" not in body["items"][0]
    assert "vendor" not in body["items"][0]
    assert "expenditure" not in body["items"][0]
    assert body["items"][0]["scheme_id"]
    assert "not an official MPLADS Work ID" in body["scheme_id_note"]
    assert "Source amount unit is unspecified" in body["note"]

    second = client.get("/api/v1/projects", params={"page": 2, "page_size": 2})
    assert second.status_code == 200
    assert len(second.json()["items"]) == 1


def test_default_search_is_restricted_to_andhra_pradesh(client) -> None:
    session = get_session_factory()()
    try:
        insert_project(session, internal_project_id="internal:synthetic:search:ap")
        insert_project(
            session,
            internal_project_id="internal:synthetic:search:mh",
            state="Maharashtra",
            constituency="MUMBAI NORTH",
            work_description="NA - Construction of hospital",
        )
        session.commit()
    finally:
        session.close()

    defaulted = client.get("/api/v1/projects")
    assert defaulted.status_code == 200
    body = defaulted.json()
    assert body["total"] == 1
    assert body["items"][0]["state"] == "Andhra Pradesh"
    assert body["effective_state"] == "Andhra Pradesh"

    maharashtra = client.get("/api/v1/projects", params={"state": "Maharashtra"})
    assert maharashtra.json()["total"] == 1
    assert maharashtra.json()["items"][0]["state"] == "Maharashtra"

    all_states = client.get("/api/v1/projects", params={"apply_pilot_scope": False})
    ids = {item["internal_project_id"] for item in all_states.json()["items"]}
    assert "internal:synthetic:search:ap" in ids
    assert "internal:synthetic:search:mh" in ids


def test_text_search_covers_scheme_id_internal_id_work_and_mp(client) -> None:
    session = get_session_factory()()
    try:
        tanks = insert_project(session, internal_project_id="internal:synthetic:search:tanks")
        insert_project(
            session,
            internal_project_id="internal:synthetic:search:school",
            work_description="NA - Construction of school building",
            mp_name="School MP",
            constituency="ELURU",
        )
        session.commit()
        tanks_id = tanks.id
    finally:
        session.close()

    by_work = client.get("/api/v1/projects", params={"q": "school building"})
    assert by_work.status_code == 200
    items = by_work.json()["items"]
    assert len(items) == 1
    assert items[0]["internal_project_id"] == "internal:synthetic:search:school"

    by_mp = client.get("/api/v1/projects", params={"q": "School MP"})
    assert len(by_mp.json()["items"]) == 1

    by_internal = client.get(
        "/api/v1/projects",
        params={"internal_project_id": "internal:synthetic:search:tanks"},
    )
    assert len(by_internal.json()["items"]) == 1
    assert by_internal.json()["items"][0]["work_description"] == "NA - Construction of water tanks"

    by_internal_q = client.get("/api/v1/projects", params={"q": "internal:synthetic:search:tanks"})
    assert len(by_internal_q.json()["items"]) == 1

    detail = client.get(f"/api/v1/projects/{tanks_id}").json()
    scheme_id = detail["scheme_id"]
    assert scheme_id.startswith("SVK-AP-")
    by_scheme_q = client.get("/api/v1/projects", params={"q": scheme_id})
    assert len(by_scheme_q.json()["items"]) == 1
    assert by_scheme_q.json()["items"][0]["id"] == tanks_id
    by_scheme_param = client.get("/api/v1/projects", params={"scheme_id": scheme_id})
    assert len(by_scheme_param.json()["items"]) == 1


def test_filters_use_available_fields_and_ignore_district(client) -> None:
    session = get_session_factory()()
    try:
        insert_project(session)
        insert_project(
            session,
            internal_project_id="internal:synthetic:search:eluru",
            constituency="ELURU",
            category="Education",
            status="Completed",
            state="Andhra Pradesh",
        )
        session.commit()
    finally:
        session.close()

    filtered = client.get(
        "/api/v1/projects",
        params={"constituency": "ELURU", "category": "Education", "status": "Completed"},
    )
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1
    assert filtered.json()["items"][0]["constituency"] == "ELURU"

    ignored = client.get(
        "/api/v1/projects",
        params={"constituency": "ELURU", "district": "ShouldNotFilter", "vendor": "No"},
    )
    assert ignored.status_code == 200
    assert ignored.json()["total"] == 1


def test_non_geographic_constituency_is_not_used_as_filter(client) -> None:
    session = get_session_factory()()
    try:
        insert_project(session, constituency="KURNOOL")
        insert_project(
            session,
            internal_project_id="internal:synthetic:search:rs",
            constituency="Sitting Rajya Sabha",
            work_description="NA - Sitting house label preserved",
        )
        session.commit()
    finally:
        session.close()

    ignored = client.get(
        "/api/v1/projects",
        params={"constituency": "Sitting Rajya Sabha"},
    )
    assert ignored.status_code == 200
    body = ignored.json()
    assert body["constituency_filter_applied"] is False
    assert body["ignored_non_geographic_constituency"] == "Sitting Rajya Sabha"
    assert body["total"] == 2
    preserved = next(
        item for item in body["items"] if item["internal_project_id"] == "internal:synthetic:search:rs"
    )
    assert preserved["constituency"] == "Sitting Rajya Sabha"


def test_search_options_require_state_for_constituency(client) -> None:
    session = get_session_factory()()
    try:
        insert_project(session)
        insert_project(
            session,
            internal_project_id="internal:synthetic:search:options",
            constituency="ELURU",
            category="Education",
            status="Completed",
        )
        insert_project(
            session,
            internal_project_id="internal:synthetic:search:rs-opt",
            constituency="Nominated Rajya Sabha",
        )
        insert_project(
            session,
            internal_project_id="internal:synthetic:search:mh-opt",
            state="Maharashtra",
            constituency="MUMBAI NORTH",
            category="Health",
        )
        session.commit()
    finally:
        session.close()

    none = client.get("/api/v1/projects/options")
    assert none.status_code == 200
    empty = none.json()
    assert empty["constituencies"] == []
    assert empty["constituency_enabled"] is False
    assert empty["constituency_placeholder"] == "Select state first"
    assert "Andhra Pradesh" in empty["states"]
    assert "Maharashtra" in empty["states"]
    assert "district" not in empty
    assert "vendor" not in empty

    ap = client.get("/api/v1/projects/options", params={"state": "Andhra Pradesh"})
    body = ap.json()
    assert body["constituency_enabled"] is True
    assert "KURNOOL" in body["constituencies"]
    assert "ELURU" in body["constituencies"]
    assert "Sitting Rajya Sabha" not in body["constituencies"]
    assert "Nominated Rajya Sabha" not in body["constituencies"]
    assert "Nominated Rajya Sabha" in body["excluded_non_geographic_constituencies"]
    assert "MUMBAI NORTH" not in body["constituencies"]
    assert "Education" in body["categories"]
    assert "Completed" in body["statuses"]

    mh = client.get("/api/v1/projects/options", params={"state": "Maharashtra"})
    assert mh.json()["constituencies"] == ["MUMBAI NORTH"]
    assert "KURNOOL" not in mh.json()["constituencies"]


def test_search_response_has_no_fraud_wording(client) -> None:
    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    text = str(response.json()).casefold()
    assert "fraud" not in text


def test_hybrid_search_marks_enrichment_without_using_it_in_real_mode(client, monkeypatch) -> None:
    session = get_session_factory()()
    try:
        insert_project(session, internal_project_id="internal:synthetic:search:hybrid-row")
        insert_project(
            session,
            internal_project_id="internal:synthetic:search:real-only",
            constituency="ELURU",
        )
        session.commit()
    finally:
        session.close()

    monkeypatch.setattr(
        "app.search.service.has_hybrid_enrichment",
        lambda value: value == "internal:synthetic:search:hybrid-row",
    )
    hybrid = client.get("/api/v1/projects", params={"mode": "hybrid"})
    assert hybrid.status_code == 200
    by_id = {item["internal_project_id"]: item for item in hybrid.json()["items"]}
    assert by_id["internal:synthetic:search:hybrid-row"]["data_mode"] == "HYBRID"
    assert by_id["internal:synthetic:search:real-only"]["data_mode"] == "REAL"

    real = client.get("/api/v1/projects", params={"mode": "real"})
    for item in real.json()["items"]:
        assert item["data_mode"] == "REAL"
