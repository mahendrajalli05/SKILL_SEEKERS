from __future__ import annotations

from sqlalchemy import inspect, text

from app.db import check_connection, get_engine
from app.models import Base
from app.models.fusion import FusionScore
from app.models.project import Project


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
    }
    assert expected.issubset(names)


def test_fusion_score_has_priority_and_confidence_not_fraud(client) -> None:
    columns = {column.name for column in FusionScore.__table__.columns}
    assert "investigation_priority" in columns
    assert "evidence_confidence" in columns
    assert "fraud_probability" not in columns
    assert "fraud_score" not in columns


def test_project_dump_fields_are_nullable(client) -> None:
    nullable = {
        column.name
        for column in Project.__table__.columns
        if column.nullable
    }
    for field in (
        "unique_work_number",
        "work_name",
        "work_description",
        "work_category",
        "state",
        "implementing_district",
        "constituency",
        "house_name",
        "mp_name",
        "amount",
        "recommended_amount",
        "sanctioned_amount",
        "utilised_amount",
        "recommendation_date",
        "sanction_date",
        "date_of_completion",
        "work_status",
        "village_or_place",
    ):
        assert field in nullable


def test_metadata_matches_base(client) -> None:
    assert "project" in Base.metadata.tables
