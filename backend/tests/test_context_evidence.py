from __future__ import annotations

from app.db import get_session_factory
from app.domain.enums import DataMode, SignalType, SourceType
from app.engines.context.constants import ENGINE_NAME, ENGINE_VERSION
from app.engines.context.service import assess_project_context
from app.engines.fusion.constants import INTEGRATED_WEIGHTS
from app.engines.fusion_v2.constants import GROUP_WEIGHTS, SIGNAL_TYPE_TO_GROUP
from app.engines.fusion_v2.fuse import fuse_evidence_v2
from fusion_v2_fixtures import make_group_evidence
from tests.need_test_support import insert_project
from tests.test_evidence_schema import _provenance, valid_evidence


def _create(**overrides: object) -> int:
    session = get_session_factory()()
    try:
        row = insert_project(session, **overrides)
        session.commit()
        return row.id
    finally:
        session.close()


def test_context_evidence_objects_have_provenance(client) -> None:
    pid = _create(internal_project_id="internal:context:evidence")
    client.get(f"/api/v2/projects/{pid}/context", params={"data_mode": "REAL"})
    evidence = client.get(f"/api/v1/projects/{pid}/evidence").json()
    items = [item for item in evidence["items"] if item["engine_name"] == ENGINE_NAME]
    assert items
    blob = str(items).casefold()
    assert "fraud" not in blob
    need = next(item for item in items if item["signal_type"] == SignalType.DEVELOPMENT_NEED_CONTEXT.value)
    assert need["data_mode"] == "REAL"
    assert need["provenance"]["notes"]
    assert need["engine_version"] == ENGINE_VERSION
    kinds = {fact["kind"] for fact in need["evidence_facts"]}
    assert "OBSERVATION" in kinds
    assert need["source_type"] in {
        SourceType.EXTERNAL_PUBLIC_DATASET.value,
        SourceType.MPLADS_PROJECT_RECORD.value,
    }


def test_context_signals_do_not_change_risk_fusion_v2() -> None:
    cost = make_group_evidence("cost", score=80)
    without = fuse_evidence_v2(
        [cost],
        project_id=201,
        internal_project_id="internal:context:fusion:201",
        requested_data_mode=DataMode.REAL,
    )
    context_obj = valid_evidence(
        engine_name="context",
        engine_version=ENGINE_VERSION,
        signal_type=SignalType.DEVELOPMENT_NEED_CONTEXT,
        score=None,
        finding="DEVELOPMENT_NEED_CONTEXT: state-level external population context.",
        explanation="OBSERVED EXTERNAL INDICATOR. Not a legal conclusion.",
        source_type=SourceType.EXTERNAL_PUBLIC_DATASET,
        provenance=_provenance(source_type=SourceType.EXTERNAL_PUBLIC_DATASET),
        evidence_id="ev:context:201:DEVELOPMENT_NEED_CONTEXT:REAL:deadbeef",
    )
    with_context = fuse_evidence_v2(
        [cost, context_obj],
        project_id=201,
        internal_project_id="internal:context:fusion:201",
        requested_data_mode=DataMode.REAL,
    )
    assert without.investigation_priority == with_context.investigation_priority
    assert SignalType.DEVELOPMENT_NEED_CONTEXT.value not in SIGNAL_TYPE_TO_GROUP
    assert SignalType.REFERENCE_COST_CONTEXT.value not in SIGNAL_TYPE_TO_GROUP
    assert "context" not in GROUP_WEIGHTS
    assert INTEGRATED_WEIGHTS["cost"] == 0.25
