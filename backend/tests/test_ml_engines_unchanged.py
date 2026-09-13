from __future__ import annotations

from pathlib import Path

from app.engines.compliance.constants import ENGINE_VERSION as COMPLIANCE_VERSION
from app.engines.cost.constants import ENGINE_VERSION as COST_VERSION
from app.engines.fusion.constants import ENGINE_VERSION as FUSION_V1_VERSION
from app.engines.fusion_v2.constants import ENGINE_VERSION as FUSION_V2_VERSION
from app.engines.overlap.constants import ENGINE_VERSION as OVERLAP_VERSION
from app.engines.pce.constants import ENGINE_VERSION as PCE_VERSION
from app.engines.time.constants import ENGINE_VERSION as TIME_VERSION


def test_frozen_engine_versions_unchanged() -> None:
    assert COST_VERSION == "cost-peer-v1.1"
    assert TIME_VERSION == "time-peer-v1"
    assert OVERLAP_VERSION == "overlap-multi-v1"
    assert COMPLIANCE_VERSION == "compliance-rules-v1"
    assert FUSION_V1_VERSION == "risk-fusion-v1.1"
    assert FUSION_V2_VERSION == "risk-fusion-v2"
    assert PCE_VERSION == "plan-claim-evidence-v1"


def test_cost_engine_source_has_no_isolation_forest() -> None:
    root = Path(__file__).resolve().parents[1] / "app" / "engines"
    for name in ("cost", "time", "overlap", "compliance", "fusion", "fusion_v2", "pce"):
        text = ""
        folder = root / name
        for path in folder.glob("*.py"):
            text += path.read_text(encoding="utf-8")
        assert "IsolationForest" not in text
        assert "sklearn" not in text
