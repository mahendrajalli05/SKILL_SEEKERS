from __future__ import annotations

from datetime import date

import pytest

from app.ml.constants import FORBIDDEN_MODEL_INPUT_COLUMNS
from app.ml.features.cost import CostFeaturePipeline, rows_from_payload
from app.ml.features.forbidden import assert_no_label_leakage
from app.ml.features.schema import COST_FEATURE_SPECS
from app.ml.types import CostRow
from app.ml.training.split import temporal_split


def test_forbidden_columns_are_rejected() -> None:
    with pytest.raises(ValueError, match="scenario_type"):
        assert_no_label_leakage({"scenario_type": "COST_ANOMALY", "allocation_amount": 1})
    for name in (
        "demo_case_id",
        "mixed_signals",
        "anomaly_notes",
        "overlap_group_id",
        "coordinate_source",
    ):
        assert name in FORBIDDEN_MODEL_INPUT_COLUMNS


def test_feature_schema_has_sources_and_missing_behavior() -> None:
    names = {item.name for item in COST_FEATURE_SPECS}
    assert "log_allocation" in names
    assert "allocation_peer_percentile" in names
    assert all(item.source and item.missing_behavior for item in COST_FEATURE_SPECS)


def test_rows_from_payload_drops_labels() -> None:
    row = rows_from_payload(
        {
            "allocation_amount": 500000,
            "category": "Normal/Others",
            "state": "Andhra Pradesh",
            "constituency": "KURNOOL",
            "work_description": "Construction of water tanks",
            "recommendation_date": "2023-06-01",
        }
    )
    assert "scenario_type" not in row.__dict__
    assert row.recommended_date == date(2023, 6, 1)


def test_temporal_split_is_ordered_and_disjoint() -> None:
    rows = [
        CostRow(
            internal_project_id=f"id-{i}",
            allocation_amount=1000 + i,
            category="Normal/Others",
            state="Andhra Pradesh",
            constituency="KURNOOL",
            work_description="tanks",
            recommended_date=date(2023, 1, 1 + i),
            status="Unsanctioned",
            house="Lok Sabha",
        )
        for i in range(20)
    ]
    split = temporal_split(rows)
    assert set(split.train_ids).isdisjoint(split.validation_ids)
    assert set(split.train_ids).isdisjoint(split.test_ids)
    assert split.train_ids[0] == "id-0"
    assert split.test_ids[-1] == "id-19"
    assert "random" not in split.method


def test_pipeline_fit_transform_shapes() -> None:
    rows = [
        CostRow(
            internal_project_id=f"id-{i}",
            allocation_amount=200_000 + i * 1000,
            category="Normal/Others",
            state="Andhra Pradesh",
            constituency="KURNOOL",
            work_description="Construction of water tanks" if i % 2 == 0 else "Construction of roads",
            recommended_date=date(2023, 1, 1),
            status="Unsanctioned",
            house="Lok Sabha",
        )
        for i in range(20)
    ]
    pipeline = CostFeaturePipeline(tfidf_min_df=1, tfidf_max_features=32, svd_components=2)
    pipeline.fit(rows)
    matrix = pipeline.transform(rows)
    assert matrix.shape[0] == 20
    assert matrix.shape[1] == len(pipeline.feature_names_)
    avail = pipeline.availability(rows[0])
    assert "allocation_amount" in avail.available
