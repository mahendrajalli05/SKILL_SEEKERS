from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from app.config import REPO_ROOT
from app.pipeline.discover import sha256_file
from app.pipeline.synthetic import (
    DEFAULT_CLEANED_CSV,
    DEFAULT_OUTPUT_CSV,
    DEFAULT_SEED,
    ENRICHMENT_SOURCE,
    OUTPUT_COLUMNS,
    RECORD_MODE,
    SYNTHETIC_ID_PREFIX,
    TARGET_RECORD_COUNT,
    assert_synthetic_output_dir,
    generate_and_write,
    generate_synthetic_enrichment,
    parse_int,
    parse_iso_date,
    pick_demo_projects,
    scenario_quota,
    write_synthetic_csv,
)
from app.pipeline.synthetic_validate import load_and_validate, validate_enrichment


def _project(
    pid: str,
    *,
    status: str,
    state: str = "Andhra Pradesh",
    constituency: str = "GUNTUR",
    amount: int = 500000,
    work: str = "Construction of roads, link roads, pathways",
    recommended: str = "2023-11-01",
    ida: str = "DISTRICT COLLECTOR GUNTUR_IDA",
    village: str = "Test Village",
    block: str = "Tenali",
) -> dict[str, object]:
    lifecycle = {
        "Unsanctioned": "FUTURE",
        "Sanctioned": "FUTURE",
        "Ongoing": "ONGOING",
        "Completed": "COMPLETED",
        "": "UNKNOWN",
    }.get(status, "UNKNOWN")
    return {
        "internal_project_id": pid,
        "state": state,
        "constituency": constituency,
        "category": "Normal/Others",
        "work_description": work,
        "allocation_amount": str(amount),
        "recommended_date": recommended,
        "status": status,
        "lifecycle_stage": lifecycle,
        "ida": ida,
        "city": "",
        "block": block,
        "village": village,
        "mp_name": "Shri Test MP",
        "house": "Lok Sabha",
    }


def _fixture_frame(n_extra_unsanctioned: int = 40) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for i in range(8):
        rows.append(
            _project(
                f"internal:fixture-completed-{i:03d}",
                status="Completed",
                constituency="NANDYAL" if i % 2 == 0 else "ONGOLE",
                amount=700000 + i * 10000,
                ida="DISTRICT COLLECTOR NANDYAL_IDA" if i % 2 == 0 else "DISTRICT COLLECTOR PRAKASAM_IDA",
            )
        )
    for i in range(6):
        rows.append(
            _project(
                f"internal:fixture-ongoing-{i:03d}",
                status="Ongoing",
                constituency="ANANTAPUR",
                amount=800000 + i * 25000,
                ida="DISTRICT COLLECTOR ANANTAPUR_IDA",
                work="Construction of community centers and community halls",
            )
        )
    for i in range(10):
        rows.append(
            _project(
                f"internal:fixture-sanctioned-{i:03d}",
                status="Sanctioned",
                constituency="GUNTUR",
                amount=400000 + i * 5000,
            )
        )
    for i in range(4):
        rows.append(
            _project(
                f"internal:fixture-unknown-{i:03d}",
                status="",
                constituency="KURNOOL",
                amount=250000,
                ida="DISTRICT COLLECTOR KURNOOL_IDA",
            )
        )
    for i in range(n_extra_unsanctioned):
        rows.append(
            _project(
                f"internal:fixture-unsanctioned-{i:03d}",
                status="Unsanctioned",
                constituency="VIZIANAGARAM",
                amount=300000,
                ida="DISTRICT COLLECTOR VIZIANAGARAM_IDA",
                work="NA - Street lights",
            )
        )
    rows.append(
        _project(
            "internal:fixture-up-completed-000",
            status="Completed",
            state="Uttar Pradesh",
            constituency="LUCKNOW",
            amount=550000,
            ida="DISTRICT MAGISTRATE LUCKNOW_IDA",
        )
    )
    return pd.DataFrame(rows)


def test_scenario_quota_matches_requested_mix_for_10000() -> None:
    counts = scenario_quota(10000)
    assert counts["NORMAL"] == 7000
    assert counts["COST_ANOMALY"] == 1000
    assert counts["TIME_ANOMALY"] == 800
    assert counts["OVERLAP"] == 500
    assert counts["EVIDENCE_GHOST"] == 400
    assert counts["MIXED"] == 300
    assert sum(counts.values()) == 10000


def test_demo_projects_are_deterministic() -> None:
    frame = _fixture_frame()
    first = pick_demo_projects(frame)
    second = pick_demo_projects(frame)
    assert first == second
    assert set(first) == {"GHOST", "OVERBILL", "STUCK", "CLEAN"}
    assert first["GHOST"] != first["OVERBILL"]


def test_generator_is_deterministic_with_fixed_seed() -> None:
    frame = _fixture_frame()
    first, _ = generate_synthetic_enrichment(frame, n=40, seed=26102)
    second, _ = generate_synthetic_enrichment(frame, n=40, seed=26102)
    pd.testing.assert_frame_equal(first, second)
    other, _ = generate_synthetic_enrichment(frame, n=40, seed=26103)
    assert not first.equals(other)


def test_hybrid_labels_and_synthetic_ids() -> None:
    frame = _fixture_frame()
    out, stats = generate_synthetic_enrichment(frame, n=40, seed=26102)
    assert list(out.columns) == OUTPUT_COLUMNS
    assert (out["record_mode"] == RECORD_MODE).all()
    assert (out["enrichment_source"] == ENRICHMENT_SOURCE).all()
    assert out["synthetic_record_id"].str.startswith(SYNTHETIC_ID_PREFIX).all()
    assert out["synthetic_record_id"].nunique() == 40
    assert out["internal_project_id"].nunique() == 40
    assert not out["synthetic_record_id"].str.lower().str.contains("mplads").any()
    assert stats.generated_records == 40
    for column in ("implementing_district", "implementing_agency", "vendor_name"):
        marked = out[column].astype(str).str.upper().str.contains("SYNTHETIC")
        present = out[column].astype(str).str.strip() != ""
        assert marked[present].all()


def test_normal_rows_keep_date_and_amount_constraints() -> None:
    frame = _fixture_frame()
    out, _ = generate_synthetic_enrichment(frame, n=40, seed=26102)
    normal = out[out["scenario_type"].isin(["NORMAL", "DEMO_CLEAN"])]
    assert not normal.empty
    for _, row in normal.iterrows():
        rec = parse_iso_date(row["real_recommended_date"])
        sanction = parse_iso_date(row["sanction_date"])
        planned_start = parse_iso_date(row["planned_start_date"])
        planned_end = parse_iso_date(row["planned_completion_date"])
        actual_start = parse_iso_date(row["actual_start_date"])
        actual_end = parse_iso_date(row["actual_completion_date"])
        if rec and sanction:
            assert rec <= sanction
        if sanction and planned_start:
            assert sanction <= planned_start
        if planned_start and planned_end:
            assert planned_start <= planned_end
        if actual_start and actual_end:
            assert actual_start <= actual_end
        sanctioned = parse_int(row["sanctioned_amount"])
        expenditure = parse_int(row["expenditure_amount"])
        milestone_total = parse_int(row["milestone_total_amount"])
        if sanctioned is not None and expenditure is not None:
            assert expenditure <= sanctioned
        if sanctioned is not None and milestone_total is not None:
            assert milestone_total <= sanctioned
        progress = parse_int(row["physical_progress_percent"])
        assert progress is not None and 0 <= progress <= 100
        if row["real_status"] == "Completed":
            assert row["actual_completion_date"]
        if row["real_status"] == "Ongoing":
            assert not str(row["actual_completion_date"]).strip()


def test_cost_anomaly_and_demo_cases_are_identifiable() -> None:
    frame = _fixture_frame()
    out, stats = generate_synthetic_enrichment(frame, n=40, seed=26102)
    assert set(stats.demo_case_ids) == {"GHOST", "OVERBILL", "STUCK", "CLEAN"}
    overbill = out[out["demo_case_id"] == "OVERBILL"].iloc[0]
    assert int(overbill["expenditure_amount"]) > int(overbill["sanctioned_amount"])
    stuck = out[out["demo_case_id"] == "STUCK"].iloc[0]
    assert not str(stuck["actual_completion_date"]).strip()
    assert int(stuck["physical_progress_percent"]) <= 20
    ghost = out[out["demo_case_id"] == "GHOST"].iloc[0]
    assert ghost["actual_completion_date"]
    assert int(ghost["physical_progress_percent"]) == 100
    clean = out[out["demo_case_id"] == "CLEAN"].iloc[0]
    assert clean["scenario_type"] == "DEMO_CLEAN"
    cost = out[out["scenario_type"] == "COST_ANOMALY"]
    if not cost.empty:
        row = cost.iloc[0]
        assert int(row["expenditure_amount"]) > int(row["sanctioned_amount"])


def test_validation_accepts_fixture_output() -> None:
    frame = _fixture_frame()
    out, _ = generate_synthetic_enrichment(frame, n=40, seed=26102)
    real_ids = set(frame["internal_project_id"])
    report = validate_enrichment(out, real_ids=real_ids, expected_n=40)
    assert report.duplicate_synthetic_ids == 0
    assert report.ok, [issue.message for issue in report.hard_violations]


def test_write_refuses_raw_and_processed(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="data\\\\raw|data/raw"):
        assert_synthetic_output_dir(REPO_ROOT / "data" / "raw")
    with pytest.raises(ValueError, match="processed"):
        assert_synthetic_output_dir(REPO_ROOT / "data" / "processed")
    frame = _fixture_frame()
    out, _ = generate_synthetic_enrichment(frame, n=20, seed=26102)
    target = tmp_path / "synthetic" / "out.csv"
    write_synthetic_csv(out, target)
    assert target.is_file()
    assert not (REPO_ROOT / "data" / "raw" / "out.csv").exists()


def test_generate_and_write_does_not_modify_real_extract(tmp_path: Path) -> None:
    if not DEFAULT_CLEANED_CSV.is_file():
        pytest.skip("cleaned real extract not present")
    before = sha256_file(DEFAULT_CLEANED_CSV)
    raw_dir = REPO_ROOT / "data" / "raw"
    raw_before = {path.name: path.stat().st_mtime for path in raw_dir.glob("*") if path.is_file()}
    source = pd.read_csv(DEFAULT_CLEANED_CSV, dtype=str, keep_default_na=False)
    sample = source.head(80).copy()
    generate_and_write(source_csv=DEFAULT_CLEANED_CSV, output_dir=tmp_path, n=40, seed=26102)
    assert sha256_file(DEFAULT_CLEANED_CSV) == before
    raw_after = {path.name: path.stat().st_mtime for path in raw_dir.glob("*") if path.is_file()}
    assert raw_after == raw_before
    assert (tmp_path / "sarvsakshi_synthetic_enrichment.csv").is_file()
    assert not (REPO_ROOT / "data" / "processed" / "sarvsakshi_synthetic_enrichment.csv").exists()
    assert sample.equals(pd.read_csv(DEFAULT_CLEANED_CSV, dtype=str, keep_default_na=False).head(80))


def test_links_only_to_real_internal_ids() -> None:
    frame = _fixture_frame()
    out, _ = generate_synthetic_enrichment(frame, n=40, seed=26102)
    assert set(out["internal_project_id"]).issubset(set(frame["internal_project_id"]))
    assert out["internal_project_id"].str.startswith("internal:").all()


def test_repo_dataset_validates_when_present() -> None:
    if not DEFAULT_OUTPUT_CSV.is_file():
        pytest.skip("synthetic enrichment CSV has not been generated yet")
    report = load_and_validate(DEFAULT_OUTPUT_CSV, DEFAULT_CLEANED_CSV, expected_n=TARGET_RECORD_COUNT)
    assert report.total_records == TARGET_RECORD_COUNT
    assert report.duplicate_synthetic_ids == 0
    assert report.ok, [issue.message for issue in report.hard_violations]
    assert report.unique_internal_project_ids == TARGET_RECORD_COUNT
