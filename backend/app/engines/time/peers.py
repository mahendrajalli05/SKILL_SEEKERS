"""Constituency-first peer selection for Time Intelligence V1.

Same ladder as Cost Intelligence (D016):
1. Same geographic constituency + same category + similar work title
2. Same geographic constituency + broader category
3. Same Andhra Pradesh state + same category + similar work title
4. Same Andhra Pradesh state + broader comparable work title

Peers are never fabricated. MP name is never a geography key.
REAL peers require the same observed status and a recommendation date.
HYBRID_TEST peers require a usable schedule in the same date family.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from app.engines.cost.geography import classify_constituency
from app.engines.cost.work_type import work_type_similarity
from app.engines.time.constants import (
    ANDHRA_PRADESH_CANONICAL,
    MIN_PEER_COUNT,
    SCOPE_CONSTITUENCY_CATEGORY,
    SCOPE_CONSTITUENCY_CATEGORY_WORK_TYPE,
    SCOPE_LABELS,
    SCOPE_STATE_BROADER_WORK_TYPE,
    SCOPE_STATE_CATEGORY_WORK_TYPE,
)
from app.engines.cost.constants import PRECISE_WORK_TYPE_SIMILARITY
from app.engines.time.dates import duration_days
from app.engines.time.schedule import classify_family
from app.engines.time.types import (
    PeerScope,
    PeerSelection,
    ScheduleFamily,
    TimeMode,
    TimePeerRecord,
)
from app.pipeline.profile import is_andhra_pradesh_state


class TimePeerSource(Protocol):
    def by_constituency(
        self,
        constituency: str,
        state: str | None = None,
    ) -> Sequence[TimePeerRecord]:
        ...

    def by_state(self, state: str) -> Sequence[TimePeerRecord]:
        ...


def _has_text(value: str | None) -> bool:
    return bool((value or "").strip())


def is_andhra_pradesh(state: str | None) -> bool:
    if not _has_text(state):
        return False
    return is_andhra_pradesh_state(state)


def is_usable_time_peer(subject: TimePeerRecord, other: TimePeerRecord) -> bool:
    if other.project_id == subject.project_id:
        return False
    if other.time_mode != subject.time_mode:
        return False
    if subject.time_mode == TimeMode.REAL:
        if other.recommended_date is None:
            return False
        return (other.status or "") == (subject.status or "")
    subject_family = classify_family(subject)
    other_family = classify_family(other)
    if subject_family in {ScheduleFamily.INVALID, ScheduleFamily.NONE}:
        return False
    if other_family != subject_family:
        return False
    planned = duration_days(other.planned_start_date, other.planned_completion_date)
    if planned is None or planned <= 0:
        return False
    if other_family == ScheduleFamily.CLOSED:
        actual = duration_days(other.actual_start_date, other.actual_completion_date)
        return actual is not None and actual > 0
    return True


def filter_usable_peers(
    subject: TimePeerRecord,
    rows: Sequence[TimePeerRecord],
) -> list[TimePeerRecord]:
    usable = [row for row in rows if is_usable_time_peer(subject, row)]
    usable.sort(key=lambda item: item.project_id)
    return usable


def _matches_category(row: TimePeerRecord, subject: TimePeerRecord) -> bool:
    return _has_text(subject.category) and row.category == subject.category


def _precise_work_type(row: TimePeerRecord, subject: TimePeerRecord) -> bool:
    if not _has_text(subject.derived_work_type) or not _has_text(row.derived_work_type):
        return False
    return (
        work_type_similarity(subject.work_description, row.work_description)
        >= PRECISE_WORK_TYPE_SIMILARITY
    )


def _filter(
    rows: Sequence[TimePeerRecord],
    subject: TimePeerRecord,
    *,
    require_category: bool,
    require_precise_work_type: bool,
) -> list[TimePeerRecord]:
    selected: list[TimePeerRecord] = []
    for row in rows:
        if require_category and not _matches_category(row, subject):
            continue
        if require_precise_work_type and not _precise_work_type(row, subject):
            continue
        selected.append(row)
    return selected


def _scope(
    scope_id: str,
    subject: TimePeerRecord,
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
    peers: Sequence[TimePeerRecord],
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


class InMemoryTimePeerSource:
    def __init__(self, records: Sequence[TimePeerRecord]) -> None:
        self._records = list(records)

    def by_constituency(
        self,
        constituency: str,
        state: str | None = None,
    ) -> Sequence[TimePeerRecord]:
        key = (constituency or "").strip()
        if not key:
            return []
        rows = [row for row in self._records if row.constituency == key]
        state_key = (state or "").strip()
        if state_key:
            rows = [row for row in rows if row.state == state_key]
        return rows

    def by_state(self, state: str) -> Sequence[TimePeerRecord]:
        key = (state or "").strip()
        if not key:
            return []
        return [row for row in self._records if row.state == key]


def select_peers(
    subject: TimePeerRecord,
    source: TimePeerSource,
    *,
    min_peer_count: int = MIN_PEER_COUNT,
) -> PeerSelection:
    attempted: list[str] = []
    best_attempt_peer_count = 0
    classification = classify_constituency(subject.constituency)
    exclusion = None if classification.usable_as_geography else classification.reason

    def consider(scope_id: str, grouped: list[TimePeerRecord]) -> None:
        nonlocal best_attempt_peer_count
        attempted.append(scope_id)
        best_attempt_peer_count = max(best_attempt_peer_count, len(grouped))

    def finish(scope: PeerScope, grouped: list[TimePeerRecord]) -> PeerSelection:
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
