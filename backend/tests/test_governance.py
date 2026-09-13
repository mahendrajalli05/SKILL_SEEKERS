from __future__ import annotations

from app.copilot import LLM_MODE, TEMPLATE_MODE
from app.domain.enums import EvidenceSeverity, EvidenceStatus
from app.models.fusion import FusionScore


def test_template_copilot_is_default_mode() -> None:
    assert TEMPLATE_MODE == "template"
    assert LLM_MODE == "llm"


def test_evidence_status_has_inconclusive() -> None:
    assert EvidenceStatus.INCONCLUSIVE.value == "inconclusive"
    assert all("fraud" not in member.value for member in EvidenceSeverity)


def test_no_fraud_probability_column_on_fusion_mapper() -> None:
    names = FusionScore.__table__.c.keys()
    assert "investigation_priority" in names
    assert "evidence_confidence" in names
    assert all("fraud" not in name for name in names)
