"""Risk Fusion V2 errors. Does not change frozen engines."""


class FusionV2Error(ValueError):
    """Invalid V2 fusion input (held-out labels, fraud claims, etc.)."""
