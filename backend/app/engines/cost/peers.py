"""Constituency-first peer selection for Cost Intelligence V1.1.

Priority:
1. Same *geographic* constituency + same category + similar work title
2. Same geographic constituency + broader category
3. Same Andhra Pradesh state + same category + similar work title
4. Same Andhra Pradesh state + broader comparable work title

Non-geographic constituency values (for example Sitting Rajya Sabha) are
skipped for constituency-level grouping. MP name is never a peer key.
Peers are never fabricated.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from app.engines.cost.constants import (
    ANDHRA_PRADESH_CANONICAL,
    MIN_PEER_COUNT,
    PRECISE_WORK_TYPE_SIMILARITY,
    SCOPE_CONSTITUENCY_CATEGORY,
    SCOPE_CONSTITUENCY_CATEGORY_WORK_TYPE,
    SCOPE_LABELS,
    SCOPE_STATE_BROADER_WORK_TYPE,
    SCOPE_STATE_CATEGORY_WORK_TYPE,
)
from app.engines.cost.geography import classify_constituency
from app.engines.cost.types import PeerRecord, PeerSelection, PeerScope
from app.engines.cost.work_type import work_type_similarity
from app.pipeline.profile import is_andhra_pradesh_state


class PeerSource(Protocol):
    """Reusable candidate provider. Implementations may be in-memory or SQL."""

    def by_constituency(
        self,
        constituency: str,
        state: str | None = None,
    ) -> Sequence[PeerRecord]:
        ...

    def by_state(self, state: str) -> Sequence[PeerRecord]:
        ...


def _has_text(value: str | None) -> bool:
    return bool((value or "").strip())


def is_usable_amount(amount: int | None) -> bool:
    return amount is not None and amount > 0


def is_andhra_pradesh(state: str | None) -> bool:
    if not _has_text(state):
        return False
    return is_andhra_pradesh_state(state)


def _same_synthetic_class(subject: PeerRecord, other: PeerRecord) -> bool:
    return bool(subject.is_synthetic) == bool(other.is_synthetic)


def filter_usable_peers(subject: PeerRecord, rows: Sequence[PeerRecord]) -> list[PeerRecord]:
    usable: list[PeerRecord] = []
    for row in rows:
        if row.project_id == subject.project_id:
            continue
        if not is_usable_amount(row.allocation_amount):
            continue
        if not _same_synthetic_class(subject, row):
            continue
        usable.append(row)
    usable.sort(key=lambda item: item.project_id)
    return usable


def _matches_category(row: PeerRecord, subject: PeerRecord) -> bool:
    return _has_text(subject.category) and row.category == subject.category


def _precise_work_type(row: PeerRecord, subject: PeerRecord) -> bool:
    if not _has_text(subject.derived_work_type) or not _has_text(row.derived_work_type):
        return False
    return (
        work_type_similarity(subject.work_description, row.work_description)
        >= PRECISE_WORK_TYPE_SIMILARITY
    )


def _filter(
    rows: Sequence[PeerRecord],
    subject: PeerRecord,
    *,
    require_category: bool,
    require_precise_work_type: bool,
) -> list[PeerRecord]:
    selected: list[PeerRecord] = []
    for row in rows:
        if require_category and not _matches_category(row, subject):
            continue
        if require_precise_work_type and not _precise_work_type(row, subject):
            continue
        selected.append(row)
    return selected


def _scope(
    scope_id: str,
    subject: PeerRecord,
    *,
    include_category: bool,
    precise_work_type: bool,
    geography: str,
) -> PeerScope:
    return PeerScope(
        id=scope_id,
        label=SCOPE_LABELS[scope_id],
        geography=geography,
        category=subject.category if include_category and _has_text(subject.category) else None,
        derived_work_type=(
            subject.derived_work_type
            if precise_work_type and _has_text(subject.derived_work_type)
            else None
        ),
        precise_work_type=precise_work_type,
    )


def _selection(
    scope: PeerScope,
    peers: Sequence[PeerRecord],
    attempted: list[str],
    *,
    best_attempt_peer_count: int,
    constituency_usable: bool,
    constituency_kind: str,
    constituency_exclusion_reason: str | None,
) -> PeerSelection:
    ordered = tuple(sorted(peers, key=lambda item: item.project_id))
    return PeerSelection(
        scope=scope,
        peers=ordered,
        attempted_scopes=tuple(attempted),
        best_attempt_peer_count=best_attempt_peer_count,
        constituency_usable=constituency_usable,
        constituency_kind=constituency_kind,
        constituency_exclusion_reason=constituency_exclusion_reason,
    )


class InMemoryPeerSource:
    """Deterministic in-memory peer source for tests and isolated selection."""

    def __init__(self, records: Sequence[PeerRecord]) -> None:
        self._records = list(records)

    def by_constituency(
        self,
        constituency: str,
        state: str | None = None,
    ) -> Sequence[PeerRecord]:
        key = (constituency or "").strip()
        if not key:
            return []
        rows = [row for row in self._records if row.constituency == key]
        state_key = (state or "").strip()
        if state_key:
            rows = [row for row in rows if row.state == state_key]
        return rows

    def by_state(self, state: str) -> Sequence[PeerRecord]:
        key = (state or "").strip()
        if not key:
            return []
        return [row for row in self._records if row.state == key]


def select_peers(
    subject: PeerRecord,
    source: PeerSource,
    *,
    min_peer_count: int = MIN_PEER_COUNT,
) -> PeerSelection:
    """Walk the geographic peer ladder. Returns the first sufficient group."""
    attempted: list[str] = []
    best_attempt_peer_count = 0
    classification = classify_constituency(subject.constituency)
    exclusion = (
        None if classification.usable_as_geography else classification.reason
    )

    def consider(scope_id: str, grouped: list[PeerRecord]) -> None:
        nonlocal best_attempt_peer_count
        attempted.append(scope_id)
        best_attempt_peer_count = max(best_attempt_peer_count, len(grouped))

    def finish(scope: PeerScope, grouped: list[PeerRecord]) -> PeerSelection:
        return _selection(
            scope,
            grouped,
            attempted,
            best_attempt_peer_count=len(grouped),
            constituency_usable=classification.usable_as_geography,
            constituency_kind=classification.kind.value,
            constituency_exclusion_reason=exclusion,
        )

    if classification.usable_as_geography:
        local = filter_usable_peers(
            subject,
            source.by_constituency(
                subject.constituency,
                subject.state if _has_text(subject.state) else None,
            ),
        )
        if _has_text(subject.category) and _has_text(subject.derived_work_type):
            grouped = _filter(
                local,
                subject,
                require_category=True,
                require_precise_work_type=True,
            )
            consider(SCOPE_CONSTITUENCY_CATEGORY_WORK_TYPE, grouped)
            if len(grouped) >= min_peer_count:
                return finish(
                    _scope(
                        SCOPE_CONSTITUENCY_CATEGORY_WORK_TYPE,
                        subject,
                        include_category=True,
                        precise_work_type=True,
                        geography=subject.constituency,
                    ),
                    grouped,
                )
        if _has_text(subject.category):
            grouped = _filter(
                local,
                subject,
                require_category=True,
                require_precise_work_type=False,
            )
            consider(SCOPE_CONSTITUENCY_CATEGORY, grouped)
            if len(grouped) >= min_peer_count:
                return finish(
                    _scope(
                        SCOPE_CONSTITUENCY_CATEGORY,
                        subject,
                        include_category=True,
                        precise_work_type=False,
                        geography=subject.constituency,
                    ),
                    grouped,
                )

    if is_andhra_pradesh(subject.state):
        statewide = filter_usable_peers(subject, source.by_state(subject.state))
        if _has_text(subject.category) and _has_text(subject.derived_work_type):
            grouped = _filter(
                statewide,
                subject,
                require_category=True,
                require_precise_work_type=True,
            )
            consider(SCOPE_STATE_CATEGORY_WORK_TYPE, grouped)
            if len(grouped) >= min_peer_count:
                return finish(
                    _scope(
                        SCOPE_STATE_CATEGORY_WORK_TYPE,
                        subject,
                        include_category=True,
                        precise_work_type=True,
                        geography=ANDHRA_PRADESH_CANONICAL,
                    ),
                    grouped,
                )
        if _has_text(subject.derived_work_type):
            grouped = _filter(
                statewide,
                subject,
                require_category=False,
                require_precise_work_type=True,
            )
            consider(SCOPE_STATE_BROADER_WORK_TYPE, grouped)
            if len(grouped) >= min_peer_count:
                return finish(
                    _scope(
                        SCOPE_STATE_BROADER_WORK_TYPE,
                        subject,
                        include_category=False,
                        precise_work_type=True,
                        geography=ANDHRA_PRADESH_CANONICAL,
                    ),
                    grouped,
                )

    return PeerSelection(
        scope=None,
        peers=(),
        attempted_scopes=tuple(attempted),
        best_attempt_peer_count=best_attempt_peer_count,
        constituency_usable=classification.usable_as_geography,
        constituency_kind=classification.kind.value,
        constituency_exclusion_reason=exclusion,
    )
