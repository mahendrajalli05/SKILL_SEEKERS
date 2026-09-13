from __future__ import annotations

from datetime import date

import pytest

from app.domain.enums import DataMode, EvidenceDisposition, FusionExplanationType, RecommendedAction
from app.domain.schemas.evidence import EvidenceFact
from app.engines.fusion_v2.constants import ENGINE_VERSION, GROUP_WEIGHTS, GOVERNANCE_NOTE
from app.engines.fusion_v2.fuse import fuse_evidence_v2
from app.engines.fusion_v2.service import assess_project_risk_v2, list_fusion_v2_history
from app.evidence.repository import persist_evidence_object
from app.models.project import Project
from fusion_v2_fixtures import all_major_groups, make_group_evidence
from sqlalchemy import select

from app.db import get_session_factory
from app.models.fusion import FusionScore
from app.models.fusion_v2 import FusionScoreV2History


def _fuse(objects, *, project_id=101, mode=DataMode.REAL):
    return fuse_evidence_v2(
        objects,
        project_id=project_id,
        internal_project_id=f"internal:fusion-v2:{project_id}",
        requested_data_mode=mode,
    )


def test_all_major_evidence_groups_present() -> None:
    result = _fuse(all_major_groups(score=80))
    scored = {item.group_id for item in result.contributing_evidence_groups}
    assert "cost" in scored
    assert "geospatial" in scored
    assert "citizen" in scored
    assert 0 <= result.investigation_priority <= 100
    assert result.investigation_priority > 40
    assert "fraud" not in result.explanation.casefold()
    assert "Need / impact" not in [
        item.display_name for item in result.contributing_evidence_groups
    ]


def test_only_one_evidence_group_does_not_become_100() -> None:
    result = _fuse(
        [
            make_group_evidence(
                "cost",
                score=100,
                disposition=EvidenceDisposition.WHY_FLAGGED,
                confidence=1.0,
            )
        ]
    )
    assert result.investigation_priority < 30
    assert result.investigation_priority > 0
    assert result.unavailable_evidence
    assert result.investigation_priority != 100


def test_missing_evidence_is_unavailable_not_zero_risk() -> None:
    result = _fuse([])
    assert result.investigation_priority == 0
    assert result.explanation_type == FusionExplanationType.INSUFFICIENT_EVIDENCE
    assert result.recommended_action == RecommendedAction.NEED_MORE_INFORMATION
    names = {item.group_id: item.unavailable_reason for item in result.unavailable_evidence}
    assert "cost" in names
    assert "not treated as suspicious" in (names["cost"] or "").casefold()
    assert "unavailable is not treated as zero-risk" in result.explanation.casefold() or "not treated as zero" in result.explanation.casefold()


def test_correlated_overlap_and_graph_are_discounted() -> None:
    overlap = make_group_evidence(
        "overlap",
        score=90,
        disposition=EvidenceDisposition.WHY_FLAGGED,
        confidence=0.9,
    )
    graph = make_group_evidence(
        "graph",
        score=95,
        disposition=EvidenceDisposition.WHY_FLAGGED,
        confidence=0.9,
        extra_facts=[
            EvidenceFact(key="strongest_relationship", value="SIMILAR_TO", source="relationship-graph-v1"),
            EvidenceFact(key="similar_project_count", value=3, source="relationship-graph-v1"),
        ],
    )
    correlated = _fuse([overlap, graph])
    independent_graph = make_group_evidence(
        "graph",
        score=95,
        disposition=EvidenceDisposition.WHY_FLAGGED,
        confidence=0.9,
        extra_facts=[
            EvidenceFact(key="strongest_relationship", value="IDA", source="relationship-graph-v1"),
            EvidenceFact(key="similar_project_count", value=0, source="relationship-graph-v1"),
            EvidenceFact(key="independent_signal_count", value=2, source="relationship-graph-v1"),
            EvidenceFact(key="independent_signals", value=["ida_concentration"], source="relationship-graph-v1"),
        ],
    )
    independent = _fuse([overlap, independent_graph])
    assert correlated.discounted_correlated_evidence
    assert correlated.investigation_priority < independent.investigation_priority
    assert "shared semantic" in correlated.explanation.casefold() or "similar" in correlated.explanation.casefold()


def test_independent_corroborating_evidence_is_not_discounted() -> None:
    cost = make_group_evidence("cost", score=80, disposition=EvidenceDisposition.WHY_FLAGGED)
    geo = make_group_evidence(
        "geospatial",
        score=80,
        disposition=EvidenceDisposition.WHY_FLAGGED,
    )
    result = _fuse([cost, geo])
    ids = {item.group_id for item in result.discounted_correlated_evidence}
    assert "cost" not in ids
    assert "geospatial" not in ids
    assert result.investigation_priority > _fuse([cost]).investigation_priority


def test_conflicting_evidence_does_not_force_conclusion() -> None:
    citizen = make_group_evidence(
        "citizen",
        score=55,
        disposition=EvidenceDisposition.WHY_FLAGGED,
        finding="Citizen reports incomplete work",
        extra_facts=[EvidenceFact(key="accepted_report_count", value=3, source="jan-sakshi-v1")],
    )
    milestone = make_group_evidence(
        "milestone",
        score=0,
        disposition=EvidenceDisposition.WHY_NOT_FLAGGED,
        finding="Milestone evidence indicates complete",
    )
    satellite = make_group_evidence(
        "satellite",
        score=None,
        disposition=EvidenceDisposition.INCONCLUSIVE,
        finding="Satellite is inconclusive",
        signal_type=None,
    )
    result = _fuse([citizen, milestone, satellite])
    assert result.explanation_type == FusionExplanationType.CONFLICTING_EVIDENCE
    assert result.conflicting_evidence
    assert result.evidence_confidence < 80
    assert "disagree" in result.explanation.casefold() or "conflict" in result.explanation.casefold()
    assert "fraud" not in result.explanation.casefold()


def test_high_priority_low_confidence_is_conservative() -> None:
    objects = all_major_groups(
        score=100,
        disposition=EvidenceDisposition.WHY_FLAGGED,
        confidence=0.12,
    )
    result = _fuse(objects)
    assert result.investigation_priority >= 45
    assert result.evidence_confidence < 40
    assert result.recommended_action == RecommendedAction.NEED_MORE_INFORMATION


def test_low_priority_high_confidence() -> None:
    objects = [
        make_group_evidence(group, score=0, disposition=EvidenceDisposition.WHY_NOT_FLAGGED, confidence=0.9)
        for group in ("cost", "time", "overlap", "compliance", "graph", "geospatial")
    ]
    result = _fuse(objects)
    assert result.investigation_priority <= 24
    assert result.evidence_confidence > result.investigation_priority
    assert result.recommended_action in {
        RecommendedAction.MONITOR,
        RecommendedAction.NEED_MORE_INFORMATION,
    }


def test_real_hybrid_synthetic_modes_are_retained() -> None:
    real = _fuse(
        [make_group_evidence("cost", score=40, data_mode=DataMode.REAL)],
        mode=DataMode.REAL,
    )
    hybrid = _fuse(
        [make_group_evidence("time", score=80, disposition=EvidenceDisposition.WHY_FLAGGED, data_mode=DataMode.HYBRID)],
        mode=DataMode.HYBRID,
    )
    synthetic = _fuse(
        [make_group_evidence("cost", score=80, disposition=EvidenceDisposition.WHY_FLAGGED, data_mode=DataMode.SYNTHETIC)],
        mode=DataMode.SYNTHETIC,
    )
    assert real.data_mode == DataMode.REAL
    assert hybrid.data_mode == DataMode.HYBRID
    assert synthetic.data_mode == DataMode.SYNTHETIC
    assert "HYBRID" in hybrid.explanation
    assert "SYNTHETIC" in synthetic.explanation
    assert "not a government" in synthetic.explanation.casefold()


def test_duplicate_evidence_ids_are_ignored() -> None:
    first = make_group_evidence("cost", score=50, disposition=EvidenceDisposition.WHY_FLAGGED)
    result = _fuse([first, first, first])
    assert first.evidence_id in result.ignored_duplicate_evidence_ids
    assert result.evidence_ids.count(first.evidence_id) == 1


def test_unavailable_and_not_assessable_are_distinct() -> None:
    time_na = make_group_evidence(
        "time",
        score=None,
        disposition=EvidenceDisposition.NOT_ASSESSABLE,
        finding="Time Anomaly is not assessable",
    )
    result = _fuse([time_na])
    not_assessable = {item.group_id: item.state.value for item in result.not_assessable_evidence}
    unavailable = {item.group_id for item in result.unavailable_evidence}
    assert not_assessable["time"] == "NOT_ASSESSABLE"
    assert "cost" in unavailable
    assert result.investigation_priority == 0


def test_score_bounded_and_deterministic() -> None:
    objects = all_major_groups(score=100)
    first = _fuse(objects)
    second = _fuse(objects)
    assert first.investigation_priority == second.investigation_priority
    assert first.evidence_confidence == second.evidence_confidence
    assert first.evidence_fingerprint == second.evidence_fingerprint
    assert 0 <= first.investigation_priority <= 100
    assert 0 <= first.evidence_confidence <= 100
    assert first.engine_version == ENGINE_VERSION


def test_monotonicity_independent_signal() -> None:
    low = _fuse([make_group_evidence("cost", score=20, disposition=EvidenceDisposition.WHY_FLAGGED)])
    high = _fuse([make_group_evidence("cost", score=80, disposition=EvidenceDisposition.WHY_FLAGGED)])
    added = _fuse(
        [
            make_group_evidence("cost", score=80, disposition=EvidenceDisposition.WHY_FLAGGED),
            make_group_evidence("geospatial", score=80, disposition=EvidenceDisposition.WHY_FLAGGED),
        ]
    )
    assert high.investigation_priority >= low.investigation_priority
    assert added.investigation_priority >= high.investigation_priority


def test_no_fraud_wording_no_sanction_no_payment() -> None:
    result = _fuse(all_major_groups(score=100))
    blob = (result.explanation + " " + result.recommendation + " " + GOVERNANCE_NOTE).casefold()
    assert "fraud" not in blob or "not a legal finding" in blob
    assert "this project is fraudulent" not in blob
    assert "fraud_probability" not in blob
    assert "pfms" not in blob
    assert "automatic sanction" not in blob or "no automatic sanction" in blob
    assert "payment release" in blob
    assert result.recommended_action != "SANCTION"


def test_provenance_preserved_on_breakdown() -> None:
    obj = make_group_evidence("cost", score=70, disposition=EvidenceDisposition.WHY_FLAGGED)
    result = _fuse([obj])
    cost = next(item for item in result.all_groups if item.group_id == "cost")
    assert obj.evidence_id in cost.evidence_ids
    assert cost.items[0].source_ids
    assert cost.items[0].raw_evidence_score == 70
    assert cost.effective_contribution > 0


def test_weights_are_documented_prototype_values() -> None:
    assert round(sum(GROUP_WEIGHTS.values()), 4) == 1.0
    assert GROUP_WEIGHTS["need"] == 0.0


def test_historical_reproducibility_and_new_evidence(client) -> None:
    session = get_session_factory()()
    try:
        project = Project(
            internal_project_id="internal:synthetic:fusion-v2:hist",
            internal_id_kind="internal_surrogate_hash",
            internal_id_scheme="sarvsakshi_internal_work_v1",
            source_dataset="github_vonter_india-mplads-works_MPLADS.csv",
            is_synthetic=True,
            synthetic_label="SYNTHETIC: fusion v2 history test",
            lifecycle_stage="FUTURE",
            state="Andhra Pradesh",
        )
        session.add(project)
        session.flush()
        cost = make_group_evidence(
            "cost",
            project_id=project.id,
            score=100,
            disposition=EvidenceDisposition.WHY_FLAGGED,
            data_mode=DataMode.SYNTHETIC,
        )
        persist_evidence_object(session, cost)
        session.commit()
        first = assess_project_risk_v2(session, project.id, data_mode=DataMode.SYNTHETIC, persist=True)
        replay = assess_project_risk_v2(session, project.id, data_mode=DataMode.SYNTHETIC, persist=True)
        assert replay.investigation_priority == first.investigation_priority
        assert replay.evidence_fingerprint == first.evidence_fingerprint
        geo = make_group_evidence(
            "geospatial",
            project_id=project.id,
            score=90,
            disposition=EvidenceDisposition.WHY_FLAGGED,
            data_mode=DataMode.SYNTHETIC,
        )
        persist_evidence_object(session, geo)
        session.commit()
        updated = assess_project_risk_v2(session, project.id, data_mode=DataMode.SYNTHETIC, persist=True)
        assert updated.investigation_priority >= first.investigation_priority
        history = list_fusion_v2_history(session, project.id, data_mode=DataMode.SYNTHETIC)
        assert len(history) >= 3
        assert history[0].investigation_priority == first.investigation_priority
        assert history[0].payload_json == history[1].payload_json
        v1_count = session.scalars(select(FusionScore).where(FusionScore.project_id == project.id)).first()
        assert v1_count is None
        hist_rows = list(session.scalars(select(FusionScoreV2History)).all())
        assert hist_rows[0].investigation_priority == first.investigation_priority
    finally:
        session.close()
