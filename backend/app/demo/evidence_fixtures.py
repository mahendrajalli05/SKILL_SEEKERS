"""Attach labelled HYBRID demo evidence through existing Evidence Object APIs.

Does not create new demo projects, does not modify real MPLADS project rows,
does not change intelligence formulas, and does not invent official records.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.demo.catalog import normalize_case_id
from app.demo.constants import CASE_IDS, FIXTURE_LAYER, FIXTURE_NOTICE, FIXTURE_SOURCE, internal_project_id_for
from app.demo.image_bytes import (
    GHOST_REPORTED_IMAGE_LAT,
    GHOST_REPORTED_IMAGE_LON,
    jpeg_with_exif_gps,
)
from app.domain.enums import DataMode, EvidenceEngine
from app.evidence.repository import list_project_evidence
from app.logging_config import get_logger
from app.models.project import Project
from app.search.enrichment_display import enrichment_for

logger = get_logger("sarvsakshi.demo.evidence_fixtures")

PLAN_SCOPE = {
    "GHOST": (
        "SYNTHETIC DEMO / CONTROLLED PROTOTYPE plan overlay for the GHOST case. "
        "Not an official MPLADS record."
    ),
    "OVERBILL": (
        "SYNTHETIC DEMO / CONTROLLED PROTOTYPE plan overlay for the OVER-BILL case. "
        "Not an official MPLADS record."
    ),
    "STUCK": (
        "SYNTHETIC DEMO / CONTROLLED PROTOTYPE plan overlay for the STUCK case. "
        "Not an official MPLADS record."
    ),
    "CLEAN": (
        "SYNTHETIC DEMO / CONTROLLED PROTOTYPE plan overlay for the CLEAN case. "
        "Not an official MPLADS record."
    ),
}


def _engine_name(item: Any) -> str:
    name = getattr(item, "engine_name", None)
    if hasattr(name, "value"):
        return str(name.value)
    if name:
        return str(name)
    return str(getattr(item, "engine", "") or "")


def _has_engine(session: Session, project_id: int, engine: str) -> bool:
    return any(_engine_name(item) == engine for item in list_project_evidence(session, project_id))


def _has_fixture_photo(session: Session, project_id: int) -> bool:
    from app.engines.image.repository import list_project_photos

    return any(str(photo.source or "") == FIXTURE_SOURCE for photo in list_project_photos(session, project_id))


def _hybrid_claim_exists(session: Session, project_id: int) -> bool:
    from app.engines.pce.repository import list_claims

    return any(str(row.data_mode or "").upper() == DataMode.HYBRID.value for row in list_claims(session, project_id))


def _hybrid_milestone_exists(session: Session, project_id: int) -> bool:
    from app.engines.milestone.repository import list_milestones

    return any(str(row.data_mode or "").upper() == DataMode.HYBRID.value for row in list_milestones(session, project_id))


def _lookup_demo_project(session: Session, case_id: str) -> Project | None:
    internal_id = internal_project_id_for(case_id)
    return session.scalars(select(Project).where(Project.internal_project_id == internal_id)).first()


def _plan_payload(project: Project, case_id: str) -> dict[str, Any]:
    enrichment = enrichment_for(project.internal_project_id)
    payload: dict[str, Any] = {
        "sanctioned_scope": PLAN_SCOPE[case_id],
        "budget_estimate": project.allocation_amount,
        "source": FIXTURE_SOURCE,
    }
    if enrichment is not None:
        payload["planned_start_date"] = enrichment.planned_start_date
        payload["planned_completion_date"] = enrichment.planned_completion_date
        if enrichment.milestone_amount is not None:
            payload["milestone_amount"] = enrichment.milestone_amount
        if case_id == "STUCK":
            payload["milestone_label"] = "M2 superstructure"
        elif case_id == "CLEAN":
            payload["milestone_label"] = "Planning"
        elif case_id == "OVERBILL":
            payload["milestone_label"] = "Final claim"
    return payload


def _claim_payload(project: Project, case_id: str) -> dict[str, Any]:
    enrichment = enrichment_for(project.internal_project_id)
    if case_id == "GHOST":
        return {
            "claimed_progress": "Completion claimed",
            "claimed_progress_percent": 100,
            "claimed_completion_state": "Completed as claimed",
            "claimant_source": FIXTURE_SOURCE,
        }
    if case_id == "OVERBILL":
        expenditure = None if enrichment is None else enrichment.expenditure_amount
        if expenditure is None:
            expenditure = int(project.allocation_amount or 0)
        return {
            "claimed_progress": "Completion claimed",
            "claimed_progress_percent": 100,
            "claimed_expenditure": expenditure,
            "claimed_completion_state": "Completed as claimed",
            "claimant_source": FIXTURE_SOURCE,
        }
    if case_id == "STUCK":
        progress = 12 if enrichment is None else enrichment.physical_progress_percent
        expenditure = None if enrichment is None else enrichment.expenditure_amount
        payload: dict[str, Any] = {
            "claimed_progress": "Low reported physical progress",
            "claimed_progress_percent": progress,
            "claimant_source": FIXTURE_SOURCE,
        }
        if expenditure is not None:
            payload["claimed_expenditure"] = expenditure
        return payload
    return {
        "claimed_progress": "Work not started; planning consistent",
        "claimed_progress_percent": 0 if enrichment is None else enrichment.physical_progress_percent or 0,
        "claimant_source": FIXTURE_SOURCE,
    }


def _persist_core_engines(session: Session, project: Project) -> bool:
    from app.engines.compliance.service import assess_project_compliance
    from app.engines.compliance.types import ComplianceMode
    from app.engines.cost.service import assess_project_cost
    from app.engines.time.service import assess_project_time
    from app.engines.time.types import TimeMode

    changed = False
    if not _has_engine(session, project.id, EvidenceEngine.COST.value):
        try:
            assess_project_cost(session, project.id, persist=True)
            changed = True
        except Exception as exc:  # noqa: BLE001 — fixtures must not fail the demo journey
            logger.warning("demo fixture cost persist skipped project_id=%s err=%s", project.id, exc)
    if not _has_engine(session, project.id, EvidenceEngine.TIME.value):
        try:
            assess_project_time(session, project.id, mode=TimeMode.HYBRID_TEST, persist=True)
            changed = True
        except Exception as exc:  # noqa: BLE001
            logger.warning("demo fixture time persist skipped project_id=%s err=%s", project.id, exc)
    if not _has_engine(session, project.id, EvidenceEngine.COMPLIANCE.value):
        try:
            assess_project_compliance(session, project.id, mode=ComplianceMode.HYBRID_TEST, persist=True)
            changed = True
        except Exception as exc:  # noqa: BLE001
            logger.warning("demo fixture compliance persist skipped project_id=%s err=%s", project.id, exc)
    return changed


def _upload_fixture_image(
    session: Session,
    project: Project,
    *,
    latitude: float,
    longitude: float,
    color: tuple[int, int, int],
    pattern: str,
    filename: str,
):
    from app.engines.forensics.service import run_image_forensics
    from app.engines.image.service import attach_image_to_evidence, upload_image

    payload = jpeg_with_exif_gps(latitude=latitude, longitude=longitude, color=color, pattern=pattern)
    photo = upload_image(
        session,
        project,
        payload=payload,
        filename=filename,
        declared_mime="image/jpeg",
        data_mode=DataMode.HYBRID,
        source=FIXTURE_SOURCE,
    )
    attach_image_to_evidence(session, project, photo)
    try:
        run_image_forensics(session, project, photo, data_mode=DataMode.HYBRID, persist=True)
    except Exception as exc:  # noqa: BLE001
        logger.warning("demo fixture forensics skipped photo_id=%s err=%s", photo.id, exc)
    return photo


def _ensure_image_chain(session: Session, project: Project, case_id: str) -> bool:
    from app.engines.citizen.repository import list_reports
    from app.engines.citizen.service import submit_citizen_report
    from app.engines.geo.service import check_project_geospatial
    from app.engines.satellite.constants import SCENARIO_MATCHING_LOCATION, SCENARIO_WRONG_LOCATION
    from app.engines.satellite.service import check_project_satellite

    if case_id not in {"GHOST", "CLEAN"}:
        return False
    if _has_fixture_photo(session, project.id):
        if not _has_engine(session, project.id, EvidenceEngine.GEO.value):
            check_project_geospatial(session, project, DataMode.HYBRID, persist=True)
            return True
        return False
    enrichment = enrichment_for(project.internal_project_id)
    if case_id == "GHOST":
        _upload_fixture_image(
            session,
            project,
            latitude=GHOST_REPORTED_IMAGE_LAT,
            longitude=GHOST_REPORTED_IMAGE_LON,
            color=(180, 32, 32),
            pattern="ghost",
            filename="demo-evidence-fixtures-v1-ghost.jpg",
        )
        check_project_geospatial(session, project, DataMode.HYBRID, persist=True)
        if not _has_engine(session, project.id, EvidenceEngine.SATELLITE.value):
            try:
                check_project_satellite(
                    session,
                    project,
                    DataMode.HYBRID,
                    provider_name="mock",
                    test_scenario=SCENARIO_WRONG_LOCATION,
                    persist=True,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("demo fixture satellite skipped project_id=%s err=%s", project.id, exc)
        return True
    if enrichment is None or enrichment.latitude is None or enrichment.longitude is None:
        return False
    _upload_fixture_image(
        session,
        project,
        latitude=float(enrichment.latitude),
        longitude=float(enrichment.longitude),
        color=(20, 90, 160),
        pattern="clean",
        filename="demo-evidence-fixtures-v1-clean.jpg",
    )
    if not list_reports(session, project.id):
        citizen_bytes = jpeg_with_exif_gps(
            latitude=float(enrichment.latitude),
            longitude=float(enrichment.longitude),
            color=(40, 140, 90),
            pattern="citizen",
        )
        try:
            submit_citizen_report(
                session,
                project,
                {
                    "satisfaction_rating": 4,
                    "observation_text": (
                        "Proposed work location is consistent with the labelled plan description. "
                        "Supporting citizen observation only. Not official verification."
                    ),
                    "latitude": float(enrichment.latitude),
                    "longitude": float(enrichment.longitude),
                    "capture_timestamp": "2024-06-24T09:15:00+00:00",
                },
                DataMode.HYBRID,
                image_bytes=citizen_bytes,
                filename="demo-evidence-fixtures-v1-clean-citizen.jpg",
                declared_mime="image/jpeg",
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("demo fixture citizen skipped project_id=%s err=%s", project.id, exc)
    check_project_geospatial(session, project, DataMode.HYBRID, persist=True)
    if not _has_engine(session, project.id, EvidenceEngine.SATELLITE.value):
        try:
            check_project_satellite(
                session,
                project,
                DataMode.HYBRID,
                provider_name="mock",
                test_scenario=SCENARIO_MATCHING_LOCATION,
                persist=True,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("demo fixture satellite skipped project_id=%s err=%s", project.id, exc)
    return True


def _ensure_milestone(session: Session, project: Project, case_id: str) -> bool:
    from app.engines.milestone.repository import list_milestones
    from app.engines.milestone.service import assess_milestone, create_milestone

    if case_id == "GHOST":
        return False
    if _hybrid_milestone_exists(session, project.id):
        if not _has_engine(session, project.id, EvidenceEngine.MILESTONE.value):
            rows = [
                row
                for row in list_milestones(session, project.id)
                if str(row.data_mode or "").upper() == DataMode.HYBRID.value
            ]
            if rows:
                assess_milestone(session, rows[0].id, DataMode.HYBRID, persist=True)
                return True
        return False
    enrichment = enrichment_for(project.internal_project_id)
    if case_id == "OVERBILL":
        expenditure = None if enrichment is None else enrichment.expenditure_amount
        create_milestone(
            session,
            project,
            {
                "milestone_number": 1,
                "milestone_name": "Final claim",
                "planned_amount": project.allocation_amount,
                "claimed_expenditure": expenditure,
                "completion_claimed": True,
                "synthetic": True,
            },
            DataMode.HYBRID,
        )
    elif case_id == "STUCK":
        progress = 12 if enrichment is None else enrichment.physical_progress_percent
        create_milestone(
            session,
            project,
            {
                "milestone_number": 2,
                "milestone_name": "Superstructure",
                "planned_amount": None if enrichment is None else enrichment.milestone_amount,
                "target_date": None if enrichment is None else enrichment.planned_completion_date,
                "claimed_progress": progress,
                "completion_claimed": False,
                "synthetic": True,
            },
            DataMode.HYBRID,
        )
    else:
        create_milestone(
            session,
            project,
            {
                "milestone_number": 1,
                "milestone_name": "Planning",
                "planned_amount": project.allocation_amount,
                "claimed_progress": 0,
                "synthetic": True,
            },
            DataMode.HYBRID,
        )
    rows = [
        row
        for row in list_milestones(session, project.id)
        if str(row.data_mode or "").upper() == DataMode.HYBRID.value
    ]
    if rows:
        assess_milestone(session, rows[0].id, DataMode.HYBRID, persist=True)
    return True


def ensure_demo_case_evidence(session: Session, project: Project, case_id: str) -> dict[str, Any]:
    """Idempotently attach labelled HYBRID fixtures to one existing demo project."""
    key = normalize_case_id(case_id)
    identity = {
        "internal_project_id": project.internal_project_id,
        "status": project.status,
        "allocation_amount": project.allocation_amount,
        "work_description": project.work_description,
        "constituency": project.constituency,
        "is_synthetic": project.is_synthetic,
    }
    applied: list[str] = []
    from app.engines.pce.repository import get_plan

    if get_plan(session, project.id) is None:
        from app.engines.pce.service import record_plan

        record_plan(session, project, _plan_payload(project, key), DataMode.HYBRID)
        applied.append("plan")
    if not _hybrid_claim_exists(session, project.id):
        from app.engines.pce.service import record_claim

        record_claim(session, project, _claim_payload(project, key), DataMode.HYBRID)
        applied.append("claim")
    if _persist_core_engines(session, project):
        applied.append("core_engines")
    if _ensure_image_chain(session, project, key):
        applied.append("image_chain")
    if _ensure_milestone(session, project, key):
        applied.append("milestone")
    if not _has_engine(session, project.id, EvidenceEngine.PCE.value):
        from app.engines.pce.service import verify_project

        verify_project(session, project, DataMode.HYBRID, persist=True)
        applied.append("pce")
    if (
        identity["internal_project_id"] != project.internal_project_id
        or identity["status"] != project.status
        or identity["allocation_amount"] != project.allocation_amount
        or identity["work_description"] != project.work_description
        or identity["constituency"] != project.constituency
        or identity["is_synthetic"] != project.is_synthetic
    ):
        raise RuntimeError("Demo evidence fixtures must not modify real MPLADS project records.")
    evidence = list_project_evidence(session, project.id)
    return {
        "case_id": key,
        "project_id": project.id,
        "applied": bool(applied),
        "steps": applied,
        "evidence_ids": [item.evidence_id for item in evidence if item.evidence_id],
        "data_mode": DataMode.HYBRID.value,
        "labels": ["DEMO", "SYNTHETIC", "CONTROLLED PROTOTYPE"],
        "fixture_layer": FIXTURE_LAYER,
        "official_mplads_evidence": False,
        "notice": FIXTURE_NOTICE,
    }


def ensure_all_demo_evidence(session: Session) -> dict[str, Any]:
    items: dict[str, Any] = {}
    for case_id in CASE_IDS:
        project = _lookup_demo_project(session, case_id)
        if project is None:
            items[case_id] = {"available": False, "applied": False, "evidence_ids": []}
            continue
        items[case_id] = ensure_demo_case_evidence(session, project, case_id)
        items[case_id]["available"] = True
    return {
        "fixture_layer": FIXTURE_LAYER,
        "data_mode": DataMode.HYBRID.value,
        "labels": ["DEMO", "SYNTHETIC", "CONTROLLED PROTOTYPE"],
        "official_mplads_evidence": False,
        "notice": FIXTURE_NOTICE,
        "cases": items,
    }


def assembled_plan_claim(session: Session, project: Project, data_mode: DataMode) -> tuple[dict[str, Any], dict[str, Any]]:
    from app.engines.pce.repository import list_claims
    from app.engines.pce.service import get_project_plan

    plan = get_project_plan(session, project, data_mode)
    claims = [
        row
        for row in list_claims(session, project.id)
        if data_mode != DataMode.REAL or str(row.data_mode or "").upper() in {"", "REAL"}
    ]
    claim_row = claims[0] if claims else None
    plan_payload = {
        "plan_recorded": bool(getattr(plan, "recorded", False)),
        "sanctioned_scope": getattr(plan, "sanctioned_scope", None),
        "budget_estimate": getattr(plan, "budget_estimate", None),
        "planned_start_date": str(plan.planned_start_date) if getattr(plan, "planned_start_date", None) else None,
        "planned_completion_date": (
            str(plan.planned_completion_date) if getattr(plan, "planned_completion_date", None) else None
        ),
        "milestone_label": getattr(plan, "milestone_label", None),
        "source": getattr(plan, "source", None),
        "data_mode": data_mode.value,
        "labels": ["DEMO", "SYNTHETIC", "CONTROLLED PROTOTYPE"] if data_mode != DataMode.REAL else [],
        "official_mplads_record": False if data_mode != DataMode.REAL else None,
    }
    claim_payload = {
        "claim_recorded": claim_row is not None,
        "claimed_progress": None if claim_row is None else claim_row.reported_progress,
        "claimed_progress_percent": None if claim_row is None else claim_row.claimed_progress_percent,
        "claimed_expenditure": None if claim_row is None else claim_row.amount_used,
        "claimed_completion_state": None if claim_row is None else claim_row.completion_statement,
        "data_mode": None if claim_row is None else claim_row.data_mode,
        "labels": ["DEMO", "SYNTHETIC", "CONTROLLED PROTOTYPE"] if data_mode != DataMode.REAL else [],
        "official_mplads_record": False if data_mode != DataMode.REAL else None,
    }
    return plan_payload, claim_payload


if __name__ == "__main__":
    from app.db import get_session_factory, init_db
    from app.main import create_app

    create_app()
    init_db()
    db = get_session_factory()()
    try:
        payload = ensure_all_demo_evidence(db)
        db.commit()
        print(payload)
    finally:
        db.close()
