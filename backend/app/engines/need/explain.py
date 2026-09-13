"""Need & Impact V1 explanations.

Must not claim fraud, sanction approval, or sanction denial.
"""

from __future__ import annotations

from app.engines.need.constants import (
    CONTEXT_NOT_NEED_NOTE,
    GOVERNANCE_NOTE,
    INCONCLUSIVE,
    MP_NOT_GEOGRAPHY_NOTE,
    WEIGHT_NOTE,
)
from app.engines.need.types import DimensionScore, NeedImpactInputs, NeedImpactResult


def _join(parts: list[str]) -> str:
    return " ".join(part.strip() for part in parts if item_ok(part))


def item_ok(value: str | None) -> bool:
    return bool(value and value.strip())


def dimension_reasons(dimension: DimensionScore, limit: int = 3) -> list[str]:
    reasons: list[str] = []
    for component in dimension.components:
        if not component.used_in_score:
            continue
        if component.available and component.explanation:
            reasons.append(component.explanation)
        elif not component.available and component.unavailable_reason:
            reasons.append(f"{component.label}: {component.unavailable_reason}")
        if len(reasons) >= limit:
            break
    return reasons


def explanation_for(result: NeedImpactResult, inputs: NeedImpactInputs) -> str:
    parts = [
        GOVERNANCE_NOTE,
        WEIGHT_NOTE,
        result.need.explanation,
        result.impact.explanation,
        result.urgency.explanation,
        CONTEXT_NOT_NEED_NOTE,
        MP_NOT_GEOGRAPHY_NOTE,
    ]
    if result.priority_class == INCONCLUSIVE:
        parts.append(
            "Recommended priority class is INCONCLUSIVE because Need and Impact "
            "could not both be assessed from available verified inputs. Ranking "
            "was not forced."
        )
    else:
        parts.append(
            f"Recommended priority class is {result.priority_class} from the "
            f"prototype Priority Score {result.priority_score}. This is not a "
            "funding approval."
        )
    if inputs.data_mode.value != "REAL" and inputs.enrichment is not None:
        parts.append(
            "HYBRID/SYNTHETIC need and impact values are labelled TEST/SYNTHETIC "
            "and are not government facts."
        )
    if inputs.lifecycle_stage not in {"FUTURE", "UNKNOWN"}:
        parts.append(
            f"This work's lifecycle_stage is {inputs.lifecycle_stage}. "
            "Need & Impact V1 is designed primarily for proposed/future works."
        )
    return _join(parts)


def finding_for(result: NeedImpactResult) -> str:
    if result.priority_class == INCONCLUSIVE:
        return (
            "INCONCLUSIVE need/impact assessment. Priority recommendation was not "
            "forced from insufficient inputs."
        )
    return (
        f"{result.priority_class}: prototype Priority Score {result.priority_score}. "
        "Priority recommendation only."
    )
