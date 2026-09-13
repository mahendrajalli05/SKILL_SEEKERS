from __future__ import annotations

from app.engines.cost.constants import FLAG_SCORE_THRESHOLD
from app.engines.cost.scoring import (
    cost_anomaly_score,
    deviation_percentage,
    evidence_confidence,
    is_cost_anomaly,
    modified_z_score,
)
from app.engines.cost.stats import compute_peer_statistics


def test_deviation_percentage_example_37_4() -> None:
    assert deviation_percentage(137.4, 100.0) == 37.4
    assert deviation_percentage(62.6, 100.0) == -37.4
    assert deviation_percentage(100.0, 100.0) == 0.0


def test_modified_z_none_when_mad_zero() -> None:
    assert modified_z_score(10.0, 10.0, 0.0) is None
    assert modified_z_score(20.0, 10.0, 2.0) == 0.6745 * 10.0 / 2.0


def test_identical_peers_and_equal_actual_score_zero() -> None:
    stats = compute_peer_statistics([500_000] * 8)
    score, dev, z, method = cost_anomaly_score(500_000, stats)
    assert score == 0
    assert dev == 0.0
    assert z == 0.0
    assert method == "equal_to_median"
    assert not is_cost_anomaly(score)


def test_identical_peers_double_is_moderate_not_max() -> None:
    stats = compute_peer_statistics([500_000] * 8)
    score, dev, z, method = cost_anomaly_score(1_000_000, stats)
    assert dev == 100.0
    assert method == "log_ratio_identical_peers"
    assert z is None
    assert score == 50
    assert not is_cost_anomaly(score)


def test_identical_peers_four_times_maps_to_100() -> None:
    stats = compute_peer_statistics([500_000] * 8)
    score, _dev, _z, method = cost_anomaly_score(2_000_000, stats)
    assert method == "log_ratio_identical_peers"
    assert score == 100
    assert is_cost_anomaly(score)


def test_low_amount_is_also_anomalous() -> None:
    stats = compute_peer_statistics([500_000] * 8)
    score, dev, _z, _method = cost_anomaly_score(1, stats)
    assert dev == -100.0
    assert score >= FLAG_SCORE_THRESHOLD


def test_loose_work_type_cluster_does_not_max_out_on_modest_deviation() -> None:
    # Round-number clustering across unrelated titles: MAD is tiny, Jaccard is low.
    stats = compute_peer_statistics([200_000] * 7 + [199_950])
    score, dev, _z, method = cost_anomaly_score(
        267_000,
        stats,
        median_work_type_similarity=0.0,
    )
    assert method in {"log_ratio_loose_work_type", "log_ratio_identical_peers"}
    assert 20 <= score <= 30
    assert not is_cost_anomaly(score)
    assert dev == 33.5


def test_precise_group_still_uses_modified_z_when_spread_exists() -> None:
    amounts = [400_000, 450_000, 480_000, 500_000, 520_000, 550_000, 600_000, 650_000]
    stats = compute_peer_statistics(amounts)
    score, _dev, _z, _method = cost_anomaly_score(500_000, stats)
    assert 0 <= score <= 100
    assert not is_cost_anomaly(score)


def test_score_is_deterministic() -> None:
    stats = compute_peer_statistics([100, 200, 300, 400, 500, 600, 700])
    first = cost_anomaly_score(900, stats)
    second = cost_anomaly_score(900, stats)
    assert first == second


def test_score_is_monotonic_in_log_ratio_for_identical_peers() -> None:
    stats = compute_peer_statistics([500_000] * 8)
    scores = [
        cost_anomaly_score(amount, stats)[0]
        for amount in (500_000, 750_000, 1_000_000, 2_000_000, 5_000_000)
    ]
    assert scores == sorted(scores)
    assert scores[0] == 0
    assert scores[-1] == 100


def test_confidence_uses_peer_quality_not_raw_count() -> None:
    tight = evidence_confidence(
        scope_id="constituency_category_work_type",
        peer_count=8,
        mad=10_000.0,
        valid_amount=True,
        peer_quality=90,
    )
    loose_many = evidence_confidence(
        scope_id="constituency_category",
        peer_count=329,
        mad=1.0,
        valid_amount=True,
        peer_quality=40,
    )
    fallback = evidence_confidence(
        scope_id="state_broader_work_type",
        peer_count=5,
        mad=0.0,
        valid_amount=True,
        peer_quality=60,
        constituency_usable=False,
    )
    insufficient = evidence_confidence(
        scope_id=None,
        peer_count=2,
        mad=None,
        valid_amount=True,
        peer_quality=0,
    )
    invalid = evidence_confidence(
        scope_id=None,
        peer_count=0,
        mad=None,
        valid_amount=False,
    )
    assert tight > loose_many
    assert tight > fallback
    assert fallback > insufficient
    assert invalid == 0
    assert loose_many <= 52
    assert 0 <= tight <= 90
