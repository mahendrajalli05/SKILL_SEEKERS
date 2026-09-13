"""Helpers for observation vs derived evidence facts."""

from __future__ import annotations

import json
from typing import Any

from app.domain.enums import EvidenceFactKind
from app.domain.schemas.evidence import EvidenceFact
from app.evidence.constants import OBSERVATION_FACT_KEYS


def render_fact_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, dict)):
        return json.dumps(value, sort_keys=True, default=str)
    return str(value)


def parse_fact_value(value: str) -> Any:
    if value == "":
        return None
    if value[:1] in "[{":
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    if value in {"True", "False"}:
        return value == "True"
    return value


def format_amount_statement(amount: int | float | None) -> str | None:
    if amount is None:
        return None
    if isinstance(amount, float) and amount.is_integer():
        amount = int(amount)
    if isinstance(amount, int):
        return f"Actual allocation = {amount:,}"
    return f"Actual allocation = {amount}"


def make_fact(
    key: str,
    value: object,
    source: str,
    *,
    kind: EvidenceFactKind | None = None,
    statement: str | None = None,
) -> EvidenceFact:
    resolved = kind or (
        EvidenceFactKind.OBSERVATION
        if key in OBSERVATION_FACT_KEYS
        else EvidenceFactKind.DERIVED
    )
    return EvidenceFact(
        key=key,
        value=value,
        source=source,
        kind=resolved,
        statement=statement,
    )


def confidence_unit(engine_confidence_0_100: int | float | None) -> float:
    if engine_confidence_0_100 is None:
        return 0.0
    return round(max(0.0, min(100.0, float(engine_confidence_0_100))) / 100.0, 4)
