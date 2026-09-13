from __future__ import annotations

from app.domain.enums import DataMode, SignalType
from app.engines.image.constants import ENGINE_VERSION, TEST_WATERMARK
from app.engines.image.evaluate import evaluate_payload
from app.engines.image.service import upload_image
from app.evidence.adapters.image import analysis_to_evidence_objects
from app.evidence.repository import list_project_evidence
from app.evidence.validate import validate_evidence
from tests.image_fixtures import unique_png
from tests.image_test_support import insert_project, SYNTHETIC_LABEL


def test_evidence_objects_and_modes(client) -> None:
    from app.db import get_session_factory
    from app.engines.image.service import parse_data_mode

    session = get_session_factory()()
    try:
        real_project = insert_project(session, internal_project_id="internal:image:ev:real")
        hybrid_project = insert_project(session, internal_project_id="internal:image:ev:hybrid")
        synthetic_project = insert_project(
            session,
            internal_project_id="internal:image:ev:synthetic",
            is_synthetic=True,
            synthetic_label=SYNTHETIC_LABEL,
        )
        session.flush()
        real = upload_image(
            session,
            real_project,
            payload=unique_png(),
            filename="real.png",
            declared_mime="image/png",
            data_mode=DataMode.REAL,
        )
        hybrid = upload_image(
            session,
            hybrid_project,
            payload=unique_png(),
            filename="hybrid.png",
            declared_mime="image/png",
            data_mode=DataMode.HYBRID,
        )
        synthetic = upload_image(
            session,
            synthetic_project,
            payload=unique_png(),
            filename="synthetic.png",
            declared_mime="image/png",
            data_mode=parse_data_mode("REAL", synthetic_project),
        )
        session.commit()
        real_items = list_project_evidence(session, real_project.id, engine="image", data_mode="REAL")
        hybrid_items = list_project_evidence(session, hybrid_project.id, engine="image", data_mode="HYBRID")
        synthetic_items = list_project_evidence(session, synthetic_project.id, engine="image")
        assert real_items
        assert all(item.data_mode == DataMode.REAL for item in real_items)
        assert all(item.provenance.enrichment_used is False for item in real_items)
        assert all(item.source_type.value != "synthetic_test_record" for item in real_items)
        assert hybrid_items
        assert all(item.data_mode == DataMode.HYBRID for item in hybrid_items)
        assert all(item.provenance.enrichment_used is True for item in hybrid_items)
        assert synthetic_items
        assert all(item.data_mode == DataMode.SYNTHETIC for item in synthetic_items)
        assert all("SYNTHETIC" in item.provenance.notes for item in synthetic_items)
        assert TEST_WATERMARK.split("—")[0].strip() in "TEST DATA"
        for item in real_items + hybrid_items + synthetic_items:
            checked = validate_evidence(item)
            assert checked.engine_version == ENGINE_VERSION
            assert checked.engine_name == "image"
            assert "fraud" not in item.finding.casefold()
            assert str(real.id) in str(item.source_ids) or item.project_id != real_project.id or f"image:{real.id}" in item.source_ids
            authenticity = next(fact for fact in item.evidence_facts if fact.key == "advanced_authenticity")
            assert authenticity.value["result"] == "INCONCLUSIVE"
        assert any(item.signal_type in {SignalType.IMAGE_POTENTIAL_REUSE, SignalType.IMAGE_EXACT_DUPLICATE} for item in real_items)
        assert any(item.signal_type == SignalType.IMAGE_METADATA for item in real_items)
        assert any(item.signal_type == SignalType.IMAGE_QUALITY for item in real_items)
        assert real.data_mode == "REAL"
        assert hybrid.data_mode == "HYBRID"
        assert synthetic.data_mode == "SYNTHETIC"
    finally:
        session.close()


def test_analysis_to_evidence_is_deterministic(client) -> None:
    from app.db import get_session_factory

    session = get_session_factory()()
    try:
        project = insert_project(session, internal_project_id="internal:image:ev:det")
        session.flush()
        photo = upload_image(
            session,
            project,
            payload=unique_png(),
            filename="det.png",
            declared_mime="image/png",
            data_mode=DataMode.REAL,
        )
        first = evaluate_payload(session, photo, unique_png())
        second = evaluate_payload(session, photo, unique_png())
        assert first.content_sha256 == second.content_sha256
        assert first.ahash == second.ahash
        objects_a = analysis_to_evidence_objects(project, first)
        objects_b = analysis_to_evidence_objects(project, second)
        assert [item.evidence_id for item in objects_a] == [item.evidence_id for item in objects_b]
        for obj in objects_a:
            validate_evidence(obj)
    finally:
        session.close()
