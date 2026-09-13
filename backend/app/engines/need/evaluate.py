"""Assemble a Need & Impact assessment from scored dimensions."""

from __future__ import annotations

from datetime import date

from app.domain.enums import DataMode
from app.engines.need.constants import (
    CONTEXT_NOT_NEED_NOTE,
    ENGINE_NAME,
    ENGINE_VERSION,
    GOVERNANCE_NOTE,
    INCONCLUSIVE,
    LIMITATIONS,
    MP_NOT_GEOGRAPHY_NOTE,
    PRIORITY_WEIGHTS,
    REAL_AS_OF_DATE,
    WEIGHT_NOTE,
)
from app.engines.need.explain import explanation_for, finding_for
from app.engines.need.scoring import (
    combine_priority,
    enrichment_label_for,
    evidence_confidence,
    score_impact,
    score_need,
    score_urgency,
)
from app.engines.need.types import ConstituencyContext, NeedImpactInputs, NeedImpactResult


def evaluate_need_impact(
    inputs: NeedImpactInputs,
    *,
    constituency_context: ConstituencyContext | None = None,
    as_of: date | None = None,
) -> NeedImpactResult:
    as_of_date = as_of or REAL_AS_OF_DATE
    need = score_need(inputs)
    impact = score_impact(inputs)
    urgency = score_urgency(inputs, as_of=as_of_date)
    priority_score, priority_class = combine_priority(need, impact, urgency)
    confidence = evidence_confidence(
        data_mode=inputs.data_mode,
        need=need,
        impact=impact,
        urgency=urgency,
        enrichment=inputs.enrichment if inputs.data_mode != DataMode.REAL else None,
    )
    unavailable: list[str] = []
    for dimension in (need, impact, urgency):
        for item in dimension.unavailable_inputs:
            if item not in unavailable:
                unavailable.append(item)
    top_reasons: list[str] = []
    for dimension in (need, impact, urgency):
        for reason in dimension.top_reasons:
            if reason not in top_reasons:
                top_reasons.append(reason)
        if len(top_reasons) >= 6:
            break
    contextual = [CONTEXT_NOT_NEED_NOTE, MP_NOT_GEOGRAPHY_NOTE]
    if constituency_context is not None:
        contextual.append(constituency_context.reason)
        if constituency_context.constituency_work_count is not None:
            contextual.append(
                f"Observed works recorded in this constituency: "
                f"{constituency_context.constituency_work_count}. "
                "This count is not used as Need Score."
            )
        if constituency_context.category_work_count is not None:
            contextual.append(
                f"Observed same-category works in this constituency: "
                f"{constituency_context.category_work_count}. "
                "Category coverage is contextual only."
            )
    result = NeedImpactResult(
        project_id=inputs.project_id,
        internal_project_id=inputs.internal_project_id,
        data_mode=inputs.data_mode,
        constituency=inputs.constituency,
        category=inputs.category,
        work_description=inputs.work_description,
        requested_amount=inputs.allocation_amount,
        lifecycle_stage=inputs.lifecycle_stage,
        status=inputs.status,
        need=need,
        impact=impact,
        urgency=urgency,
        priority_score=priority_score,
        priority_class=priority_class,
        evidence_confidence=confidence,
        top_reasons=top_reasons[:6],
        unavailable_inputs=unavailable,
        contextual_evidence=contextual,
        explanation="",
        finding="",
        weights=dict(PRIORITY_WEIGHTS),
        weight_note=WEIGHT_NOTE,
        governance_note=GOVERNANCE_NOTE,
        limitations=list(LIMITATIONS),
        constituency_context=constituency_context,
        enrichment_used=inputs.data_mode != DataMode.REAL and inputs.enrichment is not None,
        enrichment_label=enrichment_label_for(inputs),
        automatic_sanction=False,
        engine_version=ENGINE_VERSION,
        engine_name=ENGINE_NAME,
    )
    result.finding = finding_for(result)
    result.explanation = explanation_for(result, inputs)
    if result.priority_class == INCONCLUSIVE and result.priority_score is not None:
        result.priority_score = None
    return result
