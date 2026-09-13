"""Build a compliance context from observed project fields plus optional HYBRID inputs."""

from __future__ import annotations

from app.engines.compliance.constants import REAL_OBSERVATION_DATE
from app.engines.compliance.enrichment import HybridComplianceFields, assert_no_label_fields
from app.engines.compliance.types import ComplianceContext, ComplianceMode
from app.models.project import Project


def context_from_project(
    row: Project,
    *,
    mode: ComplianceMode = ComplianceMode.REAL,
    hybrid: HybridComplianceFields | None = None,
) -> ComplianceContext:
    """REAL fields only, unless HYBRID_TEST supplies synthetic execution fields."""
    context = ComplianceContext(
        project_id=row.id,
        internal_project_id=row.internal_project_id,
        mode=mode,
        mp_name=(row.mp_name or "").strip(),
        work_description=(row.work_description or "").strip(),
        category=(row.category or "").strip(),
        state=(row.state or "").strip(),
        constituency=(row.constituency or "").strip(),
        ida=(row.ida or "").strip(),
        city=(row.city or "").strip(),
        ward=(row.ward or "").strip(),
        block=(row.block or "").strip(),
        village=(row.village or "").strip(),
        recommended_date=row.recommended_date,
        allocation_amount=row.allocation_amount,
        ida_approval=(row.ida_approval or "").strip(),
        status=(row.status or "").strip(),
        house=(row.house or "").strip(),
        lifecycle_stage=(row.lifecycle_stage or "").strip(),
        observation_date=REAL_OBSERVATION_DATE,
        as_of_date=None,
        sanction_date=None,
        planned_start_date=None,
        planned_completion_date=None,
        actual_start_date=None,
        actual_completion_date=None,
        sanctioned_amount=None,
        expenditure_amount=None,
        physical_progress_percent=None,
        first_payment_date=None,
        amount_unit=None,
        verified_work_district=None,
        vendor_name=None,
        latitude=None,
        longitude=None,
    )
    if mode == ComplianceMode.HYBRID_TEST and hybrid is not None:
        context = ComplianceContext(
            project_id=context.project_id,
            internal_project_id=context.internal_project_id,
            mode=mode,
            mp_name=context.mp_name,
            work_description=context.work_description,
            category=context.category,
            state=context.state,
            constituency=context.constituency,
            ida=context.ida,
            city=context.city,
            ward=context.ward,
            block=context.block,
            village=context.village,
            recommended_date=context.recommended_date,
            allocation_amount=context.allocation_amount,
            ida_approval=context.ida_approval,
            status=context.status,
            house=context.house,
            lifecycle_stage=context.lifecycle_stage,
            observation_date=context.observation_date,
            as_of_date=hybrid.as_of_date,
            sanction_date=hybrid.sanction_date,
            planned_start_date=hybrid.planned_start_date,
            planned_completion_date=hybrid.planned_completion_date,
            actual_start_date=hybrid.actual_start_date,
            actual_completion_date=hybrid.actual_completion_date,
            sanctioned_amount=hybrid.sanctioned_amount,
            expenditure_amount=hybrid.expenditure_amount,
            physical_progress_percent=hybrid.physical_progress_percent,
            first_payment_date=None,
            amount_unit=None,
            verified_work_district=None,
            vendor_name=None,
            latitude=None,
            longitude=None,
        )
    assert_no_label_fields(context)
    return context
