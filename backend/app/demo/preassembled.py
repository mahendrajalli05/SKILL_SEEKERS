"""Preassembled READ-ONLY demo-case fixture payloads for controlled prototype demonstration.

These fixtures provide deterministic, precomputed payloads for the 4 fixed
demo cases (GHOST, OVERBILL, STUCK, CLEAN) to ensure instant, reliable loading
without repeated database round-trips or live engine recomputations.
All cases are explicitly labeled:
DEMO / SYNTHETIC / CONTROLLED PROTOTYPE.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from app.demo.catalog import normalize_case_id

_FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
_CACHE: dict[str, dict[str, Any]] = {}


def load_preassembled_case(case_id: str) -> dict[str, Any]:
    """Load the preassembled fixture payload for a controlled demo case."""
    key = normalize_case_id(case_id)
    if key not in _CACHE:
        fixture_path = _FIXTURES_DIR / f"{key.lower()}.json"
        if not fixture_path.is_file():
            raise FileNotFoundError(f"Demo case fixture file not found: {fixture_path}")
        _CACHE[key] = json.loads(fixture_path.read_text(encoding="utf-8"))
    return copy.deepcopy(_CACHE[key])


def has_preassembled_case(case_id: str) -> bool:
    try:
        key = normalize_case_id(case_id)
        fixture_path = _FIXTURES_DIR / f"{key.lower()}.json"
        return fixture_path.is_file()
    except KeyError:
        return False
