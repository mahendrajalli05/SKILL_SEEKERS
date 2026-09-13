"""Overlap / Duplicate Intelligence V1.

Blocked multi-signal similarity. Produces Potential Overlap / Potential
Duplicate and Evidence Confidence. Does not assign Investigation Priority.
"""

from app.engines.overlap.constants import ENGINE_VERSION
from app.engines.overlap.service import assess_overlap, assess_project_overlap
from app.engines.overlap.types import OverlapMode

__all__ = [
    "ENGINE_VERSION",
    "OverlapMode",
    "assess_overlap",
    "assess_project_overlap",
]
