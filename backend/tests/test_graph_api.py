from __future__ import annotations

from datetime import date

from sqlalchemy import func, select

from app.db import get_session_factory
from app.engines.graph.constants import ENGINE_NAME
from app.engines.graph.service import assess_project_graph
from app.engines.overlap.embeddings import HashedTokenEmbedder
from app.models.evidence import EvidenceObjectRow
from app.models.fusion import FusionScore
from app.models.graph import GraphEdge
from app.models.project import Project

TANKS = "NA - Construction of water tanks"
SYNTHETIC_LABEL = "SYNTHETIC: relationship-graph unit test (not a government project)"


def _insert_project(session, **overrides: object) -> Project:
    values: dict[str, object] = {
        "internal_project_id": "internal:synthetic:graph:db:1",
        "internal_id_kind": "internal_surrogate_hash",
        "internal_id_scheme": "sarvsakshi_internal_work_v1",
        "source_dataset": "github_vonter_india-mplads-works_MPLADS.csv",
        "is_synthetic": True,
        "synthetic_label": SYNTHETIC_LABEL,
        "lifecycle_stage": "FUTURE",
        "state": "Andhra Pradesh",
        "constituency": "KURNOOL",
        "category": "Normal/Others",
        "work_description": TANKS,
        "source_work": TANKS,
        "mp_name": "Test MP",
        "ida": "Kurnool_IDA",
        "allocation_amount": 500_000,
        "recommended_date": date(2023, 6, 1),
        "status": "Unsanctioned",
    }
    values.update(overrides)
    row = Project(**values)
    session.add(row)
    session.flush()
    return row


def test_persist_writes_graph_edges_not_fusion(client) -> None:
    session = get_session_factory()()
    try:
        subject = _insert_project(session)
        _insert_project(
            session,
            internal_project_id="internal:synthetic:graph:db:2",
            allocation_amount=505_000,
            recommended_date=date(2023, 6, 5),
        )
        session.commit()
        result = assess_project_graph(
            session,
            subject.id,
            persist=True,
            embedder=HashedTokenEmbedder(),
        )
        evidence = session.scalars(
            select(EvidenceObjectRow).where(EvidenceObjectRow.engine == ENGINE_NAME)
        ).all()
        fusion_count = session.scalar(select(func.count()).select_from(FusionScore)) or 0
        assert fusion_count == 0
        assert evidence
        assert evidence[0].signal_type == "relationship_graph"
        if result.stats.similar_project_count:
            links = session.scalars(select(GraphEdge)).all()
            assert links
            assert all(item.edge_type == "SIMILAR_TO" for item in links)
    finally:
        session.close()


def test_graph_api(client) -> None:
    session = get_session_factory()()
    try:
        subject = _insert_project(session, internal_project_id="internal:synthetic:graph:api:subject")
        _insert_project(
            session,
            internal_project_id="internal:synthetic:graph:api:peer",
            allocation_amount=500_000,
        )
        session.commit()
        project_id = subject.id
    finally:
        session.close()

    missing = client.get("/api/v1/projects/999999/graph")
    assert missing.status_code == 404

    response = client.get(f"/api/v1/projects/{project_id}/graph")
    assert response.status_code == 200
    body = response.json()
    assert body["engine"] == ENGINE_NAME
    assert body["project_node"]["node_type"] == "PROJECT"
    assert "connected_nodes" in body
    assert "relationships" in body
    assert "relationship_strengths" in body
    assert "graph_findings" in body
    assert "graph_evidence" in body
    assert body["graph_evidence"]["kind"] in {
        "NORMAL_CONNECTIVITY",
        "HIGH_CONNECTIVITY",
        "POTENTIAL_PATTERN_OF_INTEREST",
        "INSUFFICIENT_EVIDENCE",
    }
    assert "fraud" not in body["explanation"].casefold()
    assert "fraud" not in str(body).casefold()
    assert body["signal_kind"] == "relationship_graph"
    assert body["gps_used"] is False
    assert "latitude" not in body["project_node"]["attributes"]
    assert "investigation_priority" not in body
