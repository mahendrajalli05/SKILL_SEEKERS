"""Risk Fusion V2.

Consumes standardized Evidence Objects from frozen V1/V1.1 engines.
Produces Investigation Priority and Evidence Confidence. Does not
determine fraud, sanction a project, or release funds.
"""

from app.engines.fusion_v2.fuse import fuse_evidence_v2
from app.engines.fusion_v2.service import assess_project_risk_v2

__all__ = ["assess_project_risk_v2", "fuse_evidence_v2"]
