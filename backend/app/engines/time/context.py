"""Legitimate-context hook for Time Intelligence V1.

Delay is a measured schedule finding, not a conclusion about cause.
Verified contextual explanations (weather, land, utility shifting, etc.)
are not present in the current extracts. This module is structured so those
codes can be attached later without changing scoring.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.engines.time.constants import CAUSE_NOT_ESTABLISHED
from app.engines.time.types import DelayContext

NO_DELAY_NOTE = "No delay was detected from available timing evidence."


def delay_context(
    *,
    delay_detected: bool,
    recorded_context_codes: Sequence[str] = (),
) -> DelayContext:
    codes = tuple(code.strip() for code in recorded_context_codes if str(code).strip())
    if not delay_detected:
        return DelayContext(
            delay_detected=False,
            cause_established=False,
            context_note=NO_DELAY_NOTE,
            recorded_context_codes=(),
        )
    if codes:
        joined = ", ".join(codes)
        return DelayContext(
            delay_detected=True,
            cause_established=True,
            context_note=(
                f"Delay detected. Recorded contextual codes: {joined}. "
                "These codes are supporting context only; an authorized officer decides."
            ),
            recorded_context_codes=codes,
        )
    return DelayContext(
        delay_detected=True,
        cause_established=False,
        context_note=CAUSE_NOT_ESTABLISHED,
        recorded_context_codes=(),
    )
