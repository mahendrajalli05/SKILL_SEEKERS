"""Field access helpers for the compliance evaluator."""

from __future__ import annotations

from datetime import date
from typing import Any

from app.engines.compliance.types import ComplianceContext


def is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def field_value(context: ComplianceContext, name: str) -> Any:
    return context.field_value(name)


def missing_required(context: ComplianceContext, names: tuple[str, ...]) -> list[str]:
    missing: list[str] = []
    for name in names:
        if is_missing(field_value(context, name)):
            missing.append(name)
    return missing


def as_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def as_number(value: Any) -> float | None:
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return None
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def as_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    return None


def days_between(start: date | None, end: date | None) -> int | None:
    if start is None or end is None:
        return None
    return (end - start).days
