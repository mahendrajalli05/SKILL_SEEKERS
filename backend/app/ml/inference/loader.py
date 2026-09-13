"""Load model artifacts. Never accepts client uploads. No silent version fallback."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib

from app.ml.constants import COST_MODEL_NAME, TIME_MODEL_NAME
from app.ml.errors import CorruptedModelError, ModelMissingError, ModelVersionMismatchError
from app.ml.registry.store import artifact_path, load_record
from app.ml.types import RegistryRecord

_CACHE: dict[str, dict[str, Any]] = {}


def reset_model_cache() -> None:
    _CACHE.clear()


def load_bundle(model_name: str, *, root: Path | None = None) -> dict[str, Any]:
    cache_key = f"{model_name}:{root}"
    cached = _CACHE.get(cache_key)
    if cached is not None:
        return cached
    path = artifact_path(model_name, root)
    if not path.is_file():
        raise ModelMissingError(model_name)
    try:
        bundle = joblib.load(path)
    except Exception as exc:  # noqa: BLE001 — artifact may be truncated
        raise CorruptedModelError(model_name) from exc
    if not isinstance(bundle, dict) or "model" not in bundle or "record" not in bundle:
        raise CorruptedModelError(model_name)
    record = bundle["record"]
    if not isinstance(record, RegistryRecord):
        raise CorruptedModelError(model_name)
    disk = load_record(model_name, root)
    if disk is not None and disk.model_version != record.model_version:
        raise CorruptedModelError(model_name)
    _CACHE[cache_key] = bundle
    return bundle


def require_version(bundle: dict[str, Any], requested: str | None) -> RegistryRecord:
    record: RegistryRecord = bundle["record"]
    if requested and requested != record.model_version:
        raise ModelVersionMismatchError(requested, record.model_version)
    return record


def cost_bundle(root: Path | None = None) -> dict[str, Any]:
    return load_bundle(COST_MODEL_NAME, root=root)


def time_bundle(root: Path | None = None) -> dict[str, Any]:
    return load_bundle(TIME_MODEL_NAME, root=root)
