from __future__ import annotations

from sqlalchemy import inspect, text

from app.db import check_connection, get_engine
from app.models import Base
from app.models.fusion import FusionScore
from app.models.project import Project
from app.pipeline.db_load import FORBIDDEN_PROJECT_COLUMNS


def test_sqlite_select_one(client) -> None:
    assert check_connection() is True
    with get_engine().connect() as connection:
        value = connection.execute(text("SELECT 1")).scalar()
    assert value == 1


def test_expected_tables_exist(client) -> None:
    names = set(inspect(get_engine()).get_table_names())
    expected = {
        "dataset_snapshot",
        "implementing_agency",
        "project",
        "document",
        "photo",
        "photo_details",
        "claim",
        "plan",
    "plan_artifact",
        "guideline_rule",
        "guideline_snippet",
        "evidence_object",
        "evidence_fact",
        "overlap_link",
        "graph_edge",
        "fusion_score",
        "officer_decision",
        "audit_event",
        "copilot_turn",
        "citizen_report",
        "lifecycle_workflow",
        "lifecycle_decision",
        "fusion_score_v2",
        "milestone",
        "external_source",
        "external_context_snapshot",
        "external_context_observation",
    }
    assert expected.issubset(names)


def test_fusion_score_has_priority_and_confidence_not_fraud(client) -> None:
    columns = {column.name for column in FusionScore.__table__.columns}
    assert "investigation_priority" in columns
    assert "evidence_confidence" in columns
    assert "fraud_probability" not in columns
    assert "fraud_score" not in columns


def test_project_observed_fields_are_nullable(client) -> None:
    nullable = {column.name for column in Project.__table__.columns if column.nullable}
    for field in (
        "source_mp_name",
        "source_work",
        "mp_name",
        "work_description",
        "category",
        "state",
        "constituency",
        "ida",
        "city",
        "ward",
        "block",
        "village",
        "allocation_amount",
        "recommended_date",
        "status",
        "house",
    ):
        assert field in nullable


def test_project_does_not_invent_absent_government_fields(client) -> None:
    columns = {column.name for column in Project.__table__.columns}
    assert "internal_project_id" in columns
    assert not (columns & FORBIDDEN_PROJECT_COLUMNS)


def test_metadata_matches_base(client) -> None:
    assert "project" in Base.metadata.tables
