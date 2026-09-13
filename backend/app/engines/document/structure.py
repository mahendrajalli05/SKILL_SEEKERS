"""Normalized blueprint / BOQ structure. All fields optional. No invented rates."""

from __future__ import annotations

from typing import Any

from app.engines.document.types import ExtractedField, MilestoneItem, NormalizedStructure, QuantityItem


def _as_field(payload: dict[str, Any] | None) -> ExtractedField | None:
    if not payload:
        return None
    field = ExtractedField(
        name=str(payload.get("name") or ""),
        value=payload.get("value"),
        unit=payload.get("unit"),
        confidence=payload.get("confidence"),
        extraction_method=str(payload.get("extraction_method") or "unavailable"),
        source_location=payload.get("source_location"),
        available=bool(payload.get("available")),
        unavailable_reason=payload.get("unavailable_reason"),
    )
    return field


def build_structure(extraction: dict[str, Any]) -> NormalizedStructure:
    fields = {item["name"]: item for item in extraction.get("fields") or [] if isinstance(item, dict)}
    dimensions: dict[str, ExtractedField] = {}
    for name in ("length", "width", "height", "area", "volume", "floors"):
        field = _as_field(fields.get(name))
        if field is not None:
            dimensions[name] = field
    finance: dict[str, ExtractedField] = {}
    for name in ("estimate_amount", "item_amount", "total_amount"):
        field = _as_field(fields.get(name))
        if field is not None:
            key = {"estimate_amount": "estimate", "item_amount": "item_amount", "total_amount": "total_amount"}[name]
            finance[key] = field
    dates: dict[str, ExtractedField] = {}
    for name, key in (("planned_start", "planned_start"), ("planned_completion", "planned_completion")):
        field = _as_field(fields.get(name))
        if field is not None:
            dates[key] = field
    quantities = [
        QuantityItem(
            item=item.get("item"),
            quantity=item.get("quantity"),
            unit=item.get("unit"),
            confidence=item.get("confidence"),
            source_location=item.get("source_location"),
        )
        for item in extraction.get("quantities") or []
        if isinstance(item, dict)
    ]
    milestones = [
        MilestoneItem(
            milestone=item.get("milestone"),
            amount=item.get("amount"),
            target_date=item.get("target_date"),
            confidence=item.get("confidence"),
            source_location=item.get("source_location"),
        )
        for item in extraction.get("milestones") or []
        if isinstance(item, dict)
    ]
    scope = None
    scope_field = fields.get("scope_description") or fields.get("work_name")
    if scope_field and scope_field.get("available"):
        scope = scope_field.get("value")
    return NormalizedStructure(
        scope_description=None if scope is None else str(scope),
        quantities=quantities,
        dimensions=dimensions,
        finance=finance,
        milestones=milestones,
        dates=dates,
    )
