from __future__ import annotations

from app.evidence.ids import make_evidence_id


def test_evidence_id_is_deterministic() -> None:
    first = make_evidence_id(
        engine_name="cost",
        engine_version="cost-peer-v1.1",
        project_id=3715,
        signal_type="allocation_cost_anomaly",
        data_mode="REAL",
    )
    second = make_evidence_id(
        engine_name="cost",
        engine_version="cost-peer-v1.1",
        project_id=3715,
        signal_type="allocation_cost_anomaly",
        data_mode="REAL",
    )
    assert first == second
    assert first.startswith("ev:cost:3715:allocation_cost_anomaly:REAL:")


def test_evidence_id_changes_with_project_and_mode() -> None:
    base = dict(
        engine_name="time",
        engine_version="time-peer-v1",
        signal_type="time_anomaly",
    )
    real = make_evidence_id(project_id=10, data_mode="REAL", **base)
    other = make_evidence_id(project_id=11, data_mode="REAL", **base)
    hybrid = make_evidence_id(project_id=10, data_mode="HYBRID", **base)
    assert real != other
    assert real != hybrid


def test_evidence_id_extra_distinguishes_observations() -> None:
    base = dict(
        engine_name="ml",
        engine_version="cost-anomaly-v1-abc",
        project_id=12,
        signal_type="ML_ANOMALY_SIGNAL",
        data_mode="REAL",
    )
    first = make_evidence_id(**base)
    second = make_evidence_id(**base, extra="2026-09-10T00:00:00+00:00:abcd")
    third = make_evidence_id(**base, extra="2026-09-10T00:00:01+00:00:efgh")
    assert first != second
    assert second != third
    assert first.startswith("ev:ml:12:ML_ANOMALY_SIGNAL:REAL:")
