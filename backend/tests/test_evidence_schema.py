from __future__ import annotations

from app.domain.enums import (
    DataMode,
    EvidenceDisposition,
    EvidenceEngine,
    EvidenceFactKind,
    EvidenceSeverity,
    SignalType,
    SourceType,
)
from app.domain.schemas.evidence import EvidenceFact, EvidenceObject, EvidenceProvenance
from app.evidence.constants import FUTURE_SIGNAL_TYPES
from app.evidence.errors import EvidenceValidationError
from app.evidence.ids import make_evidence_id
from app.evidence.validate import parse_and_validate, validate_evidence


def _provenance(**overrides: object) -> EvidenceProvenance:
    values: dict[str, object] = {
        "data_mode": DataMode.REAL,
        "source_type": SourceType.MPLADS_PROJECT_RECORD,
        "source_ids": ["internal:abc"],
        "internal_project_id": "internal:abc",
        "notes": "real MPLADS project records from the cleaned work-level extract.",
        "source_dataset": "github_vonter_india-mplads-works_MPLADS.csv",
        "source_url": "https://example.invalid/mplads.csv",
    }
    values.update(overrides)
    return EvidenceProvenance(**values)


def valid_evidence(**overrides: object) -> EvidenceObject:
    values: dict[str, object] = {
        "evidence_id": make_evidence_id(
            engine_name="cost",
            engine_version="cost-peer-v1.1",
            project_id=3715,
            signal_type="allocation_cost_anomaly",
            data_mode="REAL",
        ),
        "project_id": 3715,
        "signal_type": SignalType.ALLOCATION_COST_ANOMALY,
        "finding": "Allocation is 33.5% above peer median",
        "severity": EvidenceSeverity.INFO,
        "score": 21,
        "confidence": 0.42,
        "source_type": SourceType.MPLADS_PROJECT_RECORD,
        "source_ids": ["internal:abc"],
        "evidence_facts": [
            EvidenceFact(
                key="actual_amount",
                value=267000,
                source="project.allocation_amount",
                kind=EvidenceFactKind.OBSERVATION,
                statement="Actual allocation = 267,000",
            ),
            EvidenceFact(
                key="cost_anomaly_score",
                value=21,
                source="cost-peer-v1.1",
                kind=EvidenceFactKind.DERIVED,
            ),
        ],
        "explanation": "Allocation is 33.5% above the median of 329 comparable works.",
        "engine_name": EvidenceEngine.COST,
        "engine_version": "cost-peer-v1.1",
        "data_mode": DataMode.REAL,
        "provenance": _provenance(),
        "disposition": EvidenceDisposition.WHY_NOT_FLAGGED,
    }
    values.update(overrides)
    return EvidenceObject(**values)


def test_required_fields_are_present() -> None:
    obj = validate_evidence(valid_evidence())
    for field in (
        "evidence_id",
        "project_id",
        "signal_type",
        "finding",
        "severity",
        "confidence",
        "source_type",
        "source_ids",
        "evidence_facts",
        "explanation",
        "engine_name",
        "engine_version",
        "data_mode",
        "provenance",
    ):
        assert getattr(obj, field) is not None
    assert obj.score == 21
    assert obj.confidence == 0.42
    assert obj.provenance.source_ids == ["internal:abc"]


def test_score_is_optional() -> None:
    obj = validate_evidence(valid_evidence(score=None))
    assert obj.score is None


def test_observation_and_derived_facts_are_distinct() -> None:
    obj = valid_evidence()
    kinds = {fact.key: fact.kind for fact in obj.evidence_facts}
    assert kinds["actual_amount"] == EvidenceFactKind.OBSERVATION
    assert kinds["cost_anomaly_score"] == EvidenceFactKind.DERIVED
    assert obj.evidence_facts[0].statement == "Actual allocation = 267,000"


def test_future_signal_types_are_accepted() -> None:
    for signal in FUTURE_SIGNAL_TYPES:
        obj = valid_evidence(
            signal_type=signal,
            evidence_id=make_evidence_id(
                engine_name="graph",
                engine_version="future",
                project_id=1,
                signal_type=signal.value,
                data_mode="REAL",
            ),
            engine_name="graph",
            engine_version="future",
        )
        assert validate_evidence(obj).signal_type == signal


def test_parse_rejects_missing_finding() -> None:
    payload = valid_evidence().model_dump()
    payload["finding"] = ""
    try:
        parse_and_validate(payload)
    except EvidenceValidationError as exc:
        assert "finding" in str(exc).casefold() or "non-empty" in str(exc).casefold()
    else:
        raise AssertionError("empty finding must be rejected")
