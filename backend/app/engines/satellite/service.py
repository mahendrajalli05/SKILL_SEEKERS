"""Satellite / Remote-Sensing Consistency V1 orchestration.

Reuses Geospatial Consistency V1 location representation.
Writes Evidence Object V1. Does not change Risk Fusion V1.1.
"""

from __future__ import annotations

import re
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.domain.enums import DataMode
from app.engines.geo.image_gps import image_location_from_photo
from app.engines.geo.location import project_location_for
from app.engines.image.repository import list_project_photos
from app.engines.pce.plan import assemble_plan
from app.engines.pce.repository import get_plan, list_claims
from app.engines.pce.service import assembled_claim_from_row, empty_claim
from app.engines.pce.types import AssembledClaim
from app.engines.satellite.constants import (
    ALLOWED_TEST_SCENARIOS,
    DEFAULT_AOI_RADIUS_M,
    ENGINE_NAME,
    ENGINE_VERSION,
    FORBIDDEN_OVERCLAIM_PATTERN,
    GOVERNANCE_NOTE,
    PROVIDER_MOCK,
    PROVIDER_UNAVAILABLE,
)
from app.engines.satellite.dates import parse_claim_completion_date, parse_iso_date
from app.engines.satellite.errors import SatelliteError
from app.engines.satellite.evaluate import evaluate_satellite
from app.engines.satellite.pce import frame_against_claim
from app.engines.satellite.providers.registry import normalize_provider_name, resolve_provider
from app.engines.satellite.scale import classify_work_scale
from app.engines.satellite.types import ImageryRequest, SatelliteResult
from app.evidence.adapters.satellite import result_to_evidence_objects
from app.evidence.constants import FRAUD_CLAIM_PATTERN
from app.evidence.repository import add_evidence_object
from app.models.evidence import EvidenceObjectRow
from app.models.project import Project
from app.models.snapshot import DatasetSnapshot

_FRAUD_RE = re.compile(FRAUD_CLAIM_PATTERN, re.IGNORECASE)
_OVERCLAIM_RE = re.compile(FORBIDDEN_OVERCLAIM_PATTERN, re.IGNORECASE)


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


def reject_forbidden_wording(*values: object) -> None:
    blob = "\n".join("" if item is None else str(item) for item in values)
    if _FRAUD_RE.search(blob) or _OVERCLAIM_RE.search(blob):
        raise SatelliteError(
            "Satellite evidence must not claim fraud or unverified physical certainty.",
            code="forbidden_wording",
            status_code=422,
        )


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


def _latest_claim(session: Session, project: Project, data_mode: DataMode) -> AssembledClaim:
    claims = [
        item
        for item in list_claims(session, project.id)
        if not (data_mode == DataMode.REAL and str(item.data_mode or "").upper() not in {"", "REAL"})
    ]
    if not claims:
        return empty_claim(project, data_mode)
    return assembled_claim_from_row(project, claims[0])


def _plan_dates(session: Session, project: Project, data_mode: DataMode) -> tuple[date | None, date | None]:
    stored = get_plan(session, project.id)
    assembled = assemble_plan(project, stored, data_mode=data_mode)
    planned = parse_iso_date(assembled.planned_start_date)
    completion = parse_iso_date(assembled.planned_completion_date)
    return planned, completion


def _delete_satellite_for_mode(session: Session, project_id: int, data_mode: DataMode) -> None:
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


def persist_satellite_evidence(session: Session, project: Project, result: SatelliteResult) -> list[str]:
    snapshot = _snapshot(session, project)
    objects = result_to_evidence_objects(project, result, snapshot=snapshot)
    _delete_satellite_for_mode(session, project.id, result.data_mode)
    ids: list[str] = []
    for obj in objects:
        reject_forbidden_wording(obj.finding, obj.explanation)
        row = add_evidence_object(session, obj)
        if row.evidence_id:
            ids.append(row.evidence_id)
    return ids


def _allow_mock(data_mode: DataMode, provider_name: str, test_scenario: str | None) -> bool:
    if data_mode == DataMode.REAL:
        return False
    settings = get_settings()
    if bool(getattr(settings, "satellite_mock_enabled", False)):
        return True
    if normalize_provider_name(provider_name) == PROVIDER_MOCK:
        return True
    return bool(test_scenario)


def check_project_satellite(
    session: Session,
    project: Project,
    data_mode: DataMode,
    *,
    provider_name: str | None = None,
    test_scenario: str | None = None,
    date_start: str | None = None,
    date_end: str | None = None,
    aoi_radius_m: float | None = None,
    persist: bool = True,
) -> SatelliteResult:
    reject_forbidden_wording(data_mode.value, test_scenario, provider_name)
    snapshot = _snapshot(session, project)
    location = project_location_for(project, data_mode, snapshot=snapshot)
    photos = _visible_photos(session, project, data_mode)
    image_locations = [image_location_from_photo(photo) for photo in photos]
    claim = _latest_claim(session, project, data_mode)
    planned_start, planned_completion = _plan_dates(session, project, data_mode)
    claimed_completion = parse_claim_completion_date(
        claim.claimed_completion_state,
        claim.claim_date,
        claim.claimed_progress,
    )
    milestone_date = parse_iso_date(claim.claim_date) if claim.milestone_claimed else planned_completion

    requested_start = parse_iso_date(date_start) or planned_start
    requested_end = parse_iso_date(date_end) or claimed_completion or planned_completion
    radius = DEFAULT_AOI_RADIUS_M if aoi_radius_m is None else float(aoi_radius_m)
    if radius <= 0:
        raise SatelliteError(
            "Area-of-interest radius must be a positive number of metres.",
            code="invalid_aoi_radius",
            status_code=422,
        )

    scenario = None if not test_scenario else str(test_scenario).strip().lower()
    if scenario and scenario not in ALLOWED_TEST_SCENARIOS:
        raise SatelliteError(
            "Unknown TEST satellite scenario.",
            code="invalid_test_scenario",
            status_code=422,
        )
    if data_mode == DataMode.REAL:
        scenario = None

    settings = get_settings()
    configured = provider_name or getattr(settings, "satellite_provider", PROVIDER_UNAVAILABLE)
    allow_mock = _allow_mock(data_mode, str(configured), scenario)
    provider = resolve_provider(configured, data_mode, allow_mock=allow_mock)
    work_scale = classify_work_scale(project.work_description, project.category)
    request = ImageryRequest(
        latitude=location.latitude,
        longitude=location.longitude,
        date_start=requested_start,
        date_end=requested_end,
        aoi_radius_m=radius,
        data_mode=data_mode,
        test_scenario=scenario,
        work_scale=work_scale,
    )
    availability = provider.fetch_scenes(request)
    result = evaluate_satellite(
        project_id=project.id,
        internal_project_id=project.internal_project_id,
        data_mode=data_mode,
        project_location=location,
        availability=availability,
        image_locations=image_locations,
        work_scale=work_scale,
        planned_date=planned_start,
        claimed_completion=claimed_completion,
        milestone_date=milestone_date,
        aoi_radius_m=radius,
    )
    result.engine_version = ENGINE_VERSION
    result.note = GOVERNANCE_NOTE
    result.plan_claim_evidence = frame_against_claim(result, claim)
    result.provenance = location.provenance
    reject_forbidden_wording(
        result.explanation,
        result.overall_result,
        result.finding,
        result.plan_claim_evidence.note,
    )
    if persist:
        result.evidence_ids = persist_satellite_evidence(session, project, result)
    return result
