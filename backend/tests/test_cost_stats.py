from __future__ import annotations

import pytest

from app.engines.cost.stats import compute_peer_statistics, median, median_absolute_deviation, percentile


def test_median_odd_and_even() -> None:
    assert median([1, 3, 2]) == 2.0
    assert median([10, 20, 30, 40]) == 25.0


def test_percentile_linear_interpolation() -> None:
    values = [10.0, 20.0, 30.0, 40.0, 50.0]
    assert percentile(values, 0) == 10.0
    assert percentile(values, 50) == 30.0
    assert percentile(values, 25) == 20.0
    assert percentile(values, 75) == 40.0
    assert percentile(values, 100) == 50.0


def test_mad_of_symmetric_sample() -> None:
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    centre = median(values)
    assert centre == 3.0
    assert median_absolute_deviation(values, centre) == 1.0


def test_peer_statistics_include_percentile_range_and_mad() -> None:
    amounts = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
    stats = compute_peer_statistics(amounts)
    assert stats.peer_count == 10
    assert stats.median == 550.0
    assert stats.percentile_25 == 325.0
    assert stats.percentile_75 == 775.0
    assert stats.percentile_10 is not None
    assert stats.percentile_90 is not None
    assert stats.mad == 250.0


def test_percentiles_10_90_omitted_when_n_below_10() -> None:
    stats = compute_peer_statistics([1, 2, 3, 4, 5])
    assert stats.percentile_10 is None
    assert stats.percentile_90 is None
    assert stats.median == 3.0


def test_empty_amounts_raise() -> None:
    with pytest.raises(ValueError):
        compute_peer_statistics([])


def test_extreme_peer_amount_does_not_dominate_median() -> None:
    typical = [100_000, 120_000, 150_000, 180_000, 200_000, 220_000, 250_000, 300_000]
    skewed = [*typical, 100_000_000]
    stats = compute_peer_statistics(skewed)
    assert stats.median == 200_000.0
    assert stats.percentile_75 < 1_000_000
    assert stats.log_mad >= 0


def test_non_positive_amounts_raise() -> None:
    with pytest.raises(ValueError):
        compute_peer_statistics([100, 0, 200])

