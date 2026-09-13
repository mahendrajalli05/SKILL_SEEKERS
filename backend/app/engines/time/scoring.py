"""Time Anomaly score (0–100) and Evidence Confidence.

Score is produced only when sufficient timing evidence exists.
REAL mode does not invent duration and does not produce a Time Anomaly score.

HYBRID_TEST:
- Closed: delay versus own plan, blended with peer actual duration when available.
- Open: time-consumed vs physical progress, and overdue versus planned completion.

Only late / behind-schedule direction contributes. Early or on-track maps to 0.
This is not a fused Investigation Priority.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.engines.cost.stats import compute_peer_statistics, median, median_absolute_deviation
from app.engines.time.constants import (
    FLAG_SCORE_THRESHOLD,
    HYBRID_CONFIDENCE_CAP,
    MIN_PEER_COUNT,
    MISMATCH_POINTS_FOR_MAX,
    MODIFIED_Z_REFERENCE,
    PLAN_DELAY_RATIO_FOR_MAX,
    REAL_CONFIDENCE_CAP,
    SCOPE_CONFIDENCE_BASE,
)
from app.engines.time.dates import duration_days
from app.engines.time.schedule import compute_schedule_metrics
from app.engines.time.types import (
    ScheduleFamily,
    ScheduleMetrics,
    TimeMode,
    TimePeerRecord,
)

_Z_CONSTANT = 0.6745


def _clip_score(value: float) -> int:
    return int(round(min(100.0, max(0.0, value))))


def completed_plan_score(delay_days: int, planned_duration_days: int) -> int:
    """Map non-negative delay vs planned duration. 100% overtime → 100."""
    if planned_duration_days <= 0:
        raise ValueError("planned_duration_days must be positive.")
    if delay_days <= 0:
        return 0
    return _clip_score(100.0 * delay_days / (PLAN_DELAY_RATIO_FOR_MAX * planned_duration_days))


def ongoing_mismatch_score(time_consumed_percent: float, progress: float) -> int:
    """Map (time consumed − physical progress) percentage points to 0–100."""
    mismatch = time_consumed_percent - progress
    if mismatch <= 0:
        return 0
    return _clip_score(100.0 * mismatch / MISMATCH_POINTS_FOR_MAX)


def overdue_score(overdue_days: int, planned_duration_days: int, *, progress: float) -> int:
    if planned_duration_days <= 0:
        raise ValueError("planned_duration_days must be positive.")
    if progress >= 100:
        return 0
    if overdue_days <= 0:
        return 0
    return _clip_score(100.0 * overdue_days / planned_duration_days)


def is_time_anomaly(score: int) -> bool:
    return score >= FLAG_SCORE_THRESHOLD


def _late_only_peer_score(
    actual: float,
    values: Sequence[float],
    *,
    require_positive: bool = True,
) -> tuple[int, str, float | None]:
    """Peer duration/mismatch score in the late direction only."""
    if require_positive:
        stats = compute_peer_statistics(values)
        centre = stats.median
        mad = stats.mad
    else:
        centre = median(values)
        mad = median_absolute_deviation(values, centre)
    if actual <= centre:
        return 0, "peer_at_or_below_median", 0.0
    if mad > 0:
        z = _Z_CONSTANT * (actual - centre) / mad
        return _clip_score(100.0 * max(0.0, z) / MODIFIED_Z_REFERENCE), "peer_modified_z", z
    if centre <= 0:
        return 0, "peer_median_non_positive", None
    ratio_excess = (actual - centre) / centre
    return _clip_score(100.0 * ratio_excess), "peer_ratio", None


def closed_time_score(
    metrics: ScheduleMetrics,
    peers: Sequence[TimePeerRecord],
) -> tuple[int | None, str | None, float | None]:
    if metrics.family != ScheduleFamily.CLOSED:
        return None, None, None
    if metrics.planned_duration_days is None or metrics.planned_duration_days <= 0:
        return None, None, None
    if metrics.actual_duration_days is None:
        return None, None, None
    delay_days = max(0, metrics.slippage_days or 0)
    plan_score = completed_plan_score(delay_days, metrics.planned_duration_days)
    peer_durations = [
        days
        for peer in peers
        if (days := duration_days(peer.actual_start_date, peer.actual_completion_date))
        and days > 0
    ]
    peer_median = median(peer_durations) if len(peer_durations) >= MIN_PEER_COUNT else None
    if plan_score == 0:
        return 0, "closed_on_plan", peer_median
    if len(peer_durations) >= MIN_PEER_COUNT:
        peer_score, peer_method, _z = _late_only_peer_score(
            float(metrics.actual_duration_days),
            peer_durations,
        )
        blended = _clip_score(0.6 * plan_score + 0.4 * peer_score)
        return blended, f"closed_plan_and_{peer_method}", peer_median
    return plan_score, "closed_plan_only", peer_median


def open_time_score(
    metrics: ScheduleMetrics,
    peers: Sequence[TimePeerRecord],
) -> tuple[int | None, str | None, float | None]:
    if metrics.family != ScheduleFamily.OPEN:
        return None, None, None
    if metrics.planned_duration_days is None or metrics.planned_duration_days <= 0:
        return None, None, None
    if metrics.time_consumed_percent is None:
        return None, None, None
    progress = float(metrics.physical_progress_percent) if metrics.physical_progress_percent is not None else None
    if progress is None:
        # Overdue without progress still has a timing signal.
        overdue_days = metrics.slippage_days or 0
        if overdue_days > 0:
            return overdue_score(overdue_days, metrics.planned_duration_days, progress=0), "open_overdue_only", None
        return None, None, None

    mismatch_part = ongoing_mismatch_score(metrics.time_consumed_percent, progress)
    overdue_days = metrics.slippage_days or 0
    overdue_part = overdue_score(overdue_days, metrics.planned_duration_days, progress=progress)
    own_score = max(mismatch_part, overdue_part)

    peer_mismatches: list[float] = []
    for peer in peers:
        peer_metrics = compute_schedule_metrics(peer)
        if (
            peer_metrics.family == ScheduleFamily.OPEN
            and peer_metrics.progress_mismatch_points is not None
        ):
            peer_mismatches.append(max(0.0, float(peer_metrics.progress_mismatch_points)))
    peer_median_duration = None
    peer_planned = [
        days
        for peer in peers
        if (days := duration_days(peer.planned_start_date, peer.planned_completion_date))
        and days > 0
    ]
    if peer_planned:
        peer_median_duration = median(peer_planned)

    if (
        metrics.progress_mismatch_points is not None
        and len(peer_mismatches) >= MIN_PEER_COUNT
    ):
        subject_mismatch = max(0.0, float(metrics.progress_mismatch_points))
        peer_score, peer_method, _z = _late_only_peer_score(
            subject_mismatch,
            peer_mismatches,
            require_positive=False,
        )
        blended = _clip_score(0.7 * own_score + 0.3 * peer_score)
        return blended, f"open_mismatch_and_{peer_method}", peer_median_duration
    method = "open_mismatch_and_overdue" if overdue_part > mismatch_part else "open_mismatch"
    return own_score, method, peer_median_duration


def evidence_confidence(
    *,
    time_mode: TimeMode,
    valid_dates: bool,
    sufficient_timing_evidence: bool,
    has_recommended_date: bool,
    scope_id: str | None,
    peer_count: int,
    peer_quality: int,
    has_planned_dates: bool,
    has_actual_dates: bool,
    has_progress: bool,
) -> int:
    """Evidence Confidence is separate from Time Anomaly."""
    if time_mode == TimeMode.REAL:
        if not has_recommended_date:
            return 0
        raw = 12
        if scope_id is not None:
            raw += min(10, max(0, peer_quality) // 10)
        elif peer_count > 0:
            raw += 2
        return int(min(REAL_CONFIDENCE_CAP, max(5, round(raw))))

    if not valid_dates:
        return 0
    if not sufficient_timing_evidence:
        raw = 8
        if has_recommended_date:
            raw += 2
        return int(min(18, max(5, raw)))

    raw = 36
    if has_planned_dates:
        raw += 8
    if has_actual_dates:
        raw += 8
    if has_progress:
        raw += 4
    if scope_id is not None:
        base = SCOPE_CONFIDENCE_BASE[scope_id]
        quality = max(0, min(100, peer_quality))
        raw = 0.45 * raw + 0.35 * base + 0.20 * quality
        if scope_id == "constituency_category":
            raw = min(raw, 58)
        if scope_id == "state_broader_work_type":
            raw = min(raw, 60)
    return int(min(HYBRID_CONFIDENCE_CAP, max(8, round(raw))))
