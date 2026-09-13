"""Dataclasses for ML Training & Inference V1."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any


class TrainingMode(str, Enum):
    REAL = "REAL"
    HYBRID_TEST = "HYBRID_TEST"


class PredictionStatus(str, Enum):
    SCORED = "SCORED"
    INCONCLUSIVE = "INCONCLUSIVE"
    NOT_AVAILABLE = "NOT_AVAILABLE"


class DataMode(str, Enum):
    REAL = "REAL"
    HYBRID = "HYBRID"
    SYNTHETIC = "SYNTHETIC"


@dataclass(frozen=True)
class FeatureSpec:
    name: str
    source: str
    data_type: str
    preprocessing: str
    missing_behavior: str
    required: bool = False


@dataclass
class NewProjectInput:
    state: str | None = None
    constituency: str | None = None
    category: str | None = None
    work_description: str | None = None
    allocation_amount: int | float | None = None
    recommendation_date: date | None = None
    status: str | None = None
    house: str | None = None
    planned_start_date: date | None = None
    planned_completion_date: date | None = None
    physical_progress_percent: int | None = None
    data_mode: DataMode = DataMode.REAL
    model_version: str | None = None


@dataclass
class FeatureAvailability:
    available: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    unseen: list[str] = field(default_factory=list)
    unsupported: list[str] = field(default_factory=list)
    coverage: float = 0.0


@dataclass
class FeatureContribution:
    feature: str
    value: Any
    contribution: float
    note: str


@dataclass
class ModelIdentity:
    model_name: str
    model_version: str
    model_type: str
    training_mode: str
    training_data_hash: str
    feature_schema_version: str
    created_at: str


@dataclass
class MlPrediction:
    model: ModelIdentity
    status: PredictionStatus
    ml_anomaly_score: int | None
    decision_label: str | None
    feature_availability: FeatureAvailability
    feature_values: dict[str, Any]
    contributions: list[FeatureContribution]
    explanation: str
    limitations: list[str]
    data_mode: str
    fraud_probability: None = None


@dataclass
class SplitAssignment:
    train_ids: tuple[str, ...]
    validation_ids: tuple[str, ...]
    test_ids: tuple[str, ...]
    method: str
    train_count: int
    validation_count: int
    test_count: int


@dataclass
class RegistryRecord:
    model_name: str
    model_version: str
    model_type: str
    training_mode: str
    training_data_hash: str
    feature_schema_version: str
    created_at: str
    n_train: int
    n_validation: int
    n_test: int
    split_method: str
    algorithm_params: dict[str, Any]
    validation_metrics: dict[str, Any]
    limitations: list[str]
    artifact_filename: str = "model.joblib"


@dataclass
class CostRow:
    internal_project_id: str
    allocation_amount: int | None
    category: str
    state: str
    constituency: str
    work_description: str
    recommended_date: date | None
    status: str
    house: str
    is_synthetic: bool = False
