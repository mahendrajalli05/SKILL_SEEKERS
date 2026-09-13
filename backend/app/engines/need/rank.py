"""Planning-simulation ranking for proposed works.

Does not sanction projects or execute payments.
INCONCLUSIVE assessments are not forced into the ranked list.
"""

from __future__ import annotations

from app.engines.need.constants import (
    ENGINE_VERSION,
    GOVERNANCE_NOTE,
    INCONCLUSIVE,
    PLANNING_SIMULATION_NOTE,
    WEIGHT_NOTE,
)
from app.engines.need.types import NeedImpactResult, RankedProject, RankResult


def _tie_key(result: NeedImpactResult) -> tuple[float, float, int]:
    score = float(result.priority_score or 0.0)
    return (-score, -float(result.evidence_confidence), result.project_id)


def _compare_reason(higher: NeedImpactResult, lower: NeedImpactResult) -> str:
    if (higher.priority_score or -1) != (lower.priority_score or -1):
        return (
            f"Ranked above project {lower.project_id} because Priority Score "
            f"{higher.priority_score} > {lower.priority_score}."
        )
    if higher.evidence_confidence != lower.evidence_confidence:
        return (
            f"Tied on Priority Score {higher.priority_score}; ranked above project "
            f"{lower.project_id} because Evidence Confidence "
            f"{higher.evidence_confidence} > {lower.evidence_confidence}."
        )
    return (
        f"Tied on Priority Score {higher.priority_score} and Evidence Confidence; "
        f"ranked above project {lower.project_id} by stable project id "
        f"{higher.project_id} < {lower.project_id}."
    )


def _below_reason(lower: NeedImpactResult, higher: NeedImpactResult) -> str:
    if (higher.priority_score or -1) != (lower.priority_score or -1):
        return (
            f"Ranked below project {higher.project_id} because Priority Score "
            f"{lower.priority_score} < {higher.priority_score}."
        )
    if higher.evidence_confidence != lower.evidence_confidence:
        return (
            f"Tied on Priority Score {lower.priority_score}; ranked below project "
            f"{higher.project_id} because Evidence Confidence "
            f"{lower.evidence_confidence} < {higher.evidence_confidence}."
        )
    return (
        f"Tied on Priority Score and Evidence Confidence; ranked below project "
        f"{higher.project_id} by stable project id."
    )


def rank_assessments(
    results: list[NeedImpactResult],
    *,
    available_budget: int | None = None,
    available_budget_crore: float | None = None,
) -> RankResult:
    assessable = [item for item in results if item.priority_class != INCONCLUSIVE and item.priority_score is not None]
    inconclusive = [item for item in results if item not in assessable]
    assessable.sort(key=_tie_key)
    ranked: list[RankedProject] = []
    for index, current in enumerate(assessable):
        previous = assessable[index - 1] if index > 0 else None
        nxt = assessable[index + 1] if index + 1 < len(assessable) else None
        ranked.append(
            RankedProject(
                rank=index + 1,
                project_id=current.project_id,
                internal_project_id=current.internal_project_id,
                constituency=current.constituency,
                category=current.category,
                requested_amount=current.requested_amount,
                priority_score=current.priority_score,
                priority_class=current.priority_class,
                evidence_confidence=current.evidence_confidence,
                rationale=current.finding,
                why_ranked_above=_compare_reason(current, nxt) if nxt is not None else None,
                why_ranked_below=_below_reason(current, previous) if previous is not None else None,
                within_hypothetical_budget=None,
                budget_note=None,
                need_score=current.need.score,
                impact_score=current.impact.score,
                data_mode=current.data_mode.value if hasattr(current.data_mode, "value") else str(current.data_mode),
                finding=current.finding,
                top_reasons=list(current.top_reasons),
                unavailable_inputs=list(current.unavailable_inputs),
            )
        )
    remaining: int | None = None
    if available_budget is not None:
        remaining = int(available_budget)
        for item in ranked:
            amount = item.requested_amount
            if amount is None:
                item.within_hypothetical_budget = False
                item.budget_note = (
                    "Requested allocation is unavailable, so this work cannot be "
                    "placed inside the hypothetical budget simulation."
                )
                continue
            if amount <= remaining:
                item.within_hypothetical_budget = True
                remaining -= amount
                item.budget_note = (
                    "Included in the hypothetical remaining-budget simulation. "
                    "This is not a sanction."
                )
            else:
                item.within_hypothetical_budget = False
                item.budget_note = (
                    "Requested allocation exceeds the remaining hypothetical budget. "
                    "This is not a sanction denial."
                )
    unranked = [
        RankedProject(
            rank=None,
            project_id=item.project_id,
            internal_project_id=item.internal_project_id,
            constituency=item.constituency,
            category=item.category,
            requested_amount=item.requested_amount,
            priority_score=item.priority_score,
            priority_class=item.priority_class,
            evidence_confidence=item.evidence_confidence,
            rationale=(
                "INCONCLUSIVE: Need and Impact could not both be assessed from "
                "available verified inputs. Ranking was not forced."
            ),
            why_ranked_above=None,
            why_ranked_below=None,
            within_hypothetical_budget=None,
            budget_note=None,
            need_score=item.need.score,
            impact_score=item.impact.score,
            data_mode=item.data_mode.value if hasattr(item.data_mode, "value") else str(item.data_mode),
            finding=item.finding,
            top_reasons=list(item.top_reasons),
            unavailable_inputs=list(item.unavailable_inputs),
        )
        for item in inconclusive
    ]
    explanation = (
        f"{PLANNING_SIMULATION_NOTE} {GOVERNANCE_NOTE} {WEIGHT_NOTE} "
        f"{len(ranked)} work(s) have a recommended priority class. "
        f"{len(unranked)} work(s) are INCONCLUSIVE and were not forced into ranking."
    )
    return RankResult(
        items=ranked,
        unranked=unranked,
        available_budget=available_budget,
        available_budget_crore=available_budget_crore,
        remaining_budget=remaining,
        data_mode=results[0].data_mode.value if results else "REAL",
        explanation=explanation,
        engine_version=ENGINE_VERSION,
    )
