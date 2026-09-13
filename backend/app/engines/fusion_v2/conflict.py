"""Contradictory evidence detection for Risk Fusion V2.

Does not force a single conclusion. Returns CONFLICTING_EVIDENCE pairs.
"""

from __future__ import annotations

from app.engines.fusion_v2.constants import CONFLICT_PAIRS, GROUP_DISPLAY_NAMES
from app.engines.fusion_v2.types import (
    ConflictRecord,
    GroupContribution,
    V2EvidenceState,
    V2SignalPolarity,
)


def _usable(item: GroupContribution) -> bool:
    return item.state in {V2EvidenceState.ASSESSABLE, V2EvidenceState.LOW_CONFIDENCE}


def detect_conflicts(groups: list[GroupContribution]) -> list[ConflictRecord]:
    lookup = {item.group_id: item for item in groups}
    records: list[ConflictRecord] = []
    for left_id, right_id in CONFLICT_PAIRS:
        left = lookup.get(left_id)
        right = lookup.get(right_id)
        if left is None or right is None:
            continue
        if not _usable(left) or not _usable(right):
            continue
        if left.polarity == V2SignalPolarity.UNKNOWN or right.polarity == V2SignalPolarity.UNKNOWN:
            continue
        if left.polarity == right.polarity:
            continue
        records.append(
            ConflictRecord(
                left_group=left.display_name,
                right_group=right.display_name,
                left_polarity=left.polarity.value,
                right_polarity=right.polarity.value,
                summary=(
                    f"{GROUP_DISPLAY_NAMES[left_id]} indicates {left.polarity.value.lower()} "
                    f"while {GROUP_DISPLAY_NAMES[right_id]} indicates "
                    f"{right.polarity.value.lower()}. Evidence disagrees; no single "
                    "conclusion is forced."
                ),
            )
        )
    return records
