from __future__ import annotations

from app.db import get_session_factory
from app.identity.scheme_id import (
    format_scheme_id,
    looks_like_scheme_id,
    parse_scheme_id,
    reset_scheme_id_cache,
    scheme_id_for_project,
)
from app.identity.state_codes import internal_state_code
from app.models.project import Project
from app.scope import SCHEME_ID_NOTE
from tests.test_search_api import insert_project


def test_andhra_pradesh_code_is_ap() -> None:
    assert internal_state_code("Andhra Pradesh") == "AP"
    assert internal_state_code("ANDHRA PRADESH") == "AP"
    assert looks_like_scheme_id("SVK-AP-000001")
    assert parse_scheme_id("svk-ap-12") == ("AP", 12)
    assert "official MPLADS Work ID" in SCHEME_ID_NOTE
    assert SCHEME_ID_NOTE.lower().startswith("internal")


def test_scheme_ids_are_deterministic_unique_and_stable(client) -> None:
    session = get_session_factory()()
    try:
        first = insert_project(session, internal_project_id="internal:synthetic:scheme:a")
        second = insert_project(session, internal_project_id="internal:synthetic:scheme:b")
        other = insert_project(
            session,
            internal_project_id="internal:synthetic:scheme:mh",
            state="Maharashtra",
            constituency="NAGPUR",
        )
        session.commit()
        reset_scheme_id_cache()
        id_a = scheme_id_for_project(session, first)
        id_b = scheme_id_for_project(session, second)
        id_mh = scheme_id_for_project(session, other)
        again_a = scheme_id_for_project(session, first)
        first_pk = first.id
    finally:
        session.close()

    assert id_a == again_a
    assert id_a != id_b
    assert id_a.startswith("SVK-AP-")
    assert id_b.startswith("SVK-AP-")
    assert id_mh.startswith("SVK-MH-")
    assert id_a == format_scheme_id("AP", int(id_a.rsplit("-", 1)[1]))

    detail = client.get(f"/api/v1/projects/{first_pk}").json()
    assert detail["scheme_id"] == id_a
    assert detail["internal_project_id"] == "internal:synthetic:scheme:a"
    assert "not an official MPLADS Work ID" in detail["scheme_id_note"]


def test_scheme_id_does_not_change_internal_project_id(client) -> None:
    session = get_session_factory()()
    try:
        row = insert_project(session, internal_project_id="internal:synthetic:scheme:keep")
        session.commit()
        project_id = row.id
        internal = row.internal_project_id
    finally:
        session.close()

    body = client.get(f"/api/v1/projects/{project_id}").json()
    assert body["internal_project_id"] == internal
    assert body["scheme_id"] != internal
    session = get_session_factory()()
    try:
        stored = session.get(Project, project_id)
        assert stored is not None
        assert stored.internal_project_id == internal
        assert "scheme_id" not in stored.__table__.c
    finally:
        session.close()
