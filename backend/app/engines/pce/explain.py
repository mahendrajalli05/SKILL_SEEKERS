"""Human-readable Plan–Claim–Evidence explanations. Never claims fraud."""

from __future__ import annotations

from app.engines.pce.constants import GOVERNANCE_NOTE
from app.engines.pce.types import (
    AssembledClaim,
    AssembledEvidenceItem,
    AssembledPlan,
    ConsistencyStatus,
    FieldComparison,
)


def _sentences(comparisons: list[FieldComparison], status: ConsistencyStatus) -> list[str]:
    return [
        item.explanation.rstrip(".") + "."
        for item in comparisons
        if item.status == status and item.comparison_id != "quantity_cost_conversion"
    ]


def build_explanation(
    overall: ConsistencyStatus,
    comparisons: list[FieldComparison],
    plan: AssembledPlan,
    claim: AssembledClaim,
    evidence_items: list[AssembledEvidenceItem],
    missing: list[str],
) -> str:
    parts: list[str] = []
    if overall == ConsistencyStatus.MISMATCH:
        parts.extend(_sentences(comparisons, ConsistencyStatus.MISMATCH)[:4])
    elif overall == ConsistencyStatus.CONSISTENT:
        preferred = [
            item
            for item in comparisons
            if item.status == ConsistencyStatus.CONSISTENT
            and item.field in {"quantity", "cost", "milestone_amount"}
        ]
        if preferred:
            parts.extend(item.explanation.rstrip(".") + "." for item in preferred[:3])
        else:
            parts.append(
                "Available plan, claim, and evidence fields did not identify a mismatch."
            )
    else:
        if not claim.recorded:
            parts.append(
                "No claim has been recorded, so Plan–Claim–Evidence verification is INCONCLUSIVE."
            )
        if not evidence_items:
            parts.append(
                "No supporting document or image evidence was attached, so the claim cannot be verified."
            )
        inconclusive = _sentences(comparisons, ConsistencyStatus.INCONCLUSIVE)
        parts.extend(inconclusive[:3])
        if missing and not parts:
            parts.append(
                "Required information is unavailable: " + ", ".join(missing[:6]) + "."
            )
        if not parts:
            parts.append(
                "Available fields are insufficient to verify the claim. The result is INCONCLUSIVE."
            )
    parts.append(GOVERNANCE_NOTE)
    # De-duplicate while preserving order.
    seen: set[str] = set()
    unique: list[str] = []
    for sentence in parts:
        if sentence not in seen:
            seen.add(sentence)
            unique.append(sentence)
    return " ".join(unique)


def plan_findings(plan: AssembledPlan) -> list[str]:
    findings: list[str] = []
    if plan.sanctioned_scope:
        findings.append(f"Sanctioned scope: {plan.sanctioned_scope}")
    else:
        findings.append("Sanctioned scope is unavailable.")
    if plan.budget_estimate is not None:
        suffix = " (observed allocation from extract)" if plan.budget_from_extract else ""
        findings.append(f"Budget/estimate is recorded{suffix}.")
    else:
        findings.append("Budget/estimate is unavailable.")
    if plan.dimensions_value is None:
        findings.append("Plan dimensions are unavailable.")
    else:
        unit = f" {plan.dimensions_unit}" if plan.dimensions_unit else ""
        findings.append(f"Plan dimensions are {plan.dimensions_value}{unit}.")
    if plan.milestone_amount is None:
        findings.append("Milestone amount is unavailable.")
    return findings


def claim_findings(claim: AssembledClaim) -> list[str]:
    if not claim.recorded:
        return ["No claim has been recorded. Claims are statements being evaluated, not established facts."]
    findings = ["Recorded claim is a statement under evaluation, not an established fact."]
    if claim.claimed_progress_percent is not None:
        findings.append(f"Claimed progress is {claim.claimed_progress_percent}%.")
    elif claim.claimed_progress:
        findings.append(f"Claimed progress: {claim.claimed_progress}")
    else:
        findings.append("Claimed progress is unavailable.")
    if claim.claimed_expenditure is None:
        findings.append("Claimed expenditure is unavailable.")
    if claim.claimed_quantity is None:
        findings.append("Claimed quantity/dimensions are unavailable.")
    return findings


def evidence_findings(items: list[AssembledEvidenceItem]) -> list[str]:
    if not items:
        return ["No Plan–Claim–Evidence attachments were recorded."]
    findings = [f"{len(items)} supporting evidence attachment(s) recorded."]
    quantities = sum(1 for item in items if item.observed_quantity is not None)
    if quantities == 0:
        findings.append(
            "Attached evidence does not include a recorded quantity, so dimensions cannot be verified from it."
        )
    else:
        findings.append(f"{quantities} attachment(s) include a recorded quantity.")
    return findings
