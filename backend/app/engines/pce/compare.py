"""Deterministic Plan vs Claim vs Evidence comparisons.

Never infers a value that was not supplied. Never invents unit rates.
Never concludes fraud.
"""

from __future__ import annotations

from statistics import median

from app.engines.pce.constants import (
    COMPLETION_TOKENS,
    NO_UNIT_RATES_REASON,
    RELATIVE_MISMATCH_THRESHOLD,
    UNAVAILABLE_DIMENSIONS_REASON,
    UNAVAILABLE_EXPENDITURE_REASON,
)
from app.engines.pce.types import (
    AssembledClaim,
    AssembledEvidenceItem,
    AssembledPlan,
    ConsistencyStatus,
    FieldComparison,
)


def normalize_unit(unit: str | None) -> str:
    if not unit:
        return ""
    return unit.casefold().replace(".", "").replace(" ", "").replace("_", "")


def relative_difference(left: float, right: float) -> float:
    denom = max(abs(left), abs(right))
    if denom == 0:
        return 0.0
    return abs(left - right) / denom


def format_quantity(value: float | None, unit: str | None = None) -> str:
    if value is None:
        return "unavailable"
    if float(value).is_integer():
        text = f"{int(value):,}"
    else:
        text = f"{value:,.2f}"
    if unit:
        return f"{text} {unit}"
    return text


def format_amount(value: float | None, *, from_extract: bool = False) -> str:
    if value is None:
        return "unavailable"
    number = float(value)
    if from_extract:
        whole = f"{int(number):,}" if number.is_integer() else f"{number:,.2f}"
        return f"{whole} (unit unspecified in source)"
    lakhs = number / 100_000.0
    if lakhs >= 1:
        formatted = f"{lakhs:.4g}".rstrip("0").rstrip(".")
        return f"₹{formatted} lakh"
    whole = f"{int(number):,}" if number.is_integer() else f"{number:,.2f}"
    return f"₹{whole}"


def _numeric_status(left: float | None, right: float | None) -> ConsistencyStatus:
    if left is None or right is None:
        return ConsistencyStatus.INCONCLUSIVE
    if relative_difference(float(left), float(right)) > RELATIVE_MISMATCH_THRESHOLD:
        return ConsistencyStatus.MISMATCH
    return ConsistencyStatus.CONSISTENT


def _cost_cap_status(cap: float | None, spent: float | None) -> ConsistencyStatus:
    """Underspend is not a cost mismatch. Overrun beyond the threshold is."""
    if cap is None or spent is None:
        return ConsistencyStatus.INCONCLUSIVE
    if float(spent) > float(cap) * (1.0 + RELATIVE_MISMATCH_THRESHOLD):
        return ConsistencyStatus.MISMATCH
    return ConsistencyStatus.CONSISTENT


def _units_compatible(left_unit: str | None, right_unit: str | None) -> bool:
    a = normalize_unit(left_unit)
    b = normalize_unit(right_unit)
    if not a or not b:
        return True
    return a == b


def _compare_numeric(
    *,
    comparison_id: str,
    pair: str,
    field: str,
    left: float | None,
    right: float | None,
    left_unit: str | None = None,
    right_unit: str | None = None,
    left_label: str,
    right_label: str,
    formatter,
    missing: list[str],
) -> FieldComparison:
    if left is None or right is None:
        why = (
            f"{left_label} is {formatter(left)} and {right_label} is "
            f"{formatter(right)}. Required values are unavailable, so this "
            "comparison is INCONCLUSIVE."
        )
        return FieldComparison(
            comparison_id=comparison_id,
            pair=pair,
            field=field,
            status=ConsistencyStatus.INCONCLUSIVE,
            left_value=left,
            right_value=right,
            explanation=why,
            missing_information=list(missing),
        )
    if not _units_compatible(left_unit, right_unit):
        why = (
            f"{left_label} uses unit '{left_unit}' and {right_label} uses "
            f"unit '{right_unit}'. Unit conversion was not performed, so this "
            "comparison is INCONCLUSIVE."
        )
        return FieldComparison(
            comparison_id=comparison_id,
            pair=pair,
            field=field,
            status=ConsistencyStatus.INCONCLUSIVE,
            left_value=left,
            right_value=right,
            explanation=why,
            missing_information=["compatible units"],
        )
    status = _numeric_status(left, right)
    if status == ConsistencyStatus.MISMATCH:
        why = (
            f"{left_label} is {formatter(left)} and {right_label} is "
            f"{formatter(right)}. The relative difference exceeds "
            f"{int(RELATIVE_MISMATCH_THRESHOLD * 100)}%, so this comparison "
            "is a MISMATCH."
        )
    else:
        why = (
            f"{left_label} is {formatter(left)} and {right_label} is "
            f"{formatter(right)}. No {field} mismatch was identified from "
            "the supplied values."
        )
    return FieldComparison(
        comparison_id=comparison_id,
        pair=pair,
        field=field,
        status=status,
        left_value=left,
        right_value=right,
        explanation=why,
        missing_information=[],
    )


def _compare_cost_cap(
    *,
    comparison_id: str,
    pair: str,
    field: str,
    cap: float | None,
    spent: float | None,
    cap_label: str,
    spent_label: str,
    formatter,
    missing: list[str],
) -> FieldComparison:
    if cap is None or spent is None:
        why = (
            f"{cap_label} is {formatter(cap)} and {spent_label} is "
            f"{formatter(spent)}. Required values are unavailable, so this "
            "comparison is INCONCLUSIVE."
        )
        return FieldComparison(
            comparison_id=comparison_id,
            pair=pair,
            field=field,
            status=ConsistencyStatus.INCONCLUSIVE,
            left_value=cap,
            right_value=spent,
            explanation=why,
            missing_information=list(missing),
        )
    status = _cost_cap_status(cap, spent)
    if status == ConsistencyStatus.MISMATCH:
        why = (
            f"{spent_label} is {formatter(spent)} and {cap_label} is "
            f"{formatter(cap)}. Claimed or recorded spend exceeds the available "
            f"amount by more than {int(RELATIVE_MISMATCH_THRESHOLD * 100)}%, "
            "so this comparison is a MISMATCH."
        )
    else:
        why = (
            f"{spent_label} is {formatter(spent)} and {cap_label} is "
            f"{formatter(cap)}. No expenditure mismatch was identified from "
            "the supplied evidence."
        )
    return FieldComparison(
        comparison_id=comparison_id,
        pair=pair,
        field=field,
        status=status,
        left_value=cap,
        right_value=spent,
        explanation=why,
        missing_information=[],
    )


def _evidence_quantity(
    items: list[AssembledEvidenceItem],
) -> tuple[float | None, str | None, list[str], ConsistencyStatus | None]:
    values: list[tuple[float, str | None]] = []
    for item in items:
        if item.observed_quantity is not None:
            values.append((float(item.observed_quantity), item.observed_quantity_unit))
    if not values:
        return None, None, ["evidence quantity"], None
    units = {normalize_unit(unit) for _value, unit in values if normalize_unit(unit)}
    if len(units) > 1:
        return None, None, ["compatible evidence units"], ConsistencyStatus.INCONCLUSIVE
    nums = [value for value, _unit in values]
    unit = next((unit for _value, unit in values if unit), None)
    if len(nums) >= 2:
        spread = relative_difference(min(nums), max(nums))
        if spread > RELATIVE_MISMATCH_THRESHOLD:
            return median(nums), unit, [], ConsistencyStatus.MISMATCH
    return median(nums), unit, [], None


def _evidence_expenditure(items: list[AssembledEvidenceItem]) -> tuple[float | None, list[str]]:
    values = [float(item.observed_expenditure) for item in items if item.observed_expenditure is not None]
    if not values:
        return None, ["evidence expenditure"]
    if len(values) >= 2 and relative_difference(min(values), max(values)) > RELATIVE_MISMATCH_THRESHOLD:
        return median(values), ["conflicting evidence expenditure"]
    return median(values), []


def _claim_complete(claim: AssembledClaim) -> bool:
    if claim.claimed_progress_percent is not None and claim.claimed_progress_percent >= 100:
        return True
    tokens = " ".join(
        part for part in (claim.claimed_completion_state, claim.claimed_progress) if part
    ).casefold()
    return any(token in tokens for token in COMPLETION_TOKENS)


def compare_plan_claim_evidence(
    plan: AssembledPlan,
    claim: AssembledClaim,
    evidence_items: list[AssembledEvidenceItem],
) -> list[FieldComparison]:
    comparisons: list[FieldComparison] = []
    ev_qty, ev_qty_unit, ev_qty_missing, ev_qty_conflict = _evidence_quantity(evidence_items)
    ev_exp, ev_exp_missing = _evidence_expenditure(evidence_items)

    def amount_fmt(value: float | None) -> str:
        return format_amount(value)

    def qty_fmt(value: float | None) -> str:
        return format_quantity(value, plan.dimensions_unit or claim.claimed_quantity_unit or ev_qty_unit)

    plan_dim_missing = [] if plan.dimensions_value is not None else ["plan dimensions/area"]
    claim_qty_missing = [] if claim.claimed_quantity is not None else ["claimed quantity"]
    plan_budget_missing = [] if plan.budget_estimate is not None else ["allocation/sanctioned amount"]
    claim_exp_missing = [] if claim.claimed_expenditure is not None else ["claimed expenditure"]
    milestone_missing = [] if plan.milestone_amount is not None else ["milestone amount"]

    comparisons.append(
        _compare_numeric(
            comparison_id="quantity_plan_vs_claim",
            pair="PLAN_VS_CLAIM",
            field="quantity",
            left=plan.dimensions_value,
            right=claim.claimed_quantity,
            left_unit=plan.dimensions_unit,
            right_unit=claim.claimed_quantity_unit,
            left_label="Plan dimensions",
            right_label="claimed quantity",
            formatter=qty_fmt,
            missing=plan_dim_missing + claim_qty_missing,
        )
    )
    if ev_qty_conflict == ConsistencyStatus.INCONCLUSIVE:
        comparisons.append(
            FieldComparison(
                comparison_id="quantity_plan_vs_evidence",
                pair="PLAN_VS_EVIDENCE",
                field="quantity",
                status=ConsistencyStatus.INCONCLUSIVE,
                left_value=plan.dimensions_value,
                right_value=None,
                explanation=(
                    "Attached evidence records use different quantity units. "
                    "Unit conversion was not performed."
                ),
                missing_information=["compatible evidence units"],
            )
        )
        comparisons.append(
            FieldComparison(
                comparison_id="quantity_claim_vs_evidence",
                pair="CLAIM_VS_EVIDENCE",
                field="quantity",
                status=ConsistencyStatus.INCONCLUSIVE,
                left_value=claim.claimed_quantity,
                right_value=None,
                explanation=(
                    "Attached evidence records use different quantity units. "
                    "Unit conversion was not performed."
                ),
                missing_information=["compatible evidence units"],
            )
        )
    else:
        if ev_qty_conflict == ConsistencyStatus.MISMATCH:
            comparisons.append(
                FieldComparison(
                    comparison_id="quantity_evidence_internal",
                    pair="EVIDENCE",
                    field="quantity",
                    status=ConsistencyStatus.MISMATCH,
                    left_value=min(item.observed_quantity or 0 for item in evidence_items),
                    right_value=max(item.observed_quantity or 0 for item in evidence_items),
                    explanation=(
                        "Attached evidence records quantities that differ by more "
                        f"than {int(RELATIVE_MISMATCH_THRESHOLD * 100)}%."
                    ),
                    missing_information=[],
                )
            )
        comparisons.append(
            _compare_numeric(
                comparison_id="quantity_plan_vs_evidence",
                pair="PLAN_VS_EVIDENCE",
                field="quantity",
                left=plan.dimensions_value,
                right=ev_qty,
                left_unit=plan.dimensions_unit,
                right_unit=ev_qty_unit,
                left_label="Plan dimensions",
                right_label="evidence quantity",
                formatter=qty_fmt,
                missing=plan_dim_missing + ev_qty_missing,
            )
        )
        comparisons.append(
            _compare_numeric(
                comparison_id="quantity_claim_vs_evidence",
                pair="CLAIM_VS_EVIDENCE",
                field="quantity",
                left=claim.claimed_quantity,
                right=ev_qty,
                left_unit=claim.claimed_quantity_unit,
                right_unit=ev_qty_unit,
                left_label="Claimed quantity",
                right_label="evidence quantity",
                formatter=qty_fmt,
                missing=claim_qty_missing + ev_qty_missing,
            )
        )

    comparisons.append(
        _compare_cost_cap(
            comparison_id="cost_plan_vs_claim",
            pair="PLAN_VS_CLAIM",
            field="cost",
            cap=plan.budget_estimate,
            spent=claim.claimed_expenditure,
            cap_label="Plan allocation/estimate",
            spent_label="Claimed expenditure",
            formatter=amount_fmt,
            missing=plan_budget_missing + claim_exp_missing,
        )
    )
    comparisons.append(
        _compare_cost_cap(
            comparison_id="cost_plan_vs_evidence",
            pair="PLAN_VS_EVIDENCE",
            field="cost",
            cap=plan.budget_estimate,
            spent=ev_exp,
            cap_label="Plan allocation/estimate",
            spent_label="Evidence expenditure",
            formatter=amount_fmt,
            missing=plan_budget_missing + ev_exp_missing,
        )
    )
    comparisons.append(
        _compare_numeric(
            comparison_id="cost_claim_vs_evidence",
            pair="CLAIM_VS_EVIDENCE",
            field="cost",
            left=claim.claimed_expenditure,
            right=ev_exp,
            left_label="Claimed expenditure",
            right_label="evidence expenditure",
            formatter=amount_fmt,
            missing=claim_exp_missing + ev_exp_missing,
        )
    )
    comparisons.append(
        _compare_cost_cap(
            comparison_id="cost_claim_vs_milestone",
            pair="PLAN_VS_CLAIM",
            field="milestone_amount",
            cap=plan.milestone_amount,
            spent=claim.claimed_expenditure,
            cap_label="the available milestone allocation",
            spent_label="Claimed expenditure",
            formatter=amount_fmt,
            missing=milestone_missing + claim_exp_missing,
        )
    )

    conversion_missing = [
        item
        for item in (
            None if plan.dimensions_value is not None else "plan dimensions/area",
            None if claim.claimed_quantity is not None else "claimed quantity",
            None if plan.budget_estimate is not None else "allocation/sanctioned amount",
            None if claim.claimed_expenditure is not None else "expenditure",
            None if plan.milestone_amount is not None else "milestone amount",
        )
        if item
    ]
    comparisons.append(
        FieldComparison(
            comparison_id="quantity_cost_conversion",
            pair="QUANTITY_COST",
            field="unit_rate",
            status=ConsistencyStatus.INCONCLUSIVE,
            left_value=None,
            right_value=None,
            explanation=NO_UNIT_RATES_REASON,
            missing_information=conversion_missing or ["unit rates"],
        )
    )

    photo_only = bool(evidence_items) and ev_qty is None and ev_exp is None
    if _claim_complete(claim):
        if not evidence_items:
            comparisons.append(
                FieldComparison(
                    comparison_id="completion_claim_vs_evidence",
                    pair="CLAIM_VS_EVIDENCE",
                    field="completion",
                    status=ConsistencyStatus.INCONCLUSIVE,
                    left_value=claim.claimed_completion_state or claim.claimed_progress_percent,
                    right_value=None,
                    explanation=(
                        "Claimed completion is 100%, but no supporting document or "
                        "image evidence was supplied to verify the claim."
                    ),
                    missing_information=["supporting evidence"],
                )
            )
        elif photo_only and plan.dimensions_value is None and claim.claimed_quantity is None:
            comparisons.append(
                FieldComparison(
                    comparison_id="completion_claim_vs_evidence",
                    pair="CLAIM_VS_EVIDENCE",
                    field="completion",
                    status=ConsistencyStatus.INCONCLUSIVE,
                    left_value=claim.claimed_completion_state or claim.claimed_progress_percent,
                    right_value="photo only",
                    explanation=(
                        "Claimed completion is 100%, but the submitted evidence does "
                        "not contain sufficient information to verify the claimed "
                        "dimensions."
                    ),
                    missing_information=["plan dimensions", "claimed quantity", "evidence quantity"],
                )
            )
        elif photo_only and (plan.dimensions_value is not None or claim.claimed_quantity is not None):
            comparisons.append(
                FieldComparison(
                    comparison_id="completion_claim_vs_evidence",
                    pair="CLAIM_VS_EVIDENCE",
                    field="completion",
                    status=ConsistencyStatus.INCONCLUSIVE,
                    left_value=claim.claimed_completion_state or claim.claimed_progress_percent,
                    right_value="photo only",
                    explanation=(
                        "Claimed completion is 100%, but the submitted evidence does "
                        "not contain sufficient information to verify the claimed "
                        "dimensions."
                    ),
                    missing_information=["evidence quantity"],
                )
            )

    if plan.dimensions_value is None and claim.claimed_quantity is None and photo_only:
        comparisons.append(
            FieldComparison(
                comparison_id="dimensions_photo_only",
                pair="PLAN_VS_CLAIM_VS_EVIDENCE",
                field="quantity",
                status=ConsistencyStatus.INCONCLUSIVE,
                left_value=None,
                right_value="photo only",
                explanation=(
                    f"{UNAVAILABLE_DIMENSIONS_REASON} The attached evidence is a "
                    "photo/document without a recorded quantity, so dimensions "
                    "cannot be verified."
                ),
                missing_information=["plan dimensions", "claimed quantity", "evidence quantity"],
            )
        )

    if claim.recorded and claim.claimed_expenditure is None:
        comparisons.append(
            FieldComparison(
                comparison_id="expenditure_unavailable",
                pair="PLAN_VS_CLAIM",
                field="cost",
                status=ConsistencyStatus.INCONCLUSIVE,
                left_value=plan.budget_estimate,
                right_value=None,
                explanation=UNAVAILABLE_EXPENDITURE_REASON,
                missing_information=["claimed expenditure"],
            )
        )

    return comparisons


def overall_result(
    comparisons: list[FieldComparison],
    *,
    has_claim: bool,
    has_evidence: bool,
) -> ConsistencyStatus:
    assessable = [
        item
        for item in comparisons
        if item.comparison_id != "quantity_cost_conversion"
    ]
    if any(item.status == ConsistencyStatus.MISMATCH for item in assessable):
        return ConsistencyStatus.MISMATCH
    consistent = [item for item in assessable if item.status == ConsistencyStatus.CONSISTENT]
    if consistent and has_evidence:
        return ConsistencyStatus.CONSISTENT
    if consistent and has_claim and not has_evidence:
        return ConsistencyStatus.INCONCLUSIVE
    return ConsistencyStatus.INCONCLUSIVE


def evidence_confidence(
    comparisons: list[FieldComparison],
    overall: ConsistencyStatus,
    *,
    data_mode_cap: float,
    has_evidence: bool,
) -> float:
    usable = [item for item in comparisons if item.comparison_id != "quantity_cost_conversion"]
    assessed = [item for item in usable if item.status != ConsistencyStatus.INCONCLUSIVE]
    coverage = (len(assessed) / len(usable)) if usable else 0.0
    if overall == ConsistencyStatus.INCONCLUSIVE and not assessed:
        raw = 0.12 if has_evidence else 0.08
    elif overall == ConsistencyStatus.MISMATCH:
        raw = 0.35 + 0.45 * coverage
    else:
        raw = 0.40 + 0.45 * coverage
    return round(min(data_mode_cap, max(0.0, raw)), 4)


def collect_missing(comparisons: list[FieldComparison], plan: AssembledPlan, claim: AssembledClaim) -> list[str]:
    missing: list[str] = []
    seen: set[str] = set()
    for item in comparisons:
        for entry in item.missing_information:
            if entry not in seen:
                seen.add(entry)
                missing.append(entry)
    extras = []
    if not plan.recorded and plan.dimensions_value is None:
        extras.append("recorded plan dimensions")
    if not claim.recorded:
        extras.append("recorded claim")
    for entry in extras:
        if entry not in seen:
            seen.add(entry)
            missing.append(entry)
    return missing
