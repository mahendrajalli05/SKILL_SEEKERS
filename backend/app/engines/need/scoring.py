"""Transparent Need / Impact / Urgency / Priority scoring.

Prototype weights only. Unavailable components are omitted and remaining
weights are renormalized among available components of that dimension.
Historical work counts and historical funding are never Need inputs.
"""

from __future__ import annotations

from datetime import date

from app.domain.enums import DataMode
from app.engines.need.category import disaster_text_flag, essential_service_relevance
from app.engines.need.constants import (
    BENEFICIARY_BANDS,
    DISASTER_TEXT_URGENCY,
    HIGH_PRIORITY,
    HIGH_PRIORITY_MIN,
    HYBRID_CONFIDENCE_CAP,
    HYBRID_ENRICHMENT_LABEL,
    IMPACT_COMPONENT_WEIGHTS,
    INCONCLUSIVE,
    LOW_PRIORITY,
    MEDIUM_PRIORITY,
    MEDIUM_PRIORITY_MIN,
    NEED_COMPONENT_WEIGHTS,
    PARTIAL_CONFIDENCE_CAP,
    PRIORITY_WEIGHTS,
    REAL_AS_OF_DATE,
    REAL_CONFIDENCE_CAP,
    SYNTHETIC_CONFIDENCE_CAP,
    SYNTHETIC_VALUE_NOTE,
    UNAVAILABLE_CONFIDENCE,
    URGENCY_WAITING_MAX,
)
from app.engines.need.types import (
    DimensionScore,
    NeedImpactInputs,
    SignalComponent,
    SyntheticNeedImpactEnrichment,
)


def clip_score(value: float | None) -> float | None:
    if value is None:
        return None
    return round(max(0.0, min(100.0, float(value))), 1)


def weighted_available_score(components: list[SignalComponent]) -> float | None:
    used = [item for item in components if item.used_in_score and item.available and item.score is not None]
    if not used:
        return None
    total_weight = sum(item.weight for item in used)
    if total_weight <= 0:
        return None
    raw = sum((item.weight / total_weight) * float(item.score) for item in used)
    return clip_score(raw)


def beneficiary_score(count: int | None) -> float | None:
    if count is None:
        return None
    if count < 0:
        return None
    if count == 0:
        return 0.0
    assigned = 20.0
    for minimum, score in BENEFICIARY_BANDS:
        if count >= minimum:
            assigned = score
    return clip_score(assigned)


def waiting_urgency_score(recommended: date | None, as_of: date) -> float | None:
    if recommended is None:
        return None
    days = (as_of - recommended).days
    if days < 0:
        return 20.0
    if days < 180:
        return 35.0
    if days < 365:
        return 55.0
    if days < 730:
        return 75.0
    return URGENCY_WAITING_MAX


def _unavailable(
    key: str,
    label: str,
    weight: float,
    reason: str,
    data_mode: DataMode,
    *,
    used_in_score: bool = True,
) -> SignalComponent:
    return SignalComponent(
        key=key,
        label=label,
        available=False,
        score=None,
        weight=weight,
        source="unavailable",
        data_mode=data_mode.value,
        synthetic=False,
        unavailable_reason=reason,
        explanation=reason,
        used_in_score=used_in_score,
    )


def _synthetic_component(
    key: str,
    label: str,
    weight: float,
    score: float | None,
    data_mode: DataMode,
    explanation: str,
) -> SignalComponent:
    if score is None:
        return _unavailable(
            key,
            label,
            weight,
            f"{label} is unavailable: no TEST/SYNTHETIC value was supplied. "
            "The value was not invented.",
            data_mode,
        )
    return SignalComponent(
        key=key,
        label=label,
        available=True,
        score=clip_score(score),
        weight=weight,
        source=SYNTHETIC_VALUE_NOTE,
        data_mode=data_mode.value,
        synthetic=True,
        explanation=explanation,
    )


def _real_need_unavailable(data_mode: DataMode) -> list[SignalComponent]:
    reason = (
        "Unavailable in the current public MPLADS extract. Population, "
        "infrastructure, and underserved-area statistics were not invented."
    )
    return [
        _unavailable("population", "Population need", NEED_COMPONENT_WEIGHTS["population"], reason, data_mode),
        _unavailable(
            "infrastructure_gap",
            "Infrastructure gap",
            NEED_COMPONENT_WEIGHTS["infrastructure_gap"],
            reason,
            data_mode,
        ),
        _unavailable(
            "underserved_area",
            "Underserved-area indicator",
            NEED_COMPONENT_WEIGHTS["underserved_area"],
            reason,
            data_mode,
        ),
        _unavailable(
            "disaster_context",
            "Disaster / essential-service statistics",
            NEED_COMPONENT_WEIGHTS["disaster_context"],
            "Verified disaster or essential-service statistics are unavailable. "
            "Work-title disaster keywords, if any, are recorded as contextual text only "
            "and are not converted into a fabricated statistic.",
            data_mode,
        ),
    ]


def score_need(inputs: NeedImpactInputs) -> DimensionScore:
    data_mode = inputs.data_mode
    enrichment = inputs.enrichment if data_mode != DataMode.REAL else None
    components: list[SignalComponent] = []
    if enrichment is None:
        components.extend(_real_need_unavailable(data_mode))
        if disaster_text_flag(inputs.work_description, inputs.category):
            components.append(
                SignalComponent(
                    key="disaster_text_context",
                    label="Disaster keywords in work description",
                    available=True,
                    score=None,
                    weight=0.0,
                    source="project.work_description",
                    data_mode=data_mode.value,
                    synthetic=False,
                    explanation=(
                        "Observed work description contains disaster-related words. "
                        "This is contextual text only and is not used as a Need Score."
                    ),
                    used_in_score=False,
                )
            )
    else:
        components.append(
            _synthetic_component(
                "population",
                "Population need",
                NEED_COMPONENT_WEIGHTS["population"],
                enrichment.population_need_index,
                data_mode,
                "TEST/SYNTHETIC population-need index. Not a census fact.",
            )
        )
        components.append(
            _synthetic_component(
                "infrastructure_gap",
                "Infrastructure gap",
                NEED_COMPONENT_WEIGHTS["infrastructure_gap"],
                enrichment.infrastructure_gap_index,
                data_mode,
                "TEST/SYNTHETIC infrastructure-gap index. Not a government statistic.",
            )
        )
        components.append(
            _synthetic_component(
                "underserved_area",
                "Underserved-area indicator",
                NEED_COMPONENT_WEIGHTS["underserved_area"],
                enrichment.underserved_index,
                data_mode,
                "TEST/SYNTHETIC underserved-area index. Not a government statistic.",
            )
        )
        disaster_score = 90.0 if enrichment.disaster_flag else (10.0 if enrichment.disaster_flag is False else None)
        components.append(
            _synthetic_component(
                "disaster_context",
                "Disaster / essential-service context",
                NEED_COMPONENT_WEIGHTS["disaster_context"],
                disaster_score,
                data_mode,
                "TEST/SYNTHETIC disaster-context flag. Not an official disaster declaration.",
            )
        )
    score = weighted_available_score(components)
    available = score is not None
    unavailable = [item.label for item in components if item.used_in_score and not item.available]
    reasons = [
        item.explanation
        for item in components
        if item.used_in_score and item.available and item.explanation
    ]
    if not available:
        finding = INCONCLUSIVE
        explanation = (
            "Need Score is INCONCLUSIVE: verified population, infrastructure, "
            "underserved-area, and disaster statistics are unavailable and were "
            "not invented. Historical MPLADS work counts were not used as a substitute."
        )
        confidence = UNAVAILABLE_CONFIDENCE
    else:
        finding = "NEED_ASSESSED"
        explanation = (
            "Need Score combines available verified or labelled TEST/SYNTHETIC "
            "need components with documented prototype weights. Historical project "
            "count is not a need input."
        )
        confidence = 0.70 if enrichment is not None else UNAVAILABLE_CONFIDENCE
    return DimensionScore(
        name="need",
        score=score,
        available=available,
        confidence=confidence,
        finding=finding,
        explanation=explanation,
        components=components,
        unavailable_inputs=unavailable,
        top_reasons=reasons[:4],
    )


def score_impact(inputs: NeedImpactInputs) -> DimensionScore:
    data_mode = inputs.data_mode
    enrichment = inputs.enrichment if data_mode != DataMode.REAL else None
    relevance_score, _band, relevance_explanation = essential_service_relevance(
        inputs.category, inputs.work_description
    )
    components: list[SignalComponent] = []
    if enrichment is None:
        components.append(
            _unavailable(
                "beneficiary_count",
                "Beneficiary count",
                IMPACT_COMPONENT_WEIGHTS["beneficiary_count"],
                "Beneficiary count is unavailable in the current public MPLADS extract "
                "and was not invented.",
                data_mode,
            )
        )
        components.append(
            _unavailable(
                "community_coverage",
                "Expected community coverage",
                IMPACT_COMPONENT_WEIGHTS["community_coverage"],
                "Expected community coverage is unavailable and was not invented.",
                data_mode,
            )
        )
        components.append(
            _unavailable(
                "infrastructure_gap",
                "Infrastructure gap",
                IMPACT_COMPONENT_WEIGHTS["infrastructure_gap"],
                "Infrastructure-gap statistics are unavailable and were not invented.",
                data_mode,
            )
        )
    else:
        components.append(
            _synthetic_component(
                "beneficiary_count",
                "Beneficiary count",
                IMPACT_COMPONENT_WEIGHTS["beneficiary_count"],
                beneficiary_score(enrichment.beneficiary_count),
                data_mode,
                (
                    f"TEST/SYNTHETIC beneficiary count {enrichment.beneficiary_count} "
                    "mapped with documented prototype bands. Not a government headcount."
                    if enrichment.beneficiary_count is not None
                    else SYNTHETIC_VALUE_NOTE
                ),
            )
        )
        components.append(
            _synthetic_component(
                "community_coverage",
                "Expected community coverage",
                IMPACT_COMPONENT_WEIGHTS["community_coverage"],
                enrichment.community_coverage_index,
                data_mode,
                "TEST/SYNTHETIC community-coverage index. Not a government statistic.",
            )
        )
        components.append(
            _synthetic_component(
                "infrastructure_gap",
                "Infrastructure gap",
                IMPACT_COMPONENT_WEIGHTS["infrastructure_gap"],
                enrichment.infrastructure_gap_index,
                data_mode,
                "TEST/SYNTHETIC infrastructure-gap index. Not a government statistic.",
            )
        )
    if relevance_score is None:
        components.append(
            _unavailable(
                "essential_service_relevance",
                "Essential-service relevance",
                IMPACT_COMPONENT_WEIGHTS["essential_service_relevance"],
                relevance_explanation,
                data_mode,
            )
        )
    else:
        components.append(
            SignalComponent(
                key="essential_service_relevance",
                label="Essential-service relevance",
                available=True,
                score=clip_score(relevance_score),
                weight=IMPACT_COMPONENT_WEIGHTS["essential_service_relevance"],
                source="project.category + project.work_description",
                data_mode=data_mode.value,
                synthetic=False,
                explanation=relevance_explanation,
            )
        )
    score = weighted_available_score(components)
    available = score is not None
    unavailable = [item.label for item in components if item.used_in_score and not item.available]
    reasons = [
        item.explanation
        for item in components
        if item.used_in_score and item.available and item.explanation
    ]
    if not available:
        finding = INCONCLUSIVE
        explanation = (
            "Impact Score is INCONCLUSIVE: beneficiary counts, community coverage, "
            "and essential-service relevance could not be assessed from available "
            "verified inputs. No impact statistics were invented."
        )
        confidence = UNAVAILABLE_CONFIDENCE
    else:
        finding = "IMPACT_ASSESSED"
        explanation = (
            "Impact Score combines available components with documented prototype "
            "weights. Allocation amount is not used as an impact proxy."
        )
        confidence = 0.70 if enrichment is not None else 0.40
    return DimensionScore(
        name="impact",
        score=score,
        available=available,
        confidence=confidence,
        finding=finding,
        explanation=explanation,
        components=components,
        unavailable_inputs=unavailable,
        top_reasons=reasons[:4],
    )


def score_urgency(inputs: NeedImpactInputs, as_of: date | None = None) -> DimensionScore:
    data_mode = inputs.data_mode
    enrichment = inputs.enrichment if data_mode != DataMode.REAL else None
    as_of_date = as_of or REAL_AS_OF_DATE
    components: list[SignalComponent] = []
    future_like = inputs.lifecycle_stage in {"FUTURE", "UNKNOWN"}
    waiting = waiting_urgency_score(inputs.recommended_date, as_of_date) if future_like else None
    if waiting is None:
        reason = (
            "Urgency from waiting time is unavailable: recommendation date is missing "
            "or the work is not in a proposed/future lifecycle stage derived from STATUS."
        )
        if not future_like:
            reason = (
                "Need & Impact V1 urgency from waiting time applies to proposed/future "
                f"works. This work's lifecycle_stage is {inputs.lifecycle_stage}."
            )
        components.append(_unavailable("waiting_time", "Waiting time since recommendation", 0.70, reason, data_mode))
    else:
        components.append(
            SignalComponent(
                key="waiting_time",
                label="Waiting time since recommendation",
                available=True,
                score=waiting,
                weight=0.70,
                source="project.recommended_date",
                data_mode=data_mode.value,
                explanation=(
                    f"Prototype waiting-time urgency from recommended_date to as-of "
                    f"{as_of_date.isoformat()}. Not an official MPLADS urgency rule."
                ),
            )
        )
    if disaster_text_flag(inputs.work_description, inputs.category):
        components.append(
            SignalComponent(
                key="disaster_text",
                label="Disaster keywords in observed text",
                available=True,
                score=DISASTER_TEXT_URGENCY,
                weight=0.30,
                source="project.work_description",
                data_mode=data_mode.value,
                explanation=(
                    "Observed work description contains disaster-related words. "
                    "This is not a verified disaster declaration."
                ),
            )
        )
    elif enrichment is not None and enrichment.urgency_index is not None:
        components.append(
            _synthetic_component(
                "urgency_index",
                "TEST/SYNTHETIC urgency index",
                0.30,
                enrichment.urgency_index,
                data_mode,
                "TEST/SYNTHETIC urgency index. Not an official urgency rating.",
            )
        )
    else:
        components.append(
            _unavailable(
                "disaster_text",
                "Disaster keywords in observed text",
                0.30,
                "No disaster-related words were observed in category or work description. "
                "No disaster statistic was invented.",
                data_mode,
            )
        )
    score = weighted_available_score(components)
    available = score is not None
    unavailable = [item.label for item in components if item.used_in_score and not item.available]
    reasons = [
        item.explanation
        for item in components
        if item.used_in_score and item.available and item.explanation
    ]
    if not available:
        finding = INCONCLUSIVE
        explanation = "Urgency is INCONCLUSIVE: no supported waiting-time or disaster-text input is available."
        confidence = UNAVAILABLE_CONFIDENCE
    else:
        finding = "URGENCY_ASSESSED"
        explanation = "Urgency uses only supported waiting-time and observed-text or labelled TEST/SYNTHETIC inputs."
        confidence = 0.55 if enrichment is not None else 0.40
    return DimensionScore(
        name="urgency",
        score=score,
        available=available,
        confidence=confidence,
        finding=finding,
        explanation=explanation,
        components=components,
        unavailable_inputs=unavailable,
        top_reasons=reasons[:3],
    )


def combine_priority(
    need: DimensionScore,
    impact: DimensionScore,
    urgency: DimensionScore,
) -> tuple[float | None, str]:
    """Need and Impact are both required for HIGH/MEDIUM/LOW. Urgency is optional."""
    if not need.available or not impact.available:
        return None, INCONCLUSIVE
    parts = [
        ("need", need.score, PRIORITY_WEIGHTS["need"]),
        ("impact", impact.score, PRIORITY_WEIGHTS["impact"]),
    ]
    if urgency.available and urgency.score is not None:
        parts.append(("urgency", urgency.score, PRIORITY_WEIGHTS["urgency"]))
    total_weight = sum(weight for _, _, weight in parts)
    raw = sum((weight / total_weight) * float(score) for _, score, weight in parts)
    score = clip_score(raw)
    assert score is not None
    if score >= HIGH_PRIORITY_MIN:
        return score, HIGH_PRIORITY
    if score >= MEDIUM_PRIORITY_MIN:
        return score, MEDIUM_PRIORITY
    return score, LOW_PRIORITY


def evidence_confidence(
    *,
    data_mode: DataMode,
    need: DimensionScore,
    impact: DimensionScore,
    urgency: DimensionScore,
    enrichment: SyntheticNeedImpactEnrichment | None,
) -> float:
    need_slots = [item for item in need.components if item.used_in_score]
    impact_slots = [item for item in impact.components if item.used_in_score]
    slots = need_slots + impact_slots
    if not slots:
        coverage = 0.0
    else:
        coverage = sum(1 for item in slots if item.available) / len(slots)
    if not need.available and not impact.available:
        base = UNAVAILABLE_CONFIDENCE
    else:
        quality = 0.75 if enrichment is not None else 0.45
        if urgency.available:
            quality = min(1.0, quality + 0.05)
        base = 0.50 * coverage + 0.35 * quality + 0.15 * (0.7 if enrichment is not None else 0.4)
    if data_mode == DataMode.REAL:
        cap = REAL_CONFIDENCE_CAP
        if not need.available or not impact.available:
            cap = min(cap, PARTIAL_CONFIDENCE_CAP)
    elif data_mode == DataMode.HYBRID:
        cap = HYBRID_CONFIDENCE_CAP
    else:
        cap = SYNTHETIC_CONFIDENCE_CAP
    return round(max(0.0, min(cap, base)), 4)


def enrichment_label_for(inputs: NeedImpactInputs) -> str | None:
    if inputs.data_mode == DataMode.REAL or inputs.enrichment is None:
        return None
    return inputs.enrichment.label or HYBRID_ENRICHMENT_LABEL
