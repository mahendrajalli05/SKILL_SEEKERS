"""Milestone Advisor V1.

Decision-support for milestone readiness. Does not release funds.
Does not change Cost, Time, Overlap, Compliance, or Risk Fusion.
"""

from app.engines.milestone.constants import ENGINE_NAME, ENGINE_VERSION

__all__ = ["ENGINE_NAME", "ENGINE_VERSION"]
