from __future__ import annotations

from app.domain.enums import DataMode, SignalType
from app.engines.need.evaluate import evaluate_need_impact
from app.evidence.adapters.need import result_to_evidence_objects
from app.evidence.validate import validate_evidence
from app.models.project import Project
from tests.need_test_support import high_need_enrichment, sample_inputs


def _project(**overrides: object) -> Project:
    values: dict[str, object] = {
        "id": 11,
        "internal_project_id": "internal:need-impact:subject",
        "internal_id_kind": "internal_surrogate_hash",
        "internal_id_scheme": "sarvsakshi_internal_work_v1",
        "source_dataset": "github_vonter_india-mplads-works_MPLADS.csv",
        "is_synthetic": False,
        "lifecycle_stage": "FUTURE",
        "state": "Andhra Pradesh",
        "constituency": "VIZIANAGARAM",
        "category": "Drinking Water",
        "work_description": "Construction of drinking water facility",
        "allocation_amount": 2_000_000,
        "status": "Unsanctioned",
    }
    values.update(overrides)
    return Project(**values)


def test_real_evidence_objects_validate_and_are_inconclusive() -> None:
    result = evaluate_need_impact(sample_inputs(data_mode=DataMode.REAL, project_id=11))
    objects = result_to_evidence_objects(_project(), result)
    types = {obj.signal_type for obj in objects}
    assert types == {
        SignalType.NEED_ASSESSMENT,
        SignalType.IMPACT_ASSESSMENT,
        SignalType.PRIORITY_ASSESSMENT,
    }
    for obj in objects:
        checked = validate_evidence(obj)
        assert checked.data_mode == DataMode.REAL
        assert checked.provenance.enrichment_used is False
        assert "fraud" not in checked.explanation.casefold()
        assert "sanction approved" not in checked.explanation.casefold()
        assert checked.engine_name == "need"
    priority = next(obj for obj in objects if obj.signal_type == SignalType.PRIORITY_ASSESSMENT)
    assert priority.disposition.value == "INCONCLUSIVE"


def test_hybrid_evidence_labels_synthetic_and_keeps_provenance() -> None:
    result = evaluate_need_impact(
        sample_inputs(
            project_id=11,
            data_mode=DataMode.HYBRID,
            enrichment=high_need_enrichment("internal:need-impact:subject"),
        )
    )
    objects = result_to_evidence_objects(_project(), result)
    for obj in objects:
        checked = validate_evidence(obj)
        assert checked.data_mode == DataMode.HYBRID
        assert checked.provenance.enrichment_used is True
        assert "SYNTHETIC" in checked.provenance.notes.upper() or "TEST/SYNTHETIC" in checked.provenance.notes
        assert checked.provenance.internal_project_id in checked.source_ids
