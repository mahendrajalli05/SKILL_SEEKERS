from __future__ import annotations

import pytest

from pydantic import ValidationError

from app.domain.enums import DataMode, EvidenceFactKind, SourceType
from app.domain.schemas.evidence import EvidenceFact
from app.evidence.errors import EvidenceValidationError
from app.evidence.validate import parse_and_validate, validate_evidence
from tests.test_evidence_schema import valid_evidence


def test_rejects_missing_source_ids() -> None:
    with pytest.raises((EvidenceValidationError, ValidationError)):
        parse_and_validate({**valid_evidence().model_dump(), "source_ids": []})


def test_rejects_missing_fact_source() -> None:
    with pytest.raises((EvidenceValidationError, Exception)):
        validate_evidence(
            valid_evidence(
                evidence_facts=[
                    EvidenceFact(
                        key="actual_amount",
                        value=1,
                        source="   ",
                        kind=EvidenceFactKind.OBSERVATION,
                    )
                ]
            )
        )


def test_rejects_fraud_claim() -> None:
    with pytest.raises(EvidenceValidationError, match="fraud"):
        validate_evidence(valid_evidence(finding="This project is fraud"))


def test_rejects_fraud_in_explanation() -> None:
    with pytest.raises(EvidenceValidationError, match="fraud"):
        validate_evidence(valid_evidence(explanation="fraudulent over-billing is confirmed"))


def test_rejects_real_marked_synthetic() -> None:
    with pytest.raises((EvidenceValidationError, ValidationError), match="REAL"):
        parse_and_validate(
            {
                **valid_evidence().model_dump(),
                "data_mode": DataMode.REAL.value,
                "source_type": SourceType.SYNTHETIC_TEST_RECORD.value,
                "provenance": valid_evidence().provenance.model_dump()
                | {
                    "data_mode": DataMode.REAL.value,
                    "source_type": SourceType.SYNTHETIC_TEST_RECORD.value,
                },
            }
        )


def test_rejects_real_using_hybrid_enrichment() -> None:
    with pytest.raises(EvidenceValidationError):
        validate_evidence(
            valid_evidence(
                data_mode=DataMode.REAL,
                source_type=SourceType.MPLADS_PROJECT_RECORD,
                provenance=valid_evidence().provenance.model_copy(
                    update={"enrichment_used": True}
                ),
            )
        )


def test_rejects_synthetic_label_fact_keys() -> None:
    with pytest.raises(EvidenceValidationError, match="scenario"):
        validate_evidence(
            valid_evidence(
                evidence_facts=[
                    EvidenceFact(
                        key="scenario_type",
                        value="COST_ANOMALY",
                        source="must-not-use",
                        kind=EvidenceFactKind.DERIVED,
                    )
                ]
            )
        )


def test_rejects_real_without_dataset_citation() -> None:
    with pytest.raises(EvidenceValidationError, match="source"):
        validate_evidence(
            valid_evidence(
                provenance=valid_evidence().provenance.model_copy(
                    update={"source_dataset": None, "source_url": None}
                )
            )
        )


def test_hybrid_and_real_remain_distinct() -> None:
    real = validate_evidence(valid_evidence())
    hybrid = validate_evidence(
        valid_evidence(
            data_mode=DataMode.HYBRID,
            source_type=SourceType.HYBRID_ENRICHMENT,
            provenance=valid_evidence().provenance.model_copy(
                update={
                    "data_mode": DataMode.HYBRID,
                    "source_type": SourceType.HYBRID_ENRICHMENT,
                    "enrichment_used": True,
                    "enrichment_path": "data/synthetic/sarvsakshi_synthetic_enrichment.csv",
                    "notes": "HYBRID/TEST synthetic enrichment; not official MPLADS values.",
                }
            ),
        )
    )
    assert real.data_mode == DataMode.REAL
    assert hybrid.data_mode == DataMode.HYBRID
    assert real.source_type != hybrid.source_type
    assert hybrid.provenance.enrichment_used is True
    assert real.provenance.enrichment_used is False
