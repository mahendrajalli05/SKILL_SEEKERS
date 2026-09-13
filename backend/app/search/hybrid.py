"""Lookup whether a real work has a HYBRID prototype enrichment row.

Does not load scenario labels into intelligence engines. IDs only.
"""

from __future__ import annotations

import csv
from pathlib import Path

from app.pipeline.synthetic import DEFAULT_OUTPUT_CSV

_ID_CACHE: dict[str, frozenset[str]] = {}


def hybrid_internal_project_ids(path: Path | None = None) -> frozenset[str]:
    csv_path = path or DEFAULT_OUTPUT_CSV
    key = str(csv_path.resolve()) if csv_path.exists() else str(csv_path)
    cached = _ID_CACHE.get(key)
    if cached is not None:
        return cached
    ids: set[str] = set()
    if csv_path.is_file():
        with csv_path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                value = (row.get("internal_project_id") or "").strip()
                if value:
                    ids.add(value)
    frozen = frozenset(ids)
    _ID_CACHE[key] = frozen
    return frozen


def has_hybrid_enrichment(internal_project_id: str, path: Path | None = None) -> bool:
    if not internal_project_id:
        return False
    return internal_project_id in hybrid_internal_project_ids(path)


def reset_hybrid_id_cache() -> None:
    _ID_CACHE.clear()
