"""Project-location representation. Does not write GPS onto the real project row."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from app.config import REPO_ROOT
from app.domain.enums import DataMode, SourceType
from app.engines.geo.constants import (
    HYBRID_SYNTHETIC_LABEL,
    LOCATION_UNAVAILABLE,
    PROJECT_GPS_SYNTHETIC_SOURCE,
    PROJECT_GPS_UNAVAILABLE_SOURCE,
    REAL_LOCATION_UNAVAILABLE,
    SYNTHETIC_PROJECT_LOCATION_CONFIDENCE,
    UNAVAILABLE_CONFIDENCE,
)
from app.engines.geo.types import ProjectLocation
from app.evidence.constants import HYBRID_ENRICHMENT_RELATIVE_PATH, HYBRID_ENRICHMENT_SHA256
from app.evidence.provenance import build_provenance, build_source_ids
from app.models.project import Project
from app.models.snapshot import DatasetSnapshot

_GPS_CACHE: dict[str, dict[str, tuple[float, float]]] = {}


def enrichment_csv_path() -> Path:
    return REPO_ROOT / HYBRID_ENRICHMENT_RELATIVE_PATH


def _opt_float(value: object) -> float | None:
    text = str(value or "").strip()
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def load_hybrid_coordinates(path: Path | None = None) -> dict[str, tuple[float, float]]:
    """Load SYNTHETIC enrichment coordinates only. No scenario labels."""
    csv_path = path or enrichment_csv_path()
    key = str(csv_path.resolve()) if csv_path.exists() else str(csv_path)
    if key in _GPS_CACHE:
        return _GPS_CACHE[key]
    gps: dict[str, tuple[float, float]] = {}
    if not csv_path.is_file():
        _GPS_CACHE[key] = gps
        return gps
    with csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            internal_id = (row.get("internal_project_id") or "").strip()
            if not internal_id:
                continue
            lat = _opt_float(row.get("latitude"))
            lon = _opt_float(row.get("longitude"))
            if lat is None or lon is None:
                continue
            gps[internal_id] = (lat, lon)
    _GPS_CACHE[key] = gps
    return gps


def clear_hybrid_coordinate_cache() -> None:
    _GPS_CACHE.clear()


def _unavailable_provenance(
    project: Project,
    data_mode: DataMode,
    snapshot: DatasetSnapshot | None,
) -> dict[str, Any]:
    source_type = (
        SourceType.HYBRID_ENRICHMENT
        if data_mode == DataMode.HYBRID
        else SourceType.SYNTHETIC_TEST_RECORD
        if data_mode == DataMode.SYNTHETIC
        else SourceType.MPLADS_PROJECT_RECORD
    )
    extra = (
        REAL_LOCATION_UNAVAILABLE
        if data_mode == DataMode.REAL
        else "Project coordinates were requested from SYNTHETIC enrichment and were unavailable. Coordinates were not invented."
    )
    return build_provenance(
        project,
        data_mode=data_mode,
        source_type=source_type,
        source_ids=build_source_ids(project.internal_project_id),
        snapshot=snapshot,
        extra_notes=extra,
    ).model_dump(mode="json")


def project_location_for(
    project: Project,
    data_mode: DataMode,
    *,
    snapshot: DatasetSnapshot | None = None,
) -> ProjectLocation:
    """Return a project-location object. Never invents REAL GPS."""
    if data_mode == DataMode.REAL:
        return ProjectLocation(
            project_id=project.id,
            latitude=None,
            longitude=None,
            source=PROJECT_GPS_UNAVAILABLE_SOURCE,
            data_mode=data_mode,
            confidence=UNAVAILABLE_CONFIDENCE,
            timestamp=None,
            provenance=_unavailable_provenance(project, data_mode, snapshot),
            available=False,
            unavailable_reason=LOCATION_UNAVAILABLE,
            synthetic=False,
        )

    coords = load_hybrid_coordinates().get(project.internal_project_id)
    if coords is None:
        return ProjectLocation(
            project_id=project.id,
            latitude=None,
            longitude=None,
            source=PROJECT_GPS_UNAVAILABLE_SOURCE,
            data_mode=data_mode,
            confidence=UNAVAILABLE_CONFIDENCE,
            timestamp=None,
            provenance=_unavailable_provenance(project, data_mode, snapshot),
            available=False,
            unavailable_reason=LOCATION_UNAVAILABLE,
            synthetic=data_mode != DataMode.REAL,
        )

    lat, lon = coords
    extra = (
        f"{PROJECT_GPS_SYNTHETIC_SOURCE} Label: {HYBRID_SYNTHETIC_LABEL}. "
        "Controlled prototype testing only. Do not cite as government GPS."
    )
    source_type = (
        SourceType.SYNTHETIC_TEST_RECORD
        if data_mode == DataMode.SYNTHETIC
        else SourceType.HYBRID_ENRICHMENT
    )
    provenance = build_provenance(
        project,
        data_mode=data_mode,
        source_type=source_type,
        source_ids=build_source_ids(
            project.internal_project_id,
            [HYBRID_ENRICHMENT_RELATIVE_PATH, HYBRID_ENRICHMENT_SHA256],
        ),
        snapshot=snapshot,
        extra_notes=extra,
    )
    return ProjectLocation(
        project_id=project.id,
        latitude=lat,
        longitude=lon,
        source=PROJECT_GPS_SYNTHETIC_SOURCE,
        data_mode=data_mode,
        confidence=SYNTHETIC_PROJECT_LOCATION_CONFIDENCE,
        timestamp=None,
        provenance=provenance.model_dump(mode="json"),
        available=True,
        unavailable_reason=None,
        synthetic=True,
    )
