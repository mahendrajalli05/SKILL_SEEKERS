"""TEST/SYNTHETIC Need & Impact enrichment loader.

Small controlled fixtures only. Not a census dataset and not merged into
the real MPLADS extract. REAL mode must never consume these values.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import REPO_ROOT
from app.engines.need.constants import HYBRID_ENRICHMENT_LABEL, HYBRID_ENRICHMENT_RELATIVE_PATH
from app.engines.need.types import SyntheticNeedImpactEnrichment

DEFAULT_ENRICHMENT_PATH = REPO_ROOT / HYBRID_ENRICHMENT_RELATIVE_PATH

_CACHE: dict[str, dict[str, SyntheticNeedImpactEnrichment]] = {}


def _opt_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _opt_int(value: object) -> int | None:
    number = _opt_float(value)
    if number is None:
        return None
    return int(number)


def _opt_bool(value: object) -> bool | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().casefold()
    if text in {"1", "true", "yes"}:
        return True
    if text in {"0", "false", "no"}:
        return False
    return None


def row_to_enrichment(row: dict[str, Any]) -> SyntheticNeedImpactEnrichment | None:
    internal_id = str(row.get("internal_project_id") or "").strip()
    if not internal_id:
        return None
    return SyntheticNeedImpactEnrichment(
        internal_project_id=internal_id,
        label=str(row.get("label") or HYBRID_ENRICHMENT_LABEL),
        population_need_index=_opt_float(row.get("population_need_index")),
        infrastructure_gap_index=_opt_float(row.get("infrastructure_gap_index")),
        underserved_index=_opt_float(row.get("underserved_index")),
        beneficiary_count=_opt_int(row.get("beneficiary_count")),
        community_coverage_index=_opt_float(row.get("community_coverage_index")),
        disaster_flag=_opt_bool(row.get("disaster_flag")),
        urgency_index=_opt_float(row.get("urgency_index")),
    )


def load_need_impact_enrichment(
    path: Path | None = None,
) -> dict[str, SyntheticNeedImpactEnrichment]:
    json_path = path or DEFAULT_ENRICHMENT_PATH
    key = str(json_path.resolve()) if json_path.exists() else str(json_path)
    if key in _CACHE:
        return _CACHE[key]
    records: dict[str, SyntheticNeedImpactEnrichment] = {}
    if json_path.is_file():
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        rows = payload.get("records", payload) if isinstance(payload, dict) else payload
        if isinstance(rows, list):
            for row in rows:
                if not isinstance(row, dict):
                    continue
                item = row_to_enrichment(row)
                if item is not None:
                    records[item.internal_project_id] = item
    _CACHE[key] = records
    return records


def reset_need_impact_enrichment_cache() -> None:
    _CACHE.clear()


def enrichment_for(
    internal_project_id: str,
    *,
    overlay: dict[str, SyntheticNeedImpactEnrichment] | None = None,
    path: Path | None = None,
) -> SyntheticNeedImpactEnrichment | None:
    if overlay and internal_project_id in overlay:
        return overlay[internal_project_id]
    return load_need_impact_enrichment(path).get(internal_project_id)
