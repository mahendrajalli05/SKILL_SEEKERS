from __future__ import annotations

import pytest

from app.domain.enums import DataMode, EvidenceDisposition, EvidenceFactKind
from app.domain.schemas.evidence import EvidenceFact
from app.engines.fusion.errors import FusionError
from app.engines.fusion.fuse import fuse_evidence
from fusion_fixtures import make_signal_evidence


def test_real_vs_hybrid_distinction() -> None:
    real_objects = [
        make_signal_evidence(
            "cost",
            score=80,
            confidence=0.90,
            disposition=EvidenceDisposition.WHY_FLAGGED,
            data_mode=DataMode.REAL,
        ),
        make_signal_evidence(
            "schedule",
            score=80,
            confidence=0.90,
            disposition=EvidenceDisposition.WHY_FLAGGED,
            data_mode=DataMode.REAL,
        ),
        make_signal_evidence(
            "overlap",
            score=80,
            confidence=0.90,
            disposition=EvidenceDisposition.WHY_FLAGGED,
            data_mode=DataMode.REAL,
        ),
        make_signal_evidence(
            "compliance",
            score=None,
            confidence=0.90,
            disposition=EvidenceDisposition.WHY_FLAGGED,
            severity="attention",
            rule_ids=["R004"],
            data_mode=DataMode.REAL,
        ),
    ]
    hybrid_objects = [
        make_signal_evidence(
            "cost",
            score=80,
            confidence=0.90,
            disposition=EvidenceDisposition.WHY_FLAGGED,
            data_mode=DataMode.REAL,
        ),
        make_signal_evidence(
            "schedule",
            score=80,
            confidence=0.90,
            disposition=EvidenceDisposition.WHY_FLAGGED,
            data_mode=DataMode.HYBRID,
        ),
        make_signal_evidence(
            "overlap",
            score=80,
            confidence=0.90,
            disposition=EvidenceDisposition.WHY_FLAGGED,
            data_mode=DataMode.HYBRID,
        ),
        make_signal_evidence(
            "compliance",
            score=None,
            confidence=0.90,
            disposition=EvidenceDisposition.WHY_FLAGGED,
            severity="attention",
            rule_ids=["R004"],
            data_mode=DataMode.HYBRID,
        ),
    ]
    real = fuse_evidence(real_objects, project_id=101, requested_data_mode=DataMode.REAL)
    hybrid = fuse_evidence(hybrid_objects, project_id=101, requested_data_mode=DataMode.HYBRID)
    assert real.data_mode == DataMode.REAL
    assert hybrid.data_mode == DataMode.HYBRID
    assert real.investigation_priority == hybrid.investigation_priority
    assert hybrid.evidence_confidence <= 72
    assert real.evidence_confidence >= hybrid.evidence_confidence
    assert "HYBRID" in hybrid.explanation
    assert "REAL" in real.explanation
    assert "synthetic enrichment" in hybrid.explanation


def test_forbidden_synthetic_label_leakage() -> None:
    leaked = make_signal_evidence(
        "cost",
        extra_facts=[
            EvidenceFact(
                key="scenario_type",
                value="COST_ANOMALY",
                source="must-not-be-used",
                kind=EvidenceFactKind.DERIVED,
            )
        ],
    )
    with pytest.raises(FusionError, match="scenario_type"):
        fuse_evidence([leaked], project_id=101)

    for key in (
        "demo_case_id",
        "mixed_signals",
        "anomaly_notes",
        "overlap_group_id",
        "coordinate_source",
    ):
        obj = make_signal_evidence(
            "overlap",
            extra_facts=[
                EvidenceFact(key=key, value="leak", source="must-not-be-used")
            ],
        )
        with pytest.raises(FusionError):
            fuse_evidence([obj], project_id=101)


def test_explanation_correctness() -> None:
    flagged = fuse_evidence(
        [
            make_signal_evidence("cost", score=90, disposition=EvidenceDisposition.WHY_FLAGGED),
            make_signal_evidence("overlap", score=90, disposition=EvidenceDisposition.WHY_FLAGGED),
        ],
        project_id=101,
    )
    assert flagged.explanation_type.value == "WHY_FLAGGED"
    assert "WHY_FLAGGED" in flagged.explanation_types
    assert "Cost" in flagged.explanation
    assert "Overlap" in flagged.explanation
    assert "unavailable" in flagged.explanation.lower() or "not assessable" in flagged.explanation.lower()
    assert "Evidence Confidence" in flagged.explanation or "confidence" in flagged.explanation.lower()
    assert "this project is fraudulent" not in flagged.explanation.casefold()

    clean = fuse_evidence(
        [
            make_signal_evidence("cost", score=4, disposition=EvidenceDisposition.WHY_NOT_FLAGGED),
            make_signal_evidence("schedule", score=3, disposition=EvidenceDisposition.WHY_NOT_FLAGGED),
            make_signal_evidence("overlap", score=5, disposition=EvidenceDisposition.WHY_NOT_FLAGGED),
            make_signal_evidence("compliance", score=None, disposition=EvidenceDisposition.WHY_NOT_FLAGGED),
        ],
        project_id=101,
    )
    assert clean.explanation_type.value == "WHY_NOT_FLAGGED"
    assert "low" in clean.explanation.lower()

    empty = fuse_evidence([], project_id=101)
    assert empty.explanation_type.value == "INSUFFICIENT_EVIDENCE"
    assert "no assessable" in empty.explanation.lower()


def test_recommendation_mapping() -> None:
    monitor = fuse_evidence(
        [make_signal_evidence("cost", score=8, disposition=EvidenceDisposition.WHY_NOT_FLAGGED)],
        project_id=101,
    )
    assert monitor.recommended_action.value == "MONITOR"
    assert "legal" not in monitor.recommendation.lower() or "not a legal" in monitor.recommendation.lower()

    review = fuse_evidence(
        [make_signal_evidence("cost", score=100, disposition=EvidenceDisposition.WHY_FLAGGED)],
        project_id=101,
    )
    assert review.investigation_priority == 36
    assert review.recommended_action.value == "REVIEW"

    inspect = fuse_evidence(
        [
            make_signal_evidence("cost", score=100, disposition=EvidenceDisposition.WHY_FLAGGED),
            make_signal_evidence("overlap", score=80, disposition=EvidenceDisposition.WHY_FLAGGED),
        ],
        project_id=101,
    )
    assert inspect.investigation_priority == 53
    assert inspect.recommended_action.value == "INSPECT"

    investigate = fuse_evidence(
        [
            make_signal_evidence("cost", score=100, disposition=EvidenceDisposition.WHY_FLAGGED),
            make_signal_evidence("schedule", score=100, disposition=EvidenceDisposition.WHY_FLAGGED),
            make_signal_evidence("overlap", score=100, disposition=EvidenceDisposition.WHY_FLAGGED),
            make_signal_evidence(
                "compliance",
                score=None,
                disposition=EvidenceDisposition.WHY_FLAGGED,
                severity="attention",
                rule_ids=["R004"],
            ),
        ],
        project_id=101,
    )
    assert investigate.recommended_action.value == "INVESTIGATE"
    assert "not a legal" in investigate.recommendation.lower()


def test_unavailable_signal_reporting() -> None:
    result = fuse_evidence(
        [make_signal_evidence("cost", score=50, disposition=EvidenceDisposition.WHY_NOT_FLAGGED)],
        project_id=101,
    )
    unavailable_ids = {item.signal_id: item for item in result.unavailable_signals}
    assert "schedule" in unavailable_ids
    assert "relationship_graph" in unavailable_ids
    assert "citizen_evidence" in unavailable_ids
    assert "geospatial" in unavailable_ids
    assert "image" in unavailable_ids
    assert "document" in unavailable_ids
    assert "milestone" in unavailable_ids
    assert "field_evidence" in unavailable_ids
    assert unavailable_ids["relationship_graph"].state.value == "NOT_YET_INTEGRATED"
    assert unavailable_ids["schedule"].state.value == "UNAVAILABLE"
    assert result.reserved_unavailable_weight == pytest.approx(0.30)
    assert "Prototype weights" in result.weight_note
    assert "not official MoSPI" in result.weight_note
