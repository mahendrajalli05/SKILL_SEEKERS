"""Feature schema documentation for ML V1."""

from __future__ import annotations

from app.ml.constants import FEATURE_SCHEMA_COST, FEATURE_SCHEMA_TIME
from app.ml.types import FeatureSpec

COST_FEATURE_SPECS: tuple[FeatureSpec, ...] = (
    FeatureSpec(
        name="log_allocation",
        source="project.allocation_amount",
        data_type="numeric",
        preprocessing="log1p of recorded allocation; missing → INCONCLUSIVE",
        missing_behavior="required; no imputation for scoring",
        required=True,
    ),
    FeatureSpec(
        name="allocation_peer_percentile",
        source="allocation_amount within train (state, category) group",
        data_type="numeric",
        preprocessing="empirical percentile in the frozen train peer group; fallback state then global",
        missing_behavior="0.5 when the group is empty",
        required=True,
    ),
    FeatureSpec(
        name="rec_year",
        source="project.recommended_date",
        data_type="temporal",
        preprocessing="calendar year of observed recommendation date",
        missing_behavior="train median year",
    ),
    FeatureSpec(
        name="rec_month",
        source="project.recommended_date",
        data_type="temporal",
        preprocessing="calendar month 1–12",
        missing_behavior="train median month",
    ),
    FeatureSpec(
        name="recommendation_age_days",
        source="project.recommended_date vs frozen train max date",
        data_type="temporal",
        preprocessing="days between recommendation and frozen train reference date",
        missing_behavior="train median age",
    ),
    FeatureSpec(
        name="desc_token_count",
        source="project.work_description",
        data_type="numeric",
        preprocessing="whitespace token count of observed title",
        missing_behavior="0",
    ),
    FeatureSpec(
        name="freq_state",
        source="project.state",
        data_type="categorical",
        preprocessing="train frequency encoding",
        missing_behavior="0 (unseen / blank)",
    ),
    FeatureSpec(
        name="freq_constituency",
        source="project.constituency",
        data_type="categorical",
        preprocessing="train frequency encoding",
        missing_behavior="0 (unseen / blank)",
    ),
    FeatureSpec(
        name="freq_category",
        source="project.category",
        data_type="categorical",
        preprocessing="train frequency encoding",
        missing_behavior="0 (unseen / blank); category itself is still required",
        required=True,
    ),
    FeatureSpec(
        name="freq_status",
        source="project.status",
        data_type="categorical",
        preprocessing="train frequency encoding",
        missing_behavior="0",
    ),
    FeatureSpec(
        name="freq_house",
        source="project.house",
        data_type="categorical",
        preprocessing="train frequency encoding",
        missing_behavior="0",
    ),
    FeatureSpec(
        name="text_svd_*",
        source="project.work_description",
        data_type="text",
        preprocessing="TF-IDF (train vocabulary only) + TruncatedSVD; compact work-type signal given ~99% Normal/Others",
        missing_behavior="zero vector",
    ),
)

TIME_FEATURE_SPECS: tuple[FeatureSpec, ...] = (
    FeatureSpec(
        name="planned_duration_days",
        source="HYBRID planned_start_date / planned_completion_date",
        data_type="numeric",
        preprocessing="positive planned span in days; HYBRID_TEST only",
        missing_behavior="row excluded from HYBRID_TEST training; REAL inference INCONCLUSIVE",
        required=True,
    ),
    FeatureSpec(
        name="physical_progress_percent",
        source="HYBRID physical_progress_percent",
        data_type="numeric",
        preprocessing="0–100 as recorded in the synthetic enrichment",
        missing_behavior="train median",
    ),
    FeatureSpec(
        name="log_allocation",
        source="real allocation copied onto the HYBRID row",
        data_type="numeric",
        preprocessing="log1p",
        missing_behavior="row excluded",
        required=True,
    ),
    FeatureSpec(
        name="rec_year",
        source="real recommended_date copied onto the HYBRID row",
        data_type="temporal",
        preprocessing="calendar year",
        missing_behavior="train median",
    ),
)


def cost_schema_version() -> str:
    return FEATURE_SCHEMA_COST


def time_schema_version() -> str:
    return FEATURE_SCHEMA_TIME


def spec_names(specs: tuple[FeatureSpec, ...]) -> tuple[str, ...]:
    return tuple(item.name for item in specs)
