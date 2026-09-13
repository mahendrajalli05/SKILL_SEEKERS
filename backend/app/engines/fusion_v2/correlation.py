"""Correlation / double-counting safeguards for Risk Fusion V2.

Independent corroboration is retained. Multiple representations of the
same underlying evidence are discounted, not summed as two full signals.
"""

from __future__ import annotations

from app.domain.schemas.evidence import EvidenceObject
from app.engines.fusion_v2.constants import (
    CORR_CITIZEN_GEO,
    CORR_CITIZEN_GEO_KEEP,
    CORR_DOCUMENT_PCE,
    CORR_DOCUMENT_PCE_KEEP,
    CORR_IMAGE_FAMILY,
    CORR_IMAGE_FAMILY_KEEP,
    CORR_PCE_MILESTONE,
    CORR_PCE_MILESTONE_KEEP,
    CORR_SEMANTIC,
    CORR_SEMANTIC_KEEP,
    CORR_SEMANTIC_PARTIAL_KEEP,
    GROUP_CITIZEN,
    GROUP_DOCUMENT,
    GROUP_FORENSICS,
    GROUP_GEOSPATIAL,
    GROUP_GRAPH,
    GROUP_IMAGE,
    GROUP_MILESTONE,
    GROUP_OVERLAP,
    GROUP_PCE,
)
from app.engines.fusion_v2.ingest import (
    citizen_is_location_driven,
    graph_has_independent_non_overlap,
    graph_is_overlap_derived,
)
from app.engines.fusion_v2.types import GroupContribution, V2EvidenceState


def _by_id(groups: list[GroupContribution]) -> dict[str, GroupContribution]:
    return {item.group_id: item for item in groups}


def _usable(item: GroupContribution | None) -> bool:
    if item is None:
        return False
    return item.state in {V2EvidenceState.ASSESSABLE, V2EvidenceState.LOW_CONFIDENCE}


def _pre_contribution(item: GroupContribution) -> float:
    if item.confidence_adjusted_score is None:
        return 0.0
    return item.weight * float(item.confidence_adjusted_score)


def _discount(
    weaker: GroupContribution,
    factor: float,
    reason: str,
) -> None:
    weaker.correlation_factor = min(weaker.correlation_factor, factor)
    weaker.independent = False
    if weaker.correlation_reason:
        weaker.correlation_reason = f"{weaker.correlation_reason}; {reason}"
    else:
        weaker.correlation_reason = reason


def apply_correlation(
    groups: list[GroupContribution],
    representatives: dict[str, EvidenceObject],
) -> list[GroupContribution]:
    """Mutate correlation_factor in place. Does not renormalize missing weights."""
    lookup = _by_id(groups)
    overlap = lookup.get(GROUP_OVERLAP)
    graph = lookup.get(GROUP_GRAPH)
    if _usable(overlap) and _usable(graph):
        graph_obj = representatives.get(GROUP_GRAPH)
        if graph_obj is not None and graph_is_overlap_derived(graph_obj):
            keep = CORR_SEMANTIC_KEEP
            reason = (
                "Graph/Overlap shared semantic signal. The graph's strongest "
                "relationship is essentially the same similarity relationship "
                f"as Overlap ({CORR_SEMANTIC})."
            )
            if graph_has_independent_non_overlap(graph_obj):
                keep = CORR_SEMANTIC_PARTIAL_KEEP
                reason = (
                    "Graph shares Overlap similarity but also has an additional "
                    "non-overlap relationship signal. Partial independence applied."
                )
            left, right = overlap, graph
            if _pre_contribution(graph) < _pre_contribution(overlap):
                left, right = graph, overlap
            _discount(left, keep, reason)

    image = lookup.get(GROUP_IMAGE)
    forensics = lookup.get(GROUP_FORENSICS)
    if _usable(image) and _usable(forensics) and image.flagged and forensics.flagged:
        weaker = image if _pre_contribution(image) <= _pre_contribution(forensics) else forensics
        _discount(
            weaker,
            CORR_IMAGE_FAMILY_KEEP,
            "Image evidence and image forensics both flagged on the same photo "
            f"family ({CORR_IMAGE_FAMILY}). Weaker group discounted.",
        )

    pce = lookup.get(GROUP_PCE)
    milestone = lookup.get(GROUP_MILESTONE)
    if _usable(pce) and _usable(milestone):
        weaker = pce if _pre_contribution(pce) <= _pre_contribution(milestone) else milestone
        _discount(
            weaker,
            CORR_PCE_MILESTONE_KEEP,
            "Milestone Advisor reuses Plan→Claim→Evidence. "
            f"Weaker of PCE/Milestone discounted ({CORR_PCE_MILESTONE}).",
        )

    document = lookup.get(GROUP_DOCUMENT)
    if _usable(document) and _usable(pce) and (document.flagged or pce.flagged):
        _discount(
            document,
            CORR_DOCUMENT_PCE_KEEP,
            "Document/blueprint extraction feeds Plan→Claim→Evidence. "
            f"Document discounted when PCE is also assessable ({CORR_DOCUMENT_PCE}).",
        )

    citizen = lookup.get(GROUP_CITIZEN)
    geo = lookup.get(GROUP_GEOSPATIAL)
    citizen_obj = representatives.get(GROUP_CITIZEN)
    if (
        _usable(citizen)
        and _usable(geo)
        and citizen_obj is not None
        and citizen_is_location_driven(citizen_obj)
        and geo.flagged
        and citizen.flagged
    ):
        _discount(
            citizen,
            CORR_CITIZEN_GEO_KEEP,
            "Citizen location uses the same 500 m project-GPS comparison as "
            f"geospatial consistency ({CORR_CITIZEN_GEO}).",
        )

    # Geospatial vs satellite are independent sensors — no score discount.
    return groups
