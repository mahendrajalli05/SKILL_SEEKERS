from __future__ import annotations

from datetime import date

from app.domain.enums import DataMode, EvidenceDisposition, EvidenceFactKind, SourceType
from app.engines.compliance.service import assess_compliance
from app.engines.compliance.types import ComplianceContext, ComplianceMode
from app.engines.cost.peers import InMemoryPeerSource
from app.engines.cost.service import assess_cost
from app.engines.cost.types import CostAssessmentOutcome, PeerRecord
from app.engines.cost.work_type import derive_work_type
from app.engines.overlap.embeddings import HashedTokenEmbedder
from app.engines.overlap.service import assess_overlap
from app.engines.overlap.types import OverlapMode, OverlapRecord
from app.engines.overlap.text import constituency_fields, embedding_text, rare_block_tokens
from app.engines.time.peers import InMemoryTimePeerSource
from app.engines.time.service import assess_time
from app.engines.time.types import TimeAssessmentOutcome, TimeMode, TimePeerRecord
from app.evidence.adapters.compliance import compliance_result_to_evidence
from app.evidence.adapters.cost import cost_result_to_evidence
from app.evidence.adapters.overlap import overlap_result_to_evidence
from app.evidence.adapters.time import time_result_to_evidence
from app.evidence.constants import FORBIDDEN_EVIDENCE_INPUT_COLUMNS
from app.evidence.validate import validate_evidence
from app.models.project import Project

TANKS = "NA - Construction of water tanks"


def _project(**overrides: object) -> Project:
    values: dict[str, object] = {
        "internal_project_id": "internal:evidence:1",
        "internal_id_kind": "internal_surrogate_hash",
        "internal_id_scheme": "sarvsakshi_internal_work_v1",
        "source_dataset": "github_vonter_india-mplads-works_MPLADS.csv",
        "is_synthetic": False,
        "lifecycle_stage": "FUTURE",
        "state": "Andhra Pradesh",
        "constituency": "KURNOOL",
        "category": "Normal/Others",
        "work_description": TANKS,
        "allocation_amount": 267_000,
        "status": "Unsanctioned",
    }
    values.update(overrides)
    return Project(**values)


def _peer(project_id: int, amount: int, **overrides: object) -> PeerRecord:
    values: dict[str, object] = {
        "project_id": project_id,
        "internal_project_id": f"internal:evidence:cost:{project_id}",
        "constituency": "KURNOOL",
        "category": "Normal/Others",
        "state": "Andhra Pradesh",
        "work_description": TANKS,
        "derived_work_type": derive_work_type(TANKS),
        "allocation_amount": amount,
        "recommended_date": date(2023, 6, 1),
        "is_synthetic": False,
    }
    values.update(overrides)
    return PeerRecord(**values)


def _time_record(project_id: int, **overrides: object) -> TimePeerRecord:
    values: dict[str, object] = {
        "project_id": project_id,
        "internal_project_id": f"internal:evidence:time:{project_id}",
        "constituency": "KURNOOL",
        "category": "Normal/Others",
        "state": "Andhra Pradesh",
        "work_description": TANKS,
        "derived_work_type": derive_work_type(TANKS),
        "status": "Unsanctioned",
        "lifecycle_stage": "FUTURE",
        "recommended_date": date(2023, 6, 1),
        "time_mode": TimeMode.REAL,
    }
    values.update(overrides)
    return TimePeerRecord(**values)


def _overlap_record(project_id: int, **overrides: object) -> OverlapRecord:
    constituency = str(overrides.get("constituency", "KURNOOL"))
    work = str(overrides.get("source_work", TANKS))
    value, usable, kind, _reason = constituency_fields(constituency)
    values: dict[str, object] = {
        "project_id": project_id,
        "internal_project_id": f"internal:evidence:overlap:{project_id}",
        "source_work": work,
        "work_description": work,
        "embedding_text": embedding_text(work),
        "category": "Normal/Others",
        "constituency": value,
        "constituency_usable": usable,
        "constituency_kind": kind,
        "state": "Andhra Pradesh",
        "allocation_amount": 500_000,
        "recommended_date": date(2023, 6, 1),
        "place_text": "",
        "rare_tokens": rare_block_tokens(work),
    }
    values.update(overrides)
    return OverlapRecord(**values)


def _compliance_ctx(**overrides: object) -> ComplianceContext:
    values: dict[str, object] = {
        "project_id": 1,
        "internal_project_id": "internal:evidence:compliance:1",
        "mode": ComplianceMode.REAL,
        "mp_name": "Test MP",
        "work_description": TANKS,
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
        "ida_approval": "Approved by IDA",
        "status": "Unsanctioned",
        "house": "Lok Sabha",
        "lifecycle_stage": "FUTURE",
    }
    values.update(overrides)
    return ComplianceContext(**values)


def test_cost_why_not_flagged_and_observation_split() -> None:
    subject = _peer(1, 500_000)
    peers = [_peer(10 + i, 480_000 + i * 5_000) for i in range(8)]
    result = assess_cost(subject, InMemoryPeerSource([subject, *peers]))
    assert result.outcome == CostAssessmentOutcome.WITHIN_PEER_RANGE
    project = _project(internal_project_id=subject.internal_project_id)
    obj = validate_evidence(cost_result_to_evidence(result, project))
    assert obj.disposition == EvidenceDisposition.WHY_NOT_FLAGGED
    assert obj.data_mode == DataMode.REAL
    assert obj.score == result.cost_anomaly_score
    assert abs(obj.confidence - result.evidence_confidence / 100) < 1e-9
    keys = {fact.key: fact for fact in obj.evidence_facts}
    assert keys["actual_amount"].kind == EvidenceFactKind.OBSERVATION
    assert keys["cost_anomaly_score"].kind == EvidenceFactKind.DERIVED
    assert "Actual allocation" in (keys["actual_amount"].statement or "")
    assert subject.internal_project_id in obj.source_ids
    assert obj.provenance.source_dataset
    assert fact_keys_exclude_labels(obj)


def test_cost_why_flagged() -> None:
    subject = _peer(1, 5_000_000)
    peers = [_peer(10 + i, 450_000) for i in range(8)]
    result = assess_cost(subject, InMemoryPeerSource([subject, *peers]))
    assert result.flagged is True
    obj = cost_result_to_evidence(result, _project(internal_project_id=subject.internal_project_id))
    assert obj.disposition == EvidenceDisposition.WHY_FLAGGED
    assert "above peer median" in obj.finding or "below peer median" in obj.finding
    assert result.why_flagged is not None
    assert obj.explanation == result.explanation


def test_cost_inconclusive_insufficient_peers() -> None:
    subject = _peer(1, 500_000)
    result = assess_cost(subject, InMemoryPeerSource([subject]))
    obj = cost_result_to_evidence(result, _project(internal_project_id=subject.internal_project_id))
    assert obj.disposition == EvidenceDisposition.INCONCLUSIVE
    assert obj.score is None


def test_cost_not_assessable_invalid_amount() -> None:
    subject = _peer(1, 0)
    result = assess_cost(subject, InMemoryPeerSource([subject]))
    obj = cost_result_to_evidence(result, _project(internal_project_id=subject.internal_project_id))
    assert obj.disposition == EvidenceDisposition.NOT_ASSESSABLE
    assert obj.score is None


def test_time_real_is_not_assessable() -> None:
    subject = _time_record(1)
    result = assess_time(subject, InMemoryTimePeerSource([subject]))
    assert result.outcome == TimeAssessmentOutcome.INSUFFICIENT_EVIDENCE
    project = _project(internal_project_id=subject.internal_project_id)
    obj = time_result_to_evidence(result, project)
    assert obj.data_mode == DataMode.REAL
    assert obj.disposition == EvidenceDisposition.NOT_ASSESSABLE
    assert obj.source_type == SourceType.MPLADS_PROJECT_RECORD
    assert obj.provenance.enrichment_used is False


def test_time_hybrid_why_flagged_is_hybrid() -> None:
    subject = _time_record(
        1,
        time_mode=TimeMode.HYBRID_TEST,
        status="Ongoing",
        lifecycle_stage="ONGOING",
        planned_start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 4, 1),
        actual_start_date=date(2024, 1, 1),
        actual_completion_date=None,
        physical_progress_percent=12,
        as_of_date=date(2024, 6, 30),
    )
    result = assess_time(subject, InMemoryTimePeerSource([subject]))
    assert result.flagged is True
    project = _project(internal_project_id=subject.internal_project_id)
    obj = time_result_to_evidence(result, project)
    assert obj.data_mode == DataMode.HYBRID
    assert obj.disposition == EvidenceDisposition.WHY_FLAGGED
    assert obj.provenance.enrichment_used is True
    assert obj.source_type == SourceType.HYBRID_ENRICHMENT
    assert fact_keys_exclude_labels(obj)


def test_time_hybrid_why_not_flagged() -> None:
    subject = _time_record(
        1,
        time_mode=TimeMode.HYBRID_TEST,
        status="Completed",
        lifecycle_stage="COMPLETED",
        planned_start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 4, 10),
        actual_start_date=date(2024, 1, 1),
        actual_completion_date=date(2024, 4, 10),
        physical_progress_percent=100,
        as_of_date=date(2024, 6, 30),
    )
    result = assess_time(subject, InMemoryTimePeerSource([subject]))
    obj = time_result_to_evidence(result, _project(internal_project_id=subject.internal_project_id))
    assert obj.disposition == EvidenceDisposition.WHY_NOT_FLAGGED
    assert obj.data_mode == DataMode.HYBRID


def test_overlap_compatibility_and_source_ids() -> None:
    subject = _overlap_record(1)
    peer = _overlap_record(2, allocation_amount=505_000)
    result = assess_overlap(subject, [subject, peer], mode=OverlapMode.REAL, embedder=HashedTokenEmbedder())
    project = _project(internal_project_id=subject.internal_project_id)
    obj = overlap_result_to_evidence(result, project)
    assert obj.signal_type.value == "potential_overlap"
    assert obj.data_mode == DataMode.REAL
    assert subject.internal_project_id in obj.source_ids
    assert obj.explanation == result.explanation
    assert fact_keys_exclude_labels(obj)
    if result.flagged:
        assert obj.disposition == EvidenceDisposition.WHY_FLAGGED
    elif result.outcome.value == "INSUFFICIENT_EVIDENCE":
        assert obj.disposition == EvidenceDisposition.INCONCLUSIVE
    else:
        assert obj.disposition == EvidenceDisposition.WHY_NOT_FLAGGED


def test_compliance_real_preserves_rule_sources() -> None:
    result = assess_compliance(_compliance_ctx())
    project = _project(internal_project_id=result.internal_project_id)
    obj = compliance_result_to_evidence(result, project)
    assert obj.disposition in {
        EvidenceDisposition.WHY_NOT_FLAGGED,
        EvidenceDisposition.NOT_ASSESSABLE,
        EvidenceDisposition.WHY_FLAGGED,
    }
    keys = {fact.key: fact for fact in obj.evidence_facts}
    assert "not_assessable_rule_ids" in keys
    assert "rule_results" in keys
    assert obj.guideline_refs
    assert result.internal_project_id in obj.source_ids
    assert fact_keys_exclude_labels(obj)
    assert obj.data_mode == DataMode.REAL


def test_compliance_why_flagged_hybrid_spend() -> None:
    result = assess_compliance(
        _compliance_ctx(
            mode=ComplianceMode.HYBRID_TEST,
            status="Completed",
            lifecycle_stage="COMPLETED",
            sanction_date=date(2023, 6, 20),
            sanctioned_amount=500_000,
            expenditure_amount=900_000,
            as_of_date=date(2024, 6, 30),
        )
    )
    project = _project(internal_project_id=result.internal_project_id)
    obj = compliance_result_to_evidence(result, project)
    assert obj.data_mode == DataMode.HYBRID
    assert obj.disposition == EvidenceDisposition.WHY_FLAGGED
    assert "R004" in obj.rule_ids or any(
        "R004" in str(fact.value) for fact in obj.evidence_facts if fact.key == "triggered_rule_ids"
    )


def test_synthetic_project_is_not_real() -> None:
    subject = _peer(1, 500_000)
    peers = [_peer(10 + i, 500_000) for i in range(8)]
    result = assess_cost(subject, InMemoryPeerSource([subject, *peers]))
    project = _project(
        internal_project_id=subject.internal_project_id,
        is_synthetic=True,
        synthetic_label="SYNTHETIC: unit test (not a government project)",
    )
    obj = cost_result_to_evidence(result, project)
    assert obj.data_mode == DataMode.SYNTHETIC
    assert obj.source_type == SourceType.SYNTHETIC_TEST_RECORD
    assert "SYNTHETIC" in obj.provenance.notes


def fact_keys_exclude_labels(obj) -> bool:
    keys = {fact.key for fact in obj.evidence_facts}
    assert keys.isdisjoint(FORBIDDEN_EVIDENCE_INPUT_COLUMNS)
    blob = (obj.finding + obj.explanation).casefold()
    for column in ("scenario_type", "demo_case_id", "mixed_signals", "anomaly_notes"):
        assert column not in blob
    return True
