from __future__ import annotations

from app.copilot.guardrails import contains_forbidden_recommendation, contains_fraud_claim, legal_refusal_sections
from app.copilot.grounding import extract_cited_ids, grounding_errors
from app.copilot.types import CopilotDraft, CopilotProviderName, CopilotRecommendation, CopilotSections, InvestigationBundle
from app.domain.enums import DataMode


def test_fraud_language_is_detected() -> None:
    assert contains_fraud_claim("This project is fraud.")
    assert not contains_fraud_claim("Investigation Priority is elevated.")


def test_payment_and_sanction_language_is_forbidden() -> None:
    assert contains_forbidden_recommendation("Release funds through PFMS.")
    assert contains_forbidden_recommendation("Automatically sanction this work.")


def test_legal_refusal_does_not_claim_fraud() -> None:
    text = legal_refusal_sections().render().lower()
    assert "fraud" in text
    assert "does not determine legal fraud" in text
    assert "probability" not in text or "not" in text


def test_grounding_rejects_fabricated_evidence_ids() -> None:
    bundle = InvestigationBundle(
        project_id=1,
        internal_project_id="internal:synthetic:copilot:subject",
        scheme_id="SVK-AP-000001",
        data_mode=DataMode.SYNTHETIC,
        is_synthetic=True,
        hybrid_enrichment=False,
        work_description="tanks",
        constituency="KURNOOL",
        category="Normal/Others",
        status="Unsanctioned",
        allocation_amount=1,
        recommended_date=None,
        mp_name=None,
        state="Andhra Pradesh",
        unavailable_fields=[],
        evidence=[],
        risk=None,
        pce=None,
        documents=[],
        images=None,
        citizen_reports=[],
        citizen_summary=None,
        milestones=None,
    )
    draft = CopilotDraft(
        sections=CopilotSections(
            answer="See ev:cost:999:allocation_cost_anomaly:SYNTHETIC:deadbeef",
            why="because",
            evidence="ev:cost:999:allocation_cost_anomaly:SYNTHETIC:deadbeef",
            missing="none",
            recommended_action="REVIEW",
        ),
        evidence_ids=["ev:cost:999:allocation_cost_anomaly:SYNTHETIC:deadbeef"],
        source_refs=[],
        limitations=[],
        recommended_action=CopilotRecommendation.REVIEW,
        observed_facts=[],
        derived_findings=[],
        unavailable=[],
        insufficient_evidence=False,
        provider=CopilotProviderName.DETERMINISTIC,
    )
    assert grounding_errors(draft, bundle)
    cited = extract_cited_ids(draft.sections.render())
    assert any(item.startswith("ev:cost:999") for item in cited)
