from __future__ import annotations

from app.db import get_session_factory
from app.domain.enums import DataMode, SignalType
from app.engines.geo.constants import ENGINE_VERSION, LOCATION_CONSISTENT
from app.engines.geo.service import check_project_geospatial, parse_data_mode
from app.engines.image.service import upload_image
from app.evidence.repository import list_project_evidence
from app.evidence.validate import validate_evidence
from tests.geo_test_support import insert_project
from tests.geospatial_fixtures import VIZIANAGARAM_LAT, VIZIANAGARAM_LON, jpeg_with_gps


def test_evidence_objects_and_pce_framing(client, monkeypatch) -> None:
    session = get_session_factory()()
    try:
        project = insert_project(session, internal_project_id="internal:geo:ev:hybrid")
        session.flush()
        monkeypatch.setattr(
            "app.engines.geo.location.load_hybrid_coordinates",
            lambda path=None: {project.internal_project_id: (VIZIANAGARAM_LAT, VIZIANAGARAM_LON)},
        )
        upload_image(
            session,
            project,
            payload=jpeg_with_gps(VIZIANAGARAM_LAT, VIZIANAGARAM_LON),
            filename="site.jpg",
            declared_mime="image/jpeg",
            data_mode=DataMode.HYBRID,
        )
        first = check_project_geospatial(session, project, DataMode.HYBRID, persist=True)
        second = check_project_geospatial(session, project, DataMode.HYBRID, persist=True)
        session.commit()
        assert first.overall_result == LOCATION_CONSISTENT
        assert first.evidence_ids == second.evidence_ids
        items = list_project_evidence(session, project.id, engine="geo", data_mode="HYBRID")
        assert items
        assert all(item.engine_name == "geo" for item in items)
        assert all(item.engine_version == ENGINE_VERSION for item in items)
        assert all(item.provenance.enrichment_used is True for item in items)
        assert any(item.signal_type == SignalType.GEOSPATIAL_LOCATION_CONSISTENCY for item in items)
        for item in items:
            checked = validate_evidence(item)
            assert checked.provenance.notes
            assert "fraud" not in item.finding.casefold()
            assert "fraud" not in item.explanation.casefold()
            assert "authenticity" not in item.finding.casefold() or "not" in item.explanation.casefold()
            image_facts = [fact for fact in item.evidence_facts if fact.key == "image_id"]
            if image_facts:
                assert str(image_facts[0].value)
        assert first.plan_claim_evidence is not None
        assert first.plan_claim_evidence.claim
        assert "meters" in first.plan_claim_evidence.evidence
        assert "does not prove" in first.plan_claim_evidence.note
        real_mode = parse_data_mode("REAL", project)
        real = check_project_geospatial(session, project, real_mode, persist=True)
        assert real.data_mode == DataMode.REAL
        assert real.project_location.available is False
        assert real.project_location.latitude is None
        hybrid_after = list_project_evidence(session, project.id, engine="geo", data_mode="HYBRID")
        assert hybrid_after
        real_items = list_project_evidence(session, project.id, engine="geo", data_mode="REAL")
        assert real_items
        assert all(item.provenance.enrichment_used is False for item in real_items)
        assert all("Not official MPLADS GPS" not in item.provenance.notes for item in real_items)
    finally:
        session.close()
