from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.pipeline.clean import (
    HASH_FIELD_ORDER,
    INTERNAL_ID_PREFIX,
    PRIMARY_WORKS_FILENAME,
    SOURCE_COLUMNS,
    clean_primary_dataset,
    clean_works_frame,
    lifecycle_from_status,
    make_internal_project_id,
    normalize_amount,
    normalize_date,
    normalize_ida,
    normalize_status,
    normalize_text_field,
    original_source_text,
)
from app.pipeline.load import load_tabular


def _normalized_record(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "mp_name": "Test MP",
        "work_description": "Street lights",
        "category": "Normal/Others",
        "state": "Andhra Pradesh",
        "constituency": "GUNTUR",
        "ida": "DISTRICT COLLECTOR GUNTUR_IDA",
        "city": "",
        "ward": "",
        "block": "Tenali",
        "village": "Village A",
        "recommended_date": "2024-01-15",
        "allocation_amount": 100000,
        "ida_approval": "Action Pending",
        "status": "Unsanctioned",
        "house": "Lok Sabha",
    }
    base.update(overrides)
    assert set(HASH_FIELD_ORDER) <= set(base)
    return base


def _source_frame(rows: list[dict[str, object]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=SOURCE_COLUMNS)


def test_internal_project_id_is_deterministic_and_labelled_internal() -> None:
    first = make_internal_project_id(_normalized_record())
    second = make_internal_project_id(_normalized_record())
    assert first == second
    assert first.startswith(INTERNAL_ID_PREFIX)
    assert "mplads" not in first.lower()
    changed = make_internal_project_id(_normalized_record(work_description="Roads"))
    assert changed != first


def test_date_normalization() -> None:
    assert normalize_date("2024-03-04") == "2024-03-04"
    assert normalize_date("15/01/2020") == "2020-01-15"
    assert normalize_date(" 2024-02-29 ") == "2024-02-29"
    assert normalize_date("") == ""
    assert normalize_date("not-a-date") == ""
    assert normalize_date("32/01/2020") == ""


def test_amount_normalization() -> None:
    assert normalize_amount("100000") == 100000
    assert normalize_amount("1,00,000") == 100000
    assert normalize_amount("Rs. 500") == 500
    assert normalize_amount("0") == 0
    assert normalize_amount("") is None
    assert normalize_amount("not-a-number") is None
    assert normalize_amount("₹ 2,500") == 2500


def test_status_normalization_does_not_invent_government_values() -> None:
    assert normalize_status(" ongoing ") == "Ongoing"
    assert normalize_status("UNSANCTIONED") == "Unsanctioned"
    assert normalize_status("") == ""
    assert normalize_status("Cancelled") == "Cancelled"
    assert lifecycle_from_status("Unsanctioned") == "FUTURE"
    assert lifecycle_from_status("Sanctioned") == "FUTURE"
    assert lifecycle_from_status("Ongoing") == "ONGOING"
    assert lifecycle_from_status("Completed") == "COMPLETED"
    assert lifecycle_from_status("") == "UNKNOWN"
    assert lifecycle_from_status("Cancelled") == "UNKNOWN"


def test_duplicate_handling_collapses_canonical_copies() -> None:
    row = {
        "MP NAME": "Shri Example ",
        "WORK": "NA - Street lights",
        "CATEGORY": "Normal/Others",
        "STATE": "Andhra Pradesh",
        "CONSTITUENCY": "GUNTUR",
        "IDA": "DISTRICT COLLECTOR GUNTUR_ida",
        "CITY": "",
        "WARD": "",
        "BLOCK": "Tenali",
        "VILLAGE": "Village A",
        "RECOMMENDED DATE": "2024-01-15",
        "ALLOCATION AMOUNT": "100000",
        "IDA APPROVAL": "Action Pending",
        "STATUS": "Unsanctioned",
        "HOUSE": "Lok Sabha",
    }
    spaced = dict(row)
    spaced["MP NAME"] = "Shri Example"
    spaced["IDA"] = "DISTRICT COLLECTOR GUNTUR_IDA"
    different_status = dict(row)
    different_status["STATUS"] = "Ongoing"

    frame = _source_frame([row, spaced, different_status, row])
    cleaned, stats = clean_works_frame(frame)

    assert stats.raw_row_count == 4
    assert stats.exact_extra_duplicate_count == 1
    assert len(cleaned) == 2
    unsanctioned = cleaned[cleaned["status"] == "Unsanctioned"].iloc[0]
    ongoing = cleaned[cleaned["status"] == "Ongoing"].iloc[0]
    assert unsanctioned["source_duplicate_count"] == 3
    assert ongoing["source_duplicate_count"] == 1
    assert unsanctioned["internal_project_id"] != ongoing["internal_project_id"]
    assert unsanctioned["ida"] == "DISTRICT COLLECTOR GUNTUR_IDA"


def test_source_values_are_preserved() -> None:
    frame = _source_frame(
        [
            {
                "MP NAME": "Shri Bhartruhari Mahtab ",
                "WORK": "NA - Street lights",
                "CATEGORY": "Normal/Others",
                "STATE": "Andhra Pradesh",
                "CONSTITUENCY": "nan",
                "IDA": "DISTRICT COLLECTOR GUNTUR_IDA",
                "CITY": "",
                "WARD": "",
                "BLOCK": "Tenali",
                "VILLAGE": "Village A",
                "RECOMMENDED DATE": "2024-03-04",
                "ALLOCATION AMOUNT": "100000",
                "IDA APPROVAL": "Approved by IDA",
                "STATUS": "Completed",
                "HOUSE": "Lok Sabha",
            }
        ]
    )
    cleaned, _stats = clean_works_frame(frame)
    row = cleaned.iloc[0]
    assert row["source_mp_name"] == "Shri Bhartruhari Mahtab "
    assert row["mp_name"] == "Shri Bhartruhari Mahtab"
    assert row["source_work"] == "NA - Street lights"
    assert row["work_description"] == "NA - Street lights"
    assert row["source_constituency"] == "nan"
    assert row["constituency"] == ""
    assert row["source_status"] == "Completed"
    assert row["status"] == "Completed"
    assert row["lifecycle_stage"] == "COMPLETED"
    assert row["recommended_date"] == "2024-03-04"
    assert row["allocation_amount"] == 100000
    assert "district" not in cleaned.columns
    assert "vendor" not in cleaned.columns
    assert "latitude" not in cleaned.columns
    assert "expenditure" not in cleaned.columns


def test_original_source_text_keeps_blank_and_non_blank() -> None:
    assert original_source_text("abc") == "abc"
    assert original_source_text("") == ""
    assert original_source_text(None) == ""


def test_normalize_text_and_ida() -> None:
    assert normalize_text_field("  Foo   Bar ") == "Foo Bar"
    assert normalize_ida("Deputy Commissioner Kakching_ida") == "Deputy Commissioner Kakching_IDA"


def test_clean_primary_dataset_writes_processed_not_raw(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    processed = tmp_path / "processed"
    raw_dir.mkdir()
    processed.mkdir()
    source = raw_dir / PRIMARY_WORKS_FILENAME
    fixture = _source_frame(
        [
            {
                "MP NAME": "Test MP",
                "WORK": "Road",
                "CATEGORY": "Normal/Others",
                "STATE": "Andhra Pradesh",
                "CONSTITUENCY": "GUNTUR",
                "IDA": "DISTRICT COLLECTOR GUNTUR_IDA",
                "CITY": "",
                "WARD": "",
                "BLOCK": "",
                "VILLAGE": "",
                "RECOMMENDED DATE": "2024-01-15",
                "ALLOCATION AMOUNT": "250000",
                "IDA APPROVAL": "Action Pending",
                "STATUS": "Unsanctioned",
                "HOUSE": "Lok Sabha",
            }
        ]
    )
    fixture.to_csv(source, index=False, sep=";")
    (raw_dir / f"{PRIMARY_WORKS_FILENAME}.provenance.json").write_text(
        '{"source_url": "https://example.invalid/MPLADS.csv", "extracted_at": "2026-09-09",'
        ' "download_date": "2026-09-09", "notes": "TEST FIXTURE — not a government extract"}',
        encoding="utf-8",
    )
    raw_before = source.read_bytes()
    output_csv = processed / "mplads_works_cleaned.csv"
    cleaned, stats = clean_primary_dataset(
        source,
        output_csv=output_csv,
        output_provenance=processed / "mplads_works_cleaned.provenance.json",
        cleaning_report_path=tmp_path / "DATA_CLEANING_REPORT.md",
        dictionary_path=tmp_path / "DATA_DICTIONARY.md",
        profiling_path=tmp_path / "DATA_PROFILING_REPORT.md",
        write_docs=True,
    )
    assert source.read_bytes() == raw_before
    assert output_csv.is_file()
    assert stats.cleaned_row_count == 1
    assert stats.andhra_pradesh_cleaned_count == 1
    assert cleaned.iloc[0]["internal_project_id"].startswith(INTERNAL_ID_PREFIX)
    loaded = load_tabular(output_csv)[0][0]
    assert "internal_project_id" in loaded.columns
    assert "source_mp_name" in loaded.columns
    report = (tmp_path / "DATA_CLEANING_REPORT.md").read_text(encoding="utf-8")
    assert "not an official MPLADS ID" in report
    assert "Coastal Andhra district list" in report
    dictionary = (tmp_path / "DATA_DICTIONARY.md").read_text(encoding="utf-8")
    assert "internal_project_id" in dictionary
    assert "BEGIN CLEANED DATASET" in dictionary
