from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.pipeline.classify import likely_role
from app.pipeline.profile import (
    combine_andhra,
    combine_intelligence,
    is_andhra_pradesh_state,
    profile_frame,
    recommended_works_join_keys,
)
from app.pipeline.render import COASTAL_UNDECIDED, render_data_dictionary, render_profiling_report
from app.pipeline.run import profile_raw_directory
from app.pipeline.types import DatasetInventory, Provenance
from app.pipeline.validate import validate_inventory


def _prov(name: str = "fixture.csv") -> Provenance:
    return Provenance(
        original_filename=name,
        relative_path=name,
        size_bytes=1,
        sha256="0" * 64,
        notes="TEST FIXTURE — not a government extract",
        missing_fields=["source_url", "extracted_at_or_download_date"],
    )


def _mplads_shaped_frame() -> pd.DataFrame:
    """Tiny in-memory fixture. Not government data and not written to data/raw."""
    return pd.DataFrame(
        {
            "Unique ID of Work": ["W1", "W2", "W2", "W3", "W4"],
            "State": [
                "Andhra Pradesh",
                "Andhra Pradesh",
                "Andhra Pradesh",
                "Telangana",
                "ANDHRA PRADESH",
            ],
            "District": ["Visakhapatnam", "Guntur", "Guntur", "Hyderabad", "Chittoor"],
            "Work Name": ["Road", "School", "School", "Hall", ""],
            "Implementing Agency": ["XYZ", "ABC", "ABC", "DEF", ""],
            "Work Status": ["Completed", "Ongoing", "Ongoing", "Completed", "Completed"],
            "Recommended Amount (Rs.)": ["100000", "200000", "200000", "150000", "not-a-number"],
            "Sanction Date": ["15/01/2020", "01/03/2021", "01/03/2021", "bad-date", ""],
            "Latitude": ["17.68", "", "", "", ""],
            "Longitude": ["83.21", "", "", "", ""],
        }
    )


def test_andhra_state_match_does_not_include_andaman() -> None:
    assert is_andhra_pradesh_state("Andhra Pradesh") is True
    assert is_andhra_pradesh_state("ANDHRA PRADESH") is True
    assert is_andhra_pradesh_state("AP") is True
    assert is_andhra_pradesh_state("Telangana") is False
    assert is_andhra_pradesh_state("Andaman and Nicobar Islands") is False


def test_profile_shape_missing_duplicates_and_quality() -> None:
    frame = _mplads_shaped_frame()
    profile = profile_frame(
        frame,
        relative_path="fixture.csv",
        sheet_name=None,
        header_row_index=0,
        load_notes=[],
        provenance=_prov(),
    )

    assert profile.n_rows == 5
    assert profile.n_columns == 10
    assert profile.columns == list(frame.columns)
    assert profile.duplicate_extra_row_count == 1
    assert profile.duplicate_id_extra_counts["Unique ID of Work"] == 1

    amount = next(c for c in profile.column_profiles if c.name == "Recommended Amount (Rs.)")
    assert amount.likely_role == "amount"
    assert amount.missing_count == 0
    assert amount.numeric_parseable_count == 4
    assert amount.date_parseable_count is None
    assert amount.suspected_unit == "inr"

    sanction = next(c for c in profile.column_profiles if c.name == "Sanction Date")
    assert sanction.likely_role == "date"
    assert sanction.date_parseable_count == 3
    assert sanction.date_invalid_non_null_count == 1

    work_name = next(c for c in profile.column_profiles if c.name == "Work Name")
    assert work_name.missing_count == 1
    assert work_name.missing_pct == 20.0


def test_andhra_counts_without_inventing_coastal_list() -> None:
    profile = profile_frame(
        _mplads_shaped_frame(),
        relative_path="fixture.csv",
        sheet_name=None,
        header_row_index=0,
        load_notes=[],
        provenance=_prov(),
    )
    andhra = profile.andhra
    assert andhra is not None
    assert andhra.total_ap_records == 4
    names = {d.name: d.record_count for d in andhra.districts}
    assert names == {"Guntur": 2, "Visakhapatnam": 1, "Chittoor": 1}
    assert "Hyderabad" not in names
    assert andhra.coastal_region_fields_observed == []
    assert "No final Coastal Andhra district list is asserted" in andhra.coastal_correspondence_note
    assert "cannot be decided" in andhra.coastal_correspondence_note.lower() or "does not" in andhra.coastal_correspondence_note.lower()


def test_intelligence_fields_use_only_observed_columns() -> None:
    profile = profile_frame(
        _mplads_shaped_frame(),
        relative_path="fixture.csv",
        sheet_name=None,
        header_row_index=0,
        load_notes=[],
        provenance=_prov(),
    )
    observed = set(profile.columns)
    for group in (
        profile.intelligence.cost_fields,
        profile.intelligence.time_fields,
        profile.intelligence.overlap_fields,
        profile.intelligence.relationship_graph_fields,
        profile.intelligence.evidence_passport_fields,
    ):
        assert set(group) <= observed
    assert "Recommended Amount (Rs.)" in profile.intelligence.cost_fields
    assert "Sanction Date" in profile.intelligence.time_fields
    assert "Work Name" in profile.intelligence.overlap_fields
    assert "Implementing Agency" in profile.intelligence.relationship_graph_fields
    assert "Unique ID of Work" in profile.intelligence.evidence_passport_fields
    assert "invented_satellite_area" not in observed


def test_dictionary_contains_only_observed_fields() -> None:

    dataset = profile_frame(
        _mplads_shaped_frame(),
        relative_path="fixture.csv",
        sheet_name=None,
        header_row_index=0,
        load_notes=[],
        provenance=_prov(),
    )
    inventory = DatasetInventory(
        profiled_at="2026-09-09T00:00:00+00:00",
        raw_dir="tmp",
        skipped_names=[],
        datasets=[dataset],
        combined_andhra=combine_andhra([dataset]),
        combined_intelligence=combine_intelligence([dataset]),
    )
    dictionary = render_data_dictionary(inventory)
    report = render_profiling_report(inventory)
    for column in dataset.columns:
        assert f"`{column}`" in dictionary
    assert "blueprint_area_m2" not in dictionary
    assert "fraud_probability" not in dictionary
    assert COASTAL_UNDECIDED in report


def test_empty_raw_directory_does_not_invent_fields(tmp_path: Path) -> None:
    (tmp_path / ".gitkeep").write_text("", encoding="utf-8")
    report_path = tmp_path / "report.md"
    dictionary_path = tmp_path / "dict.md"

    inventory = profile_raw_directory(
        tmp_path,
        report_path=report_path,
        dictionary_path=dictionary_path,
        write_reports=True,
    )

    assert inventory.datasets == []
    assert inventory.empty_reason is not None
    assert "None. No tabular extracts were present" in dictionary_path.read_text(encoding="utf-8")
    issues = validate_inventory(inventory)
    assert any(issue.code == "empty_raw" for issue in issues)


def test_end_to_end_csv_with_sidecar(tmp_path: Path) -> None:
    csv_path = tmp_path / "works.csv"
    _mplads_shaped_frame().to_csv(csv_path, index=False)
    (tmp_path / "works.csv.provenance.json").write_text(
        '{"source_url": "https://example.invalid/works.csv", "extracted_at": "2026-09-01"}',
        encoding="utf-8",
    )
    inventory = profile_raw_directory(tmp_path, write_reports=False)
    assert len(inventory.datasets) == 1
    dataset = inventory.datasets[0]
    assert dataset.n_rows == 5
    assert dataset.provenance.source_url == "https://example.invalid/works.csv"
    assert dataset.andhra is not None
    assert dataset.andhra.total_ap_records == 4
    issues = validate_inventory(inventory)
    assert any(issue.code == "duplicate_rows" for issue in issues)


def test_column_roles_from_names() -> None:
    assert likely_role("Implementing District") == "district"
    assert likely_role("Work Status") == "status"
    assert likely_role("Latitude") == "latitude"
    assert likely_role("WORK") == "description"
    assert likely_role("IDA") == "agency"
    assert likely_role("vendor_name") == "vendor"
    assert likely_role("MPName") == "mp"
    assert likely_role("Something unrelated") == "other"


def test_join_keys_against_recommended_works() -> None:
    recommended = profile_frame(
        _mplads_shaped_frame(),
        relative_path="github_vonter_india-mplads-works_MPLADS.csv",
        sheet_name=None,
        header_row_index=0,
        load_notes=[],
        provenance=_prov("github_vonter_india-mplads-works_MPLADS.csv"),
    )
    other = profile_frame(
        pd.DataFrame(
            {
                "State": ["Andhra Pradesh"],
                "Constituency": ["Guntur"],
                "vendor_name": ["Test Vendor"],
                "expenditure_amount": ["1000"],
            }
        ),
        relative_path="vendor.csv",
        sheet_name=None,
        header_row_index=0,
        load_notes=[],
        provenance=_prov("vendor.csv"),
    )
    rec_id, pairs = recommended_works_join_keys([recommended, other])
    assert rec_id == recommended.dataset_id
    assert any(p.right_column == "State" and p.likely_role == "state" for p in pairs)
    assert not any(p.right_column == "vendor_name" for p in pairs)
    assert not any(p.right_column == "expenditure_amount" for p in pairs)

