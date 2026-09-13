from __future__ import annotations

from app.engines.compliance.constants import ENGINE_VERSION as COMPLIANCE_VERSION
from app.engines.cost.constants import ENGINE_VERSION as COST_VERSION
from app.engines.document.constants import ENGINE_VERSION as DOCUMENT_VERSION
from app.engines.fusion.constants import ENGINE_VERSION as FUSION_VERSION
from app.engines.geo.constants import ENGINE_VERSION as GEO_VERSION
from app.engines.graph.constants import ENGINE_VERSION as GRAPH_VERSION
from app.engines.image.constants import ENGINE_VERSION as IMAGE_VERSION
from app.engines.need.constants import ENGINE_VERSION, NEED_WEIGHT, IMPACT_WEIGHT, URGENCY_WEIGHT
from app.engines.overlap.constants import ENGINE_VERSION as OVERLAP_VERSION
from app.engines.pce.constants import ENGINE_VERSION as PCE_VERSION
from app.engines.time.constants import ENGINE_VERSION as TIME_VERSION


def test_frozen_engines_unchanged() -> None:
    assert COST_VERSION == "cost-peer-v1.1"
    assert TIME_VERSION == "time-peer-v1"
    assert OVERLAP_VERSION == "overlap-multi-v1"
    assert COMPLIANCE_VERSION == "compliance-rules-v1"
    assert FUSION_VERSION == "risk-fusion-v1.1"
    assert GRAPH_VERSION == "relationship-graph-v1"
    assert PCE_VERSION == "plan-claim-evidence-v1"
    assert DOCUMENT_VERSION == "document-blueprint-v1"
    assert IMAGE_VERSION == "image-evidence-v1"
    assert GEO_VERSION == "geospatial-consistency-v1"
    assert ENGINE_VERSION == "need-impact-v1"


def test_prototype_weights_are_explicit() -> None:
    assert NEED_WEIGHT == 0.45
    assert IMPACT_WEIGHT == 0.40
    assert URGENCY_WEIGHT == 0.15
    assert round(NEED_WEIGHT + IMPACT_WEIGHT + URGENCY_WEIGHT, 2) == 1.0
