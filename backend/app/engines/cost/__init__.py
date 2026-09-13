"""Cost Intelligence V1.1 — allocation-vs-peers Cost Anomaly.

Geographic constituency validation, deterministic work-title similarity,
peer quality, and log-robust scoring. Produces Allocation Cost Anomaly and
Evidence Confidence only. Does not assign fused Investigation Priority.
"""

from app.engines.cost.constants import ENGINE_VERSION, MIN_PEER_COUNT
from app.engines.cost.service import assess_cost, assess_project_cost
from app.engines.cost.work_type import derive_work_type, work_type_representation

__all__ = [
    "ENGINE_VERSION",
    "MIN_PEER_COUNT",
    "assess_cost",
    "assess_project_cost",
    "derive_work_type",
    "work_type_representation",
]
