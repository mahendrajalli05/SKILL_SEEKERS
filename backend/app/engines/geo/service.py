"""Geospatial Consistency V1 orchestration.

Compares reported image GPS with available project coordinates.
Does not change Cost, Time, Overlap, Compliance, Fusion, Graph, PCE,
Document, or Image Evidence scoring.
"""

from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.domain.enums import DataMode
from app.engines.geo.constants import (
    DEFAULT_THRESHOLD_METERS,
    ENGINE_NAME,
    ENGINE_VERSION,
    GOVERNANCE_NOTE,
)
from app.engines.geo.errors import GeoError
from app.engines.geo.evaluate import evaluate_project
from app.engines.geo.image_gps import image_location_from_photo
from app.engines.geo.location import project_location_for
from app.engines.geo.satellite import default_satellite_provider
from app.engines.geo.types import GeospatialResult
from app.engines.image.repository import list_project_photos
from app.evidence.adapters.geo import result_to_evidence_objects
from app.evidence.constants import FRAUD_CLAIM_PATTERN
from app.evidence.repository import add_evidence_object
from app.models.evidence import EvidenceObjectRow
from app.models.project import Project
from app.models.snapshot import DatasetSnapshot

_FRAUD_RE = re.compile(FRAUD_CLAIM_PATTERN, re.IGNORECASE)


def parse_data_mode(value: str | DataMode | None, project: Project) -> DataMode:
    if project.is_synthetic:
        return DataMode.SYNTHETIC
    if isinstance(value, DataMode):
        return value
    text = str(value or "").strip().upper().replace("-", "_")
    if text in {"HYBRID", "HYBRID_TEST", "HYBRIDTEST", "HYBRID_DEMO"}:
        return DataMode.HYBRID
    if text in {"SYNTHETIC"}:
        return DataMode.SYNTHETIC
    if text in {"REAL", "REAL_DATA"}:
        return DataMode.REAL
    return DataMode.REAL


def reject_fraud_text(*values: object) -> None:
    blob = "\n".join("" if item is None else str(item) for item in values)
    if _FRAUD_RE.search(blob):
        raise GeoError(
            "Geospatial Consistency must not claim fraud or use fraud language.",
            code="fraud_language_forbidden",
            status_code=422,
        )


def resolve_threshold(value: float | int | None) -> float:
    if value is None:
        settings = get_settings()
        configured = getattr(settings, "geospatial_threshold_meters", DEFAULT_THRESHOLD_METERS)
        try:
            threshold = float(configured)
        except (TypeError, ValueError):
            threshold = DEFAULT_THRESHOLD_METERS
    else:
        threshold = float(value)
    if threshold <= 0:
        raise GeoError(
            "The prototype distance threshold must be a positive number of metres.",
            code="invalid_threshold",
            status_code=422,
        )
    return threshold


def _snapshot(session: Session, project: Project) -> DatasetSnapshot | None:
    return session.get(DatasetSnapshot, project.snapshot_id) if project.snapshot_id else project.snapshot


def _visible_photos(session: Session, project: Project, data_mode: DataMode):
    photos = list_project_photos(session, project.id)
    visible = []
    for photo in photos:
        photo_mode = str(photo.data_mode or DataMode.REAL.value).upper()
        if data_mode == DataMode.REAL and photo_mode != DataMode.REAL.value:
            continue
        visible.append(photo)
    return visible


def _delete_geo_for_mode(session: Session, project_id: int, data_mode: DataMode) -> None:
    existing = session.scalars(
        select(EvidenceObjectRow).where(
            EvidenceObjectRow.project_id == project_id,
            EvidenceObjectRow.engine == ENGINE_NAME,
            EvidenceObjectRow.data_mode == data_mode.value,
        )
    ).all()
    for row in existing:
        for fact in list(row.facts):
            session.delete(fact)
        session.delete(row)
    session.flush()


def persist_geospatial_evidence(session: Session, project: Project, result: GeospatialResult) -> list[str]:
    snapshot = _snapshot(session, project)
    objects = result_to_evidence_objects(project, result, snapshot=snapshot)
    _delete_geo_for_mode(session, project.id, result.data_mode)
    ids: list[str] = []
    for obj in objects:
        reject_fraud_text(obj.finding, obj.explanation)
        row = add_evidence_object(session, obj)
        if row.evidence_id:
            ids.append(row.evidence_id)
    return ids


def check_project_geospatial(
    session: Session,
    project: Project,
    data_mode: DataMode,
    *,
    threshold_meters: float | None = None,
    persist: bool = True,
) -> GeospatialResult:
    reject_fraud_text(data_mode.value)
    threshold = resolve_threshold(threshold_meters)
    snapshot = _snapshot(session, project)
    location = project_location_for(project, data_mode, snapshot=snapshot)
    photos = _visible_photos(session, project, data_mode)
    image_locations = [image_location_from_photo(photo) for photo in photos]
    satellite = default_satellite_provider().request_imagery(location)
    result = evaluate_project(
        project_id=project.id,
        internal_project_id=project.internal_project_id,
        data_mode=data_mode,
        project_location=location,
        image_locations=image_locations,
        threshold_meters=threshold,
        satellite=satellite,
    )
    result.engine_version = ENGINE_VERSION
    result.note = GOVERNANCE_NOTE
    result.provenance = location.provenance
    reject_fraud_text(result.explanation, result.overall_result, *(item.finding for item in result.images))
    if persist:
        result.evidence_ids = persist_geospatial_evidence(session, project, result)
        for item, evidence_id in zip(
            result.images,
            result.evidence_ids[1:],
            strict=False,
        ):
            item.evidence_id = evidence_id
    return result
