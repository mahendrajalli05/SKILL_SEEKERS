"""Milestone amount calculations.

Missing REAL expenditure stays unavailable. Synthetic amounts stay labelled.
"""

from __future__ import annotations

from app.engines.milestone.constants import SYNTHETIC_VALUE_NOTE
from app.engines.milestone.types import AmountView
from app.engines.pce.compare import relative_difference
from app.engines.pce.constants import RELATIVE_MISMATCH_THRESHOLD


def cumulative_for(
    *,
    milestone_number: int | None,
    planned_amount: float | None,
    ordered: list[tuple[int | None, float | None]],
) -> float | None:
    """Sum planned amounts for this milestone and earlier numbered rows.

    If this milestone has no planned amount, cumulative is unavailable.
    Earlier missing amounts are treated as 0 only when this milestone
    itself has a planned amount.
    """
    if planned_amount is None:
        return None
    if milestone_number is None:
        return float(planned_amount)
    total = 0.0
    for number, amount in ordered:
        if number is None:
            continue
        if number <= milestone_number and amount is not None:
            total += float(amount)
    return total


def remaining_for(
    *,
    cumulative_amount: float | None,
    total_planned: float | None,
) -> float | None:
    if cumulative_amount is None or total_planned is None:
        return None
    remaining = float(total_planned) - float(cumulative_amount)
    return remaining


def total_planned_amount(
    ordered: list[tuple[int | None, float | None]],
    *,
    fallback_allocation: float | None = None,
    allow_allocation_fallback: bool = False,
) -> float | None:
    amounts = [float(amount) for _, amount in ordered if amount is not None]
    if amounts:
        return sum(amounts)
    if allow_allocation_fallback and fallback_allocation is not None:
        return float(fallback_allocation)
    return None


def expenditure_inconsistent(
    claimed: float | None,
    planned: float | None,
    evidence_expenditure: float | None = None,
) -> bool:
    if claimed is None:
        return False
    if planned is not None and float(claimed) > float(planned) * (1.0 + RELATIVE_MISMATCH_THRESHOLD):
        return True
    if evidence_expenditure is not None:
        return relative_difference(float(claimed), float(evidence_expenditure)) > RELATIVE_MISMATCH_THRESHOLD
    return False


def progress_inconsistent(claimed: float | None, evidence_supported: float | None) -> bool:
    if claimed is None or evidence_supported is None:
        return False
    return relative_difference(float(claimed), float(evidence_supported)) > RELATIVE_MISMATCH_THRESHOLD


def amount_view(
    *,
    planned_amount: float | None,
    cumulative_amount: float | None,
    claimed_expenditure: float | None,
    remaining_planned_amount: float | None,
    claimed_expenditure_synthetic: bool = False,
    data_mode: str = "REAL",
) -> AmountView:
    note = None
    if claimed_expenditure is None:
        if data_mode == "REAL":
            note = "Expenditure is unavailable in the current public extract and was not recorded."
        else:
            note = "Claimed expenditure is unavailable for this milestone."
    if claimed_expenditure_synthetic:
        note = SYNTHETIC_VALUE_NOTE
    return AmountView(
        planned_amount=planned_amount,
        cumulative_amount=cumulative_amount,
        claimed_expenditure=claimed_expenditure,
        remaining_planned_amount=remaining_planned_amount,
        planned_amount_available=planned_amount is not None,
        cumulative_amount_available=cumulative_amount is not None,
        claimed_expenditure_available=claimed_expenditure is not None,
        remaining_available=remaining_planned_amount is not None,
        claimed_expenditure_synthetic=claimed_expenditure_synthetic,
        note=note,
    )
