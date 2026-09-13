"""Lifecycle orchestration errors. Does not change frozen engines."""


class LifecycleError(ValueError):
    """Invalid lifecycle orchestration input or officer planning action."""

    def __init__(self, message: str, *, code: str = "lifecycle_error", status_code: int = 422) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
