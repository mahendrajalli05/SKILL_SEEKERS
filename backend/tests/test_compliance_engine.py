from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_session_factory
from app.engines.compliance.constants import (
    ENGINE_VERSION,
    FORBIDDEN_MODEL_INPUT_COLUMNS,
    HYBRID_TEST_NOTE,
    REAL_LIMITATION_NOTE,
)
from app.engines.compliance.context import context_from_project
from app.engines.compliance.enrichment import HybridComplianceFields, assert_no_label_fields
from app.engines.compliance.loader import load_rules
from app.engines.compliance.service import assess_compliance, assess_project_compliance
from app.engines.compliance.types import (
    ComplianceContext,
    ComplianceMode,
    ComplianceStatus,
    RuleResultStatus,
)
from app.models.evidence import EvidenceObjectRow
from app.models.fusion import FusionScore
from app.models.project import Project

SYNTHETIC_LABEL = "SYNTHETIC: compliance-engine unit test (not a government project)"
RULESET = load_rules()


def _ctx(**overrides: object) -> ComplianceContext:
    values: dict[str, object] = {
        "project_id": 1,
        "internal_project_id": "internal:test:compliance:engine",
        "mode": ComplianceMode.REAL,
        "mp_name": "Test MP",
        "work_description": "NA - Construction of water tanks",
        "category": "Normal/Others",
        "state": "Andhra Pradesh",
        "constituency": "KURNOOL",
        "ida": "KURNOOL_IDA",
        "city": "",
        "ward": "",
        "block": "",
        "village": "",
        "recommended_date": date(2023, 6, 1),
        "allocation_amount": 500_000,
        "ida_approval": "Action Pending",
        "status": "Unsanctioned",
        "house": "Lok Sabha",
        "lifecycle_stage": "FUTURE",
    }
    values.update(overrides)
    return ComplianceContext(**values)


def test_deterministic_results() -> None:
    context = _ctx(
        mode=ComplianceMode.HYBRID_TEST,
        sanction_date=date(2023, 8, 1),
        sanctioned_amount=100,
        expenditure_amount=200,
        as_of_date=date(2024, 6, 30),
    )
    first = assess_compliance(context, RULESET)
    second = assess_compliance(context, RULESET)
    assert [item.rule_id for item in first.rule_results] == [item.rule_id for item in second.rule_results]
    assert [item.status for item in first.rule_results] == [item.status for item in second.rule_results]
    assert first.explanation == second.explanation
    assert first.triggered_rule_ids == second.triggered_rule_ids
    assert first.compliance_status == second.compliance_status


def test_context_and_result_exclude_leakage_fields() -> None:
    fields = set(ComplianceContext.__dataclass_fields__)
    assert fields.isdisjoint(FORBIDDEN_MODEL_INPUT_COLUMNS)
    hybrid = HybridComplianceFields(
        internal_project_id="internal:x",
        sanction_date=date(2023, 6, 20),
        planned_start_date=None,
        planned_completion_date=None,
        actual_start_date=None,
        actual_completion_date=None,
        sanctioned_amount=100,
        expenditure_amount=90,
        physical_progress_percent=0,
        as_of_date=date(2024, 6, 30),
    )
    assert_no_label_fields(hybrid)
    result = assess_compliance(_ctx(mode=ComplianceMode.HYBRID_TEST, sanction_date=date(2023, 6, 20)), RULESET)
    blob = result.explanation.casefold()
    for token in ("scenario_type", "demo_case_id", "anomaly_notes", "overlap_group", "coordinate_source"):
        assert token not in blob
    assert "fraud" not in blob


def test_real_context_does_not_fabricate_unavailable_fields() -> None:
    result = assess_compliance(_ctx(mode=ComplianceMode.REAL), RULESET)
    by_id = {item.rule_id: item for item in result.rule_results}
    assert by_id["R001"].status == RuleResultStatus.NOT_ASSESSABLE
    assert by_id["R002"].status == RuleResultStatus.NOT_ASSESSABLE
    assert by_id["R003"].status == RuleResultStatus.NOT_ASSESSABLE
    assert by_id["R004"].status == RuleResultStatus.NOT_ASSESSABLE
    assert by_id["R005"].status == RuleResultStatus.NOT_ASSESSABLE
    assert by_id["R007"].status == RuleResultStatus.NOT_ASSESSABLE
    assert by_id["R008"].status == RuleResultStatus.NOT_ASSESSABLE
    assert by_id["R009"].status == RuleResultStatus.NOT_ASSESSABLE
    assert by_id["R014"].status == RuleResultStatus.NOT_ASSESSABLE
    assert result.rule_results[0].evidence.get("sanction_date") in (None, None)
    assert "amount_unit" in by_id["R014"].missing_fields
    assert REAL_LIMITATION_NOTE in result.explanation


def test_hybrid_note_is_present_when_synthetic_fields_used() -> None:
    result = assess_compliance(
        _ctx(
            mode=ComplianceMode.HYBRID_TEST,
            sanction_date=date(2023, 6, 20),
            sanctioned_amount=100,
            expenditure_amount=90,
            as_of_date=date(2024, 6, 30),
        ),
        RULESET,
    )
    assert result.dataset_type == "HYBRID"
    assert HYBRID_TEST_NOTE in result.explanation
    assert result.compliance_mode == ComplianceMode.HYBRID_TEST


def test_source_reference_preserved_on_every_result() -> None:
    result = assess_compliance(_ctx(), RULESET)
    for item in result.rule_results:
        assert item.source_reference["document"]
        assert item.source_reference["url"]
        assert item.source_reference["quote"]
        assert item.source_reference["source_id"]


def test_explanation_does_not_use_fraud() -> None:
    result = assess_compliance(
        _ctx(
            mode=ComplianceMode.HYBRID_TEST,
            sanction_date=date(2023, 9, 1),
            sanctioned_amount=100,
            expenditure_amount=250,
            as_of_date=date(2024, 6, 30),
        ),
        RULESET,
    )
    assert "fraud" not in result.explanation.casefold()
    for item in result.rule_results:
        assert "fraud" not in item.explanation.casefold()
        assert item.rule_id in item.explanation or item.status == RuleResultStatus.NOT_ASSESSABLE


def _insert_project(session: Session, **overrides: object) -> Project:
    values: dict[str, object] = {
        "internal_project_id": "internal:synthetic:compliance:db:1",
        "internal_id_kind": "internal_surrogate_hash",
        "internal_id_scheme": "sarvsakshi_internal_work_v1",
        "is_synthetic": True,
        "synthetic_label": SYNTHETIC_LABEL,
        "lifecycle_stage": "FUTURE",
        "state": "Andhra Pradesh",
        "constituency": "KURNOOL",
        "category": "Normal/Others",
        "work_description": "NA - Construction of water tanks",
        "allocation_amount": 500_000,
        "recommended_date": date(2023, 6, 1),
        "status": "Unsanctioned",
        "ida": "KURNOOL_IDA",
        "ida_approval": "Action Pending",
        "house": "Lok Sabha",
    }
    values.update(overrides)
    row = Project(**values)
    session.add(row)
    session.flush()
    return row


def test_project_mapper_does_not_fabricate_hybrid_fields(client) -> None:
    session = get_session_factory()()
    try:
        row = _insert_project(session, internal_project_id="internal:synthetic:compliance:ctx")
        session.commit()
        context = context_from_project(row, mode=ComplianceMode.REAL)
        assert context.sanction_date is None
        assert context.expenditure_amount is None
        assert context.actual_completion_date is None
        assert context.amount_unit is None
        assert context.verified_work_district is None
        assert context.vendor_name is None
        assert context.latitude is None
        assert context.mode == ComplianceMode.REAL
    finally:
        session.close()


def test_persists_compliance_evidence_not_fusion(client) -> None:
    session = get_session_factory()()
    try:
        subject = _insert_project(session, internal_project_id="internal:synthetic:compliance:db:subject")
        session.commit()
        result = assess_project_compliance(
            session,
            subject.id,
            mode=ComplianceMode.REAL,
            persist=True,
        )
        assert result.compliance_status in {
            ComplianceStatus.NO_RULES_TRIGGERED,
            ComplianceStatus.INCONCLUSIVE,
            ComplianceStatus.RULES_TRIGGERED,
        }
        stored = session.scalars(
            select(EvidenceObjectRow).where(EvidenceObjectRow.project_id == subject.id)
        ).all()
        assert len(stored) == 1
        assert stored[0].engine == "compliance"
        assert stored[0].engine_version == ENGINE_VERSION
        keys = {fact.key for fact in stored[0].facts}
        assert {
            "compliance_status",
            "triggered_rule_ids",
            "not_assessable_rule_ids",
            "rule_results",
            "dataset_type",
        }.issubset(keys)
        fusion_count = session.scalar(select(func.count()).select_from(FusionScore)) or 0
        assert fusion_count == 0
    finally:
        session.close()


def test_compliance_api_real_mode(client) -> None:
    session = get_session_factory()()
    try:
        subject = _insert_project(session, internal_project_id="internal:synthetic:compliance:api:subject")
        session.commit()
        project_id = subject.id
    finally:
        session.close()

    missing = client.get("/api/v1/projects/999999/compliance")
    assert missing.status_code == 404

    response = client.get(f"/api/v1/projects/{project_id}/compliance")
    assert response.status_code == 200
    body = response.json()
    assert body["engine"] == "compliance"
    assert body["compliance_mode"] == "REAL"
    assert body["dataset_type"] == "REAL"
    assert "triggered_rules" in body
    assert "not_assessable_rules" in body
    assert "non_triggered_rules" in body
    assert any(item["status"] == "NOT_ASSESSABLE" for item in body["not_assessable_rules"])
    assert "fraud" not in str(body).casefold()


def test_compliance_api_hybrid_mode(client) -> None:
    session = get_session_factory()()
    try:
        subject = _insert_project(session, internal_project_id="internal:synthetic:compliance:api:hybrid")
        session.commit()
        project_id = subject.id
        hybrid = {
            subject.internal_project_id: HybridComplianceFields(
                internal_project_id=subject.internal_project_id,
                sanction_date=date(2023, 8, 15),
                planned_start_date=date(2023, 9, 1),
                planned_completion_date=date(2024, 3, 1),
                actual_start_date=date(2023, 9, 1),
                actual_completion_date=None,
                sanctioned_amount=500_000,
                expenditure_amount=0,
                physical_progress_percent=0,
                as_of_date=date(2024, 6, 30),
            )
        }
        result = assess_project_compliance(
            session,
            project_id,
            mode=ComplianceMode.HYBRID_TEST,
            persist=False,
            hybrid_fields=hybrid,
        )
        assert result.dataset_type == "HYBRID"
        assert "R001" in result.triggered_rule_ids
        assert HYBRID_TEST_NOTE in result.explanation
    finally:
        session.close()
