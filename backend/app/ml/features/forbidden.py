from app.engines.cost.constants import FORBIDDEN_MODEL_INPUT_COLUMNS
from app.ml.constants import FORBIDDEN_MODEL_INPUT_COLUMNS as ML_FORBIDDEN

__all__ = ["FORBIDDEN_MODEL_INPUT_COLUMNS", "ML_FORBIDDEN"]


def assert_no_label_leakage(payload: dict) -> None:
    """Raise if held-out synthetic scenario columns are offered as features."""
    present = sorted(key for key in payload if key in ML_FORBIDDEN)
    if present:
        raise ValueError(
            "Held-out synthetic label columns cannot be used as model features: "
            + ", ".join(present)
        )
