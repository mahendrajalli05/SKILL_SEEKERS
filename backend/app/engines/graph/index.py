"""Indexes and candidate generation for Relationship Graph V1.

Entity links are derived from observed fields. SIMILAR_TO candidates
are taken from Overlap Intelligence blocking, not all-pairs.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from app.engines.cost.work_type import normalize_observed_text
from app.engines.graph.constants import MAX_CLUSTER_PEERS
from app.engines.graph.types import GraphRecord


def _fold(value: str | None) -> str:
    return normalize_observed_text(value).casefold()


def cluster_key(record: GraphRecord) -> tuple[str, str, str] | None:
    """Constituency + category + IDA when at least geography or IDA exists.

    Same-category-only groups are not used: Normal/Others would explode.
    Non-geographic constituency is excluded from the key.
    """
    const = _fold(record.constituency) if record.constituency_usable else ""
    cat = _fold(record.category)
    ida = _fold(record.ida)
    if not const and not ida:
        return None
    return (const, cat, ida)


class GraphIndex:
    """Inverted indexes for ego-neighborhood construction and degree queries."""

    def __init__(self, records: Sequence[GraphRecord]) -> None:
        self.records = tuple(sorted(records, key=lambda item: item.project_id))
        self.by_id: dict[int, GraphRecord] = {}
        self.by_mp: dict[str, list[GraphRecord]] = defaultdict(list)
        self.by_constituency: dict[str, list[GraphRecord]] = defaultdict(list)
        self.by_category: dict[str, list[GraphRecord]] = defaultdict(list)
        self.by_ida: dict[str, list[GraphRecord]] = defaultdict(list)
        self.by_state: dict[str, list[GraphRecord]] = defaultdict(list)
        self.by_cluster: dict[tuple[str, str, str], list[GraphRecord]] = defaultdict(list)
        for record in self.records:
            self.by_id[record.project_id] = record
            mp = _fold(record.mp_name)
            if mp:
                self.by_mp[mp].append(record)
            if record.constituency_usable:
                const = _fold(record.constituency)
                if const:
                    self.by_constituency[const].append(record)
            cat = _fold(record.category)
            if cat:
                self.by_category[cat].append(record)
            ida = _fold(record.ida)
            if ida:
                self.by_ida[ida].append(record)
            state = _fold(record.state)
            if state:
                self.by_state[state].append(record)
            key = cluster_key(record)
            if key is not None:
                self.by_cluster[key].append(record)

    def cluster_peers(self, subject: GraphRecord) -> list[GraphRecord]:
        key = cluster_key(subject)
        if key is None:
            return []
        members = [
            item
            for item in self.by_cluster.get(key, [])
            if item.project_id != subject.project_id
        ]
        members.sort(key=lambda item: item.project_id)
        return members[:MAX_CLUSTER_PEERS]

    def cluster_size(self, subject: GraphRecord) -> int:
        key = cluster_key(subject)
        if key is None:
            return 1
        return len(self.by_cluster.get(key, []))

    def ida_count(self, subject: GraphRecord) -> int:
        key = _fold(subject.ida)
        if not key:
            return 0
        return len(self.by_ida.get(key, []))

    def constituency_count(self, subject: GraphRecord) -> int:
        if not subject.constituency_usable:
            return 0
        key = _fold(subject.constituency)
        if not key:
            return 0
        return len(self.by_constituency.get(key, []))


def candidate_strategy_label(*, constituency_usable: bool, gps_used: bool) -> str:
    parts = [
        "entity edges from observed MP / constituency / category / IDA / state",
        "cluster filter: same geographic constituency + category + IDA"
        if constituency_usable
        else "cluster filter: same IDA + category (constituency not geographic)",
        "SIMILAR_TO from Overlap Intelligence blocked candidates (not all-pairs)",
    ]
    if gps_used:
        parts.append("HYBRID GPS used only inside Overlap SIMILAR_TO scoring")
    return "; ".join(parts)
