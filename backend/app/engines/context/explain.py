"""Officer-facing explanations for contextual indicators. No fraud language."""

from __future__ import annotations

from app.engines.context.constants import STATUS_AVAILABLE, STATUS_INCONCLUSIVE, STATUS_UNAVAILABLE
from app.engines.context.types import ContextObservation, ContextResult


def explain_observation(item: ContextObservation) -> str:
    kind = item.context_kind.replace("_", " ")
    if item.status == STATUS_AVAILABLE:
        year = f" Reference period: {item.reference_year}." if item.reference_year else ""
        source = f" Source: {item.source_name}." if item.source_name else ""
        return (
            f"{kind}: {item.indicator} = {item.value} {item.unit or ''} at "
            f"{item.geographic_level or 'unspecified'} level ({item.geo_key or 'no geo key'})."
            f"{year}{source} {item.notes}"
        ).strip()
    if item.status == STATUS_INCONCLUSIVE:
        return f"{kind}: {item.indicator} is INCONCLUSIVE. {item.notes}".strip()
    return f"{kind}: {item.indicator} is UNAVAILABLE. {item.notes}".strip()


def explain_result(result: ContextResult) -> str:
    available = [item for item in result.observations if item.status == STATUS_AVAILABLE]
    parts = [
        result.governance_note,
        f"{len(available)} contextual indicator(s) are AVAILABLE. "
        "External context is not a project-specific fact and is not a legal conclusion.",
    ]
    if result.assessment_kind:
        parts.append(f"Assessment kind: {result.assessment_kind}.")
    return " ".join(parts)
