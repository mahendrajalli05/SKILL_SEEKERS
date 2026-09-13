"""Plan–Claim–Evidence V1.

Deterministic PLAN vs CLAIM vs EVIDENCE consistency. Not fused into
Investigation Priority. Frozen Cost/Time/Overlap/Compliance engines are unused.
"""

from app.engines.pce.constants import ENGINE_NAME, ENGINE_VERSION
from app.engines.pce.service import record_claim, record_evidence, record_plan, verify_project

__all__ = [
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "record_claim",
    "record_evidence",
    "record_plan",
    "verify_project",
]
