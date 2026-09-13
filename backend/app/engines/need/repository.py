"""Load observed project fields and constituency context.

Does not invent district, population, or beneficiary values.
MP name is never used as geographic scope.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.enums import DataMode, LifecycleStage
from app.engines.cost.geography import classify_constituency
from app.engines.need.constants import CONTEXT_NOT_NEED_NOTE, MP_NOT_GEOGRAPHY_NOTE
from app.engines.need.types import ConstituencyContext, NeedImpactInputs, SyntheticNeedImpactEnrichment
from app.models.project import Project
from app.models.snapshot import DatasetSnapshot


def _text(value: object) -> str:
    return str(value or "").strip()


def project_to_inputs(
    project: Project,
    data_mode: DataMode,
    *,
    enrichment: SyntheticNeedImpactEnrichment | None = None,
) -> NeedImpactInputs:
    classification = classify_constituency(project.constituency)
    return NeedImpactInputs(
        project_id=int(project.id),
        internal_project_id=project.internal_project_id,
        state=_text(project.state),
        constituency=_text(project.constituency),
        constituency_usable=classification.usable_as_geography,
        category=_text(project.category),
        work_description=_text(project.work_description),
        allocation_amount=project.allocation_amount,
        status=_text(project.status),
        recommended_date=project.recommended_date,
        lifecycle_stage=_text(project.lifecycle_stage) or LifecycleStage.UNKNOWN.value,
        mp_name=_text(project.mp_name),
        ida=_text(project.ida),
        data_mode=data_mode,
        village=_text(project.village),
        block=_text(project.block),
        city=_text(project.city),
        enrichment=None if data_mode == DataMode.REAL else enrichment,
    )


def constituency_context_for(session: Session, project: Project) -> ConstituencyContext:
    classification = classify_constituency(project.constituency)
    if not classification.usable_as_geography:
        return ConstituencyContext(
            constituency=_text(project.constituency),
            usable_as_geography=False,
            constituency_work_count=None,
            category_work_count=None,
            locality_work_count=None,
            locality_field=None,
            reason=f"{classification.reason} {MP_NOT_GEOGRAPHY_NOTE}",
            used_as_need_score=False,
        )
    constituency = _text(project.constituency)
    total = session.scalar(
        select(func.count()).select_from(Project).where(Project.constituency == constituency)
    )
    category_count = None
    category = _text(project.category)
    if category:
        category_count = session.scalar(
            select(func.count())
            .select_from(Project)
            .where(Project.constituency == constituency, Project.category == category)
        )
    locality_field = None
    locality_value = ""
    for field_name in ("village", "block", "city"):
        value = _text(getattr(project, field_name, None))
        if value:
            locality_field = field_name
            locality_value = value
            break
    locality_count = None
    if locality_field and locality_value:
        locality_count = session.scalar(
            select(func.count())
            .select_from(Project)
            .where(
                Project.constituency == constituency,
                getattr(Project, locality_field) == locality_value,
            )
        )
    return ConstituencyContext(
        constituency=constituency,
        usable_as_geography=True,
        constituency_work_count=int(total or 0),
        category_work_count=None if category_count is None else int(category_count),
        locality_work_count=None if locality_count is None else int(locality_count),
        locality_field=locality_field,
        reason=(
            f"Constituency '{constituency}' is the geographic context. "
            f"{CONTEXT_NOT_NEED_NOTE}"
        ),
        used_as_need_score=False,
    )


def snapshot_for(session: Session, project: Project) -> DatasetSnapshot | None:
    return session.get(DatasetSnapshot, project.snapshot_id) if project.snapshot_id else project.snapshot
