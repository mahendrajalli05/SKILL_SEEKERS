"""Candidate-pair generation for Overlap Intelligence V1.

Blocks by geographic constituency, observed category, rare work-type tokens,
recommendation-date windows, and GPS cells when coordinates exist.
Does not compare every record to every other record.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from datetime import date

from app.engines.overlap.constants import (
    DATE_CANDIDATE_WINDOW_DAYS,
    GEO_CELL_DEGREES,
    MAX_CANDIDATES_PER_SUBJECT,
    MAX_FULL_BLOCK_SIZE,
)
from app.engines.overlap.types import OverlapRecord


def geo_cell(lat: float, lon: float) -> tuple[int, int]:
    return (int(round(lat / GEO_CELL_DEGREES)), int(round(lon / GEO_CELL_DEGREES)))


def neighboring_cells(lat: float, lon: float) -> list[tuple[int, int]]:
    centre = geo_cell(lat, lon)
    return [(centre[0] + dx, centre[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]


def _date_ok(left: OverlapRecord, right: OverlapRecord) -> bool:
    if left.recommended_date is None or right.recommended_date is None:
        return True
    gap = abs((left.recommended_date - right.recommended_date).days)
    return gap <= DATE_CANDIDATE_WINDOW_DAYS


def _const_cat_key(record: OverlapRecord) -> tuple[str, str] | None:
    if not record.constituency_usable or not record.constituency.strip():
        return None
    return (record.constituency.strip().casefold(), record.category.strip().casefold())


class OverlapIndex:
    """Inverted indexes for blocked candidate generation."""

    def __init__(self, records: Sequence[OverlapRecord]) -> None:
        self.records = tuple(records)
        self.by_id: dict[int, OverlapRecord] = {}
        self.by_const_cat: dict[tuple[str, str], list[OverlapRecord]] = defaultdict(list)
        self.by_token: dict[str, list[OverlapRecord]] = defaultdict(list)
        self.by_title: dict[str, list[OverlapRecord]] = defaultdict(list)
        self.by_geo: dict[tuple[int, int], list[OverlapRecord]] = defaultdict(list)
        for record in self.records:
            self.by_id[record.project_id] = record
            key = _const_cat_key(record)
            if key is not None:
                self.by_const_cat[key].append(record)
            title = record.embedding_text
            if title:
                self.by_title[title].append(record)
            if record.rare_tokens:
                for token in record.rare_tokens:
                    self.by_token[token].append(record)
            elif title:
                self.by_title.setdefault(f"weak:{title}", []).append(record)
            if record.latitude is not None and record.longitude is not None:
                self.by_geo[geo_cell(record.latitude, record.longitude)].append(record)

    def _add(
        self,
        found: dict[int, OverlapRecord],
        subject: OverlapRecord,
        other: OverlapRecord,
    ) -> None:
        if other.project_id == subject.project_id:
            return
        if not _date_ok(subject, other):
            return
        found[other.project_id] = other

    def candidates_for(self, subject: OverlapRecord) -> list[OverlapRecord]:
        found: dict[int, OverlapRecord] = {}
        key = _const_cat_key(subject)
        if key is not None:
            members = self.by_const_cat.get(key, [])
            if len(members) <= MAX_FULL_BLOCK_SIZE:
                for other in members:
                    self._add(found, subject, other)
            else:
                rare = subject.rare_tokens
                title = subject.embedding_text
                for other in members:
                    if rare and (rare & other.rare_tokens):
                        self._add(found, subject, other)
                    elif title and other.embedding_text == title:
                        self._add(found, subject, other)

        if subject.embedding_text:
            for other in self.by_title.get(subject.embedding_text, []):
                same_geo = (
                    subject.constituency_usable
                    and other.constituency_usable
                    and subject.constituency.strip().casefold()
                    == other.constituency.strip().casefold()
                )
                if same_geo:
                    self._add(found, subject, other)

        if not subject.constituency_usable:
            rare = subject.rare_tokens
            subject_cat = subject.category.strip().casefold()
            for token in rare:
                for other in self.by_token.get(token, []):
                    if other.category.strip().casefold() != subject_cat:
                        continue
                    if rare & other.rare_tokens:
                        self._add(found, subject, other)

        if subject.latitude is not None and subject.longitude is not None:
            for cell in neighboring_cells(subject.latitude, subject.longitude):
                for other in self.by_geo.get(cell, []):
                    self._add(found, subject, other)

        ranked = sorted(found.values(), key=lambda item: item.project_id)
        if len(ranked) <= MAX_CANDIDATES_PER_SUBJECT:
            return ranked
        rare = subject.rare_tokens
        title = subject.embedding_text

        def strength(other: OverlapRecord) -> tuple[int, int, int]:
            exact = 1 if title and other.embedding_text == title else 0
            shared = len(rare & other.rare_tokens) if rare else 0
            return (exact, shared, -other.project_id)

        ranked.sort(key=strength, reverse=True)
        return sorted(ranked[:MAX_CANDIDATES_PER_SUBJECT], key=lambda item: item.project_id)


def generate_candidate_pairs(records: Sequence[OverlapRecord]) -> list[tuple[OverlapRecord, OverlapRecord]]:
    """Undirected pairs with canonical id order. Used in tests and batch scans."""
    index = OverlapIndex(records)
    seen: set[tuple[int, int]] = set()
    pairs: list[tuple[OverlapRecord, OverlapRecord]] = []
    for record in sorted(records, key=lambda item: item.project_id):
        for other in index.candidates_for(record):
            a, b = (record, other) if record.project_id < other.project_id else (other, record)
            key = (a.project_id, b.project_id)
            if key in seen:
                continue
            seen.add(key)
            pairs.append((a, b))
    return pairs


def blocking_strategy_label(*, gps_used: bool, constituency_usable: bool) -> str:
    parts = [
        "geographic constituency + category" if constituency_usable else "non-geographic constituency skipped",
        "rare work-type tokens",
        f"recommendation-date window {DATE_CANDIDATE_WINDOW_DAYS} days",
    ]
    if gps_used:
        parts.append("HYBRID GPS cells")
    return "; ".join(parts)


def date_window_ok(left: date | None, right: date | None) -> bool:
    if left is None or right is None:
        return True
    return abs((left - right).days) <= DATE_CANDIDATE_WINDOW_DAYS


def count_all_pairs(n: int) -> int:
    return n * (n - 1) // 2 if n > 1 else 0


def iter_block_sizes(index: OverlapIndex) -> Iterable[int]:
    for members in index.by_const_cat.values():
        yield len(members)
