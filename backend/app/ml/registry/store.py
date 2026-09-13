"""Model registry metadata. Binary artifacts stay on disk; paths are not exposed to clients."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.ml.types import RegistryRecord

REGISTRY_FILENAME = "registry.json"
METADATA_FILENAME = "metadata.json"
ARTIFACT_FILENAME = "model.joblib"


def models_root(override: Path | None = None) -> Path:
    if override is not None:
        return override
    return get_settings().ml_models_path


def registry_path(root: Path | None = None) -> Path:
    return models_root(root) / REGISTRY_FILENAME


def model_dir(model_name: str, root: Path | None = None) -> Path:
    return models_root(root) / model_name


def artifact_path(model_name: str, root: Path | None = None) -> Path:
    return model_dir(model_name, root) / ARTIFACT_FILENAME


def metadata_path(model_name: str, root: Path | None = None) -> Path:
    return model_dir(model_name, root) / METADATA_FILENAME


def load_registry(root: Path | None = None) -> dict[str, Any]:
    path = registry_path(root)
    if not path.is_file():
        return {"models": [], "updated_at": None}
    return json.loads(path.read_text(encoding="utf-8"))


def load_record(model_name: str, root: Path | None = None) -> RegistryRecord | None:
    path = metadata_path(model_name, root)
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return RegistryRecord(**payload)


def save_record(record: RegistryRecord, root: Path | None = None) -> Path:
    directory = model_dir(record.model_name, root)
    directory.mkdir(parents=True, exist_ok=True)
    payload = {
        "model_name": record.model_name,
        "model_version": record.model_version,
        "model_type": record.model_type,
        "training_mode": record.training_mode,
        "training_data_hash": record.training_data_hash,
        "feature_schema_version": record.feature_schema_version,
        "created_at": record.created_at,
        "n_train": record.n_train,
        "n_validation": record.n_validation,
        "n_test": record.n_test,
        "split_method": record.split_method,
        "algorithm_params": record.algorithm_params,
        "validation_metrics": record.validation_metrics,
        "limitations": record.limitations,
        "artifact_filename": record.artifact_filename,
    }
    metadata_path(record.model_name, root).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    registry = load_registry(root)
    models = [item for item in registry.get("models", []) if item.get("model_name") != record.model_name]
    models.append(
        {
            "model_name": record.model_name,
            "model_version": record.model_version,
            "model_type": record.model_type,
            "training_mode": record.training_mode,
            "training_data_hash": record.training_data_hash,
            "feature_schema_version": record.feature_schema_version,
            "created_at": record.created_at,
        }
    )
    models.sort(key=lambda item: item["model_name"])
    registry_path(root).write_text(
        json.dumps(
            {
                "models": models,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return metadata_path(record.model_name, root)
