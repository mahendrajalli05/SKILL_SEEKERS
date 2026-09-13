from __future__ import annotations

from datetime import date

from app.domain.enums import DataMode, LifecycleStage
from app.engines.need.types import NeedImpactInputs, SyntheticNeedImpactEnrichment
from app.models.project import Project

SYNTHETIC_LABEL = "TEST/SYNTHETIC: need-impact unit test (not a government project)"


def insert_project(session, **overrides: object) -> Project:
    values: dict[str, object] = {
        "internal_project_id": "internal:need-impact:subject",
        "internal_id_kind": "internal_surrogate_hash",
        "internal_id_scheme": "sarvsakshi_internal_work_v1",
        "source_dataset": "github_vonter_india-mplads-works_MPLADS.csv",
        "is_synthetic": False,
        "lifecycle_stage": LifecycleStage.FUTURE.value,
        "state": "Andhra Pradesh",
        "constituency": "VIZIANAGARAM",
        "category": "Drinking Water",
        "work_description": "NA - Construction of drinking water facility",
        "allocation_amount": 2_000_000,
        "recommended_date": date(2023, 6, 1),
        "status": "Unsanctioned",
        "mp_name": "Example MP",
        "ida": "District Collector_IDA",
    }
    values.update(overrides)
    row = Project(**values)
    session.add(row)
    session.flush()
    return row


def high_need_enrichment(internal_project_id: str) -> SyntheticNeedImpactEnrichment:
    return SyntheticNeedImpactEnrichment(
        internal_project_id=internal_project_id,
        label="TEST/SYNTHETIC",
        population_need_index=92,
        infrastructure_gap_index=88,
        underserved_index=90,
        beneficiary_count=12_000,
        community_coverage_index=85,
        disaster_flag=True,
        urgency_index=80,
    )


def low_need_enrichment(internal_project_id: str) -> SyntheticNeedImpactEnrichment:
    return SyntheticNeedImpactEnrichment(
        internal_project_id=internal_project_id,
        label="TEST/SYNTHETIC",
        population_need_index=12,
        infrastructure_gap_index=10,
        underserved_index=8,
        beneficiary_count=0,
        community_coverage_index=10,
        disaster_flag=False,
        urgency_index=15,
    )


def sample_inputs(**overrides: object) -> NeedImpactInputs:
    values: dict[str, object] = {
        "project_id": 1,
        "internal_project_id": "internal:need-impact:subject",
        "state": "Andhra Pradesh",
        "constituency": "VIZIANAGARAM",
        "constituency_usable": True,
        "category": "Drinking Water",
        "work_description": "Construction of drinking water facility",
        "allocation_amount": 2_000_000,
        "status": "Unsanctioned",
        "recommended_date": date(2023, 6, 1),
        "lifecycle_stage": LifecycleStage.FUTURE.value,
        "mp_name": "Example MP",
        "ida": "District Collector_IDA",
        "data_mode": DataMode.REAL,
    }
    values.update(overrides)
    return NeedImpactInputs(**values)
