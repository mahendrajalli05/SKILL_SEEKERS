"""Time Intelligence V1 — schedule/delay signals with explicit evidence limits.

REAL mode uses recommendation date + status only and does not fabricate duration.
HYBRID_TEST uses synthetic dates/progress for controlled testing only.
Produces Time Anomaly and Evidence Confidence. Does not assign Investigation Priority.
"""

from app.engines.time.constants import ENGINE_VERSION, MIN_PEER_COUNT
from app.engines.time.service import assess_project_time, assess_time
from app.engines.time.types import TimeMode

__all__ = [
    "ENGINE_VERSION",
    "MIN_PEER_COUNT",
    "TimeMode",
    "assess_time",
    "assess_project_time",
]
