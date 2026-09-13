"""ML layer errors. Do not silently fall back to another model version."""

from __future__ import annotations

from app.errors import AppError


class MlError(AppError):
    """Typed ML failure."""


class ModelMissingError(MlError):
    def __init__(self, model_name: str) -> None:
        super().__init__(
            f"Model '{model_name}' is not available. Training is an explicit backend action.",
            code="model_missing",
            status_code=503,
        )


class ModelVersionMismatchError(MlError):
    def __init__(self, requested: str, loaded: str) -> None:
        super().__init__(
            f"Requested model version '{requested}' does not match the loaded version '{loaded}'. "
            "No silent fallback was applied.",
            code="model_version_mismatch",
            status_code=409,
        )


class CorruptedModelError(MlError):
    def __init__(self, model_name: str) -> None:
        super().__init__(
            f"Model artifact '{model_name}' could not be loaded.",
            code="corrupted_model_artifact",
            status_code=503,
        )


class InsufficientFeatureCoverageError(MlError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="insufficient_feature_coverage", status_code=422)


class MalformedMlInferenceError(MlError):
    def __init__(self, message: str = "ML inference output was malformed.") -> None:
        super().__init__(message, code="malformed_ml_inference", status_code=422)


class UnsupportedDataModeError(MlError):
    def __init__(self, data_mode: str) -> None:
        super().__init__(
            f"Data mode '{data_mode}' is not supported for ML evidence.",
            code="unsupported_data_mode",
            status_code=422,
        )
