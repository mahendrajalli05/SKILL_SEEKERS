from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.demo.errors import DemoCaseError
from app.demo.service import assemble_case, case_id_from_path, list_cases
from app.domain.schemas.demo import DemoCaseListResponse, DemoCaseResponse
from app.errors import AppError

router = APIRouter()


@router.get("/demo-cases", response_model=DemoCaseListResponse)
def get_demo_cases(
    db: Session = Depends(get_db),
    data_mode: Literal["REAL", "HYBRID", "SYNTHETIC"] = Query(default="HYBRID"),
) -> DemoCaseListResponse:
    """List the four controlled prototype demonstration cases."""
    payload = list_cases(db, data_mode=data_mode)
    return DemoCaseListResponse.model_validate(payload)


@router.get("/demo-cases/{case_id}", response_model=DemoCaseResponse)
def get_demo_case(
    case_id: str,
    db: Session = Depends(get_db),
    data_mode: Literal["REAL", "HYBRID", "SYNTHETIC"] = Query(default="HYBRID"),
) -> DemoCaseResponse:
    """Assemble one controlled demonstration case from existing project data."""
    try:
        key = case_id_from_path(case_id)
        payload = assemble_case(db, key, data_mode=data_mode)
    except DemoCaseError as exc:
        raise AppError(exc.message, code=exc.code, status_code=exc.status_code) from exc
    return DemoCaseResponse.model_validate(payload)
