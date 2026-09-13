from __future__ import annotations

from datetime import date

from app.domain.enums import DataMode, EvidenceDisposition, SignalType, SourceType
from app.engines.graph.constants import ENGINE_NAME, ENGINE_VERSION, FORBIDDEN_MODEL_INPUT_COLUMNS
from app.engines.graph.service import assess_graph
from app.engines.graph.types import GraphFindingKind, GraphMode
from app.engines.overlap.embeddings import HashedTokenEmbedder
from app.evidence.adapters.graph import graph_result_to_evidence
from app.evidence.constants import FORBIDDEN_EVIDENCE_INPUT_COLUMNS
from app.evidence.validate import validate_evidence
from app.models.project import Project

from tests.test_graph_engine import TANKS, _record


def _project(**overrides: object) -> Project:
    values: dict[str, object] = {
        "id": 1,
        "internal_project_id": "internal:synthetic:graph:1",
        "internal_id_kind": "internal_surrogate_hash",
        "internal_id_scheme": "sarvsakshi_internal_work_v1",
        "source_dataset": "github_vonter_india-mplads-works_MPLADS.csv",
        "is_synthetic": False,
        "lifecycle_stage": "FUTURE",
        "state": "Andhra Pradesh",
        "constituency": "KURNOOL",
        "category": "Normal/Others",
        "work_description": TANKS,
        "mp_name": "Test MP",
        "ida": "Kurnool_IDA",
        "allocation_amount": 500_000,
        "status": "Unsanctioned",
    }
    values.update(overrides)
    return Project(**values)


def test_evidence_object_generation() -> None:
    subject = _record(1)
    other = _record(2, rec_date=date(2023, 6, 8))
    result = assess_graph(subject, [subject, other], embedder=HashedTokenEmbedder())
    project = _project()
    obj = graph_result_to_evidence(result, project)
    checked = validate_evidence(obj)
    assert checked.signal_type == SignalType.RELATIONSHIP_GRAPH
    assert checked.engine_name == ENGINE_NAME
    assert checked.engine_version == ENGINE_VERSION
    assert checked.data_mode == DataMode.REAL
    assert checked.source_type == SourceType.MPLADS_PROJECT_RECORD
    assert checked.provenance.enrichment_used is False
    assert subject.internal_project_id in checked.source_ids
    assert "fraud" not in checked.finding.casefold()
    assert "fraud" not in checked.explanation.casefold()
    fact_keys = {fact.key for fact in checked.evidence_facts}
    assert fact_keys.isdisjoint(FORBIDDEN_EVIDENCE_INPUT_COLUMNS)
    assert fact_keys.isdisjoint(FORBIDDEN_MODEL_INPUT_COLUMNS)


def test_evidence_pattern_is_why_flagged() -> None:
    subject = _record(1)
    corpus = [subject]
    for index in range(2, 8):
        corpus.append(_record(index, rec_date=date(2023, 6, index)))
    result = assess_graph(subject, corpus, embedder=HashedTokenEmbedder())
    assert result.finding_kind == GraphFindingKind.POTENTIAL_PATTERN_OF_INTEREST
    project = _project()
    obj = validate_evidence(graph_result_to_evidence(result, project))
    assert obj.disposition == EvidenceDisposition.WHY_FLAGGED
    assert "Potential Pattern of Interest" in obj.finding


def test_hybrid_evidence_is_distinguishable() -> None:
    subject = _record(1)
    result = assess_graph(
        subject,
        [subject, _record(2)],
        mode=GraphMode.HYBRID_TEST,
        embedder=HashedTokenEmbedder(),
    )
    project = _project()
    obj = validate_evidence(graph_result_to_evidence(result, project))
    assert obj.data_mode == DataMode.HYBRID
    assert obj.source_type == SourceType.HYBRID_ENRICHMENT
    assert obj.provenance.enrichment_used is True
    assert obj.data_mode != DataMode.REAL or obj.source_type != SourceType.SYNTHETIC_TEST_RECORD
    fact_keys = {fact.key for fact in obj.evidence_facts}
    assert "scenario_type" not in fact_keys
    assert "overlap_group_id" not in fact_keys
    assert "latitude" not in fact_keys
    assert "longitude" not in fact_keys


def test_synthetic_project_evidence_is_labelled() -> None:
    subject = _record(1)
    result = assess_graph(subject, [subject], embedder=HashedTokenEmbedder())
    project = _project(is_synthetic=True, synthetic_label="SYNTHETIC graph fixture")
    obj = validate_evidence(graph_result_to_evidence(result, project))
    assert obj.data_mode == DataMode.SYNTHETIC
    assert "SYNTHETIC" in obj.provenance.notes
    assert obj.source_type == SourceType.SYNTHETIC_TEST_RECORD
