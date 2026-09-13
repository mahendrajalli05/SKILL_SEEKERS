from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.config import REPO_ROOT
from app.pipeline.clean import preserve_cleaned_section
from app.pipeline.discover import build_provenance, discover_raw_files
from app.pipeline.load import load_tabular
from app.pipeline.profile import combine_andhra, combine_intelligence, profile_frame, recommended_works_join_keys
from app.pipeline.render import render_data_dictionary, render_profiling_report
from app.pipeline.types import DatasetInventory, DatasetProfile

DEFAULT_RAW_DIR = REPO_ROOT / "data" / "raw"
DEFAULT_REPORT_PATH = REPO_ROOT / "DATA_PROFILING_REPORT.md"
DEFAULT_DICTIONARY_PATH = REPO_ROOT / "DATA_DICTIONARY.md"

EMPTY_REASON = (
    "No tabular extracts were found in data/raw/ (only skippable files such as .gitkeep, "
    "or the directory was empty). Raw files were not modified. Government field inventories, "
    "Andhra Pradesh counts, and Coastal Andhra correspondence cannot be produced until real "
    "MPLADS extracts are present."
)


def profile_raw_directory(
    raw_dir: Path | None = None,
    *,
    report_path: Path | None = None,
    dictionary_path: Path | None = None,
    write_reports: bool = True,
) -> DatasetInventory:
    raw_dir = Path(raw_dir) if raw_dir is not None else DEFAULT_RAW_DIR
    report_path = Path(report_path) if report_path is not None else DEFAULT_REPORT_PATH
    dictionary_path = Path(dictionary_path) if dictionary_path is not None else DEFAULT_DICTIONARY_PATH

    files, skipped = discover_raw_files(raw_dir)
    datasets: list[DatasetProfile] = []
    for path in files:
        provenance = build_provenance(path, raw_dir)
        loaded = load_tabular(path)
        for frame, sheet_name, header_i, notes in loaded:
            datasets.append(
                profile_frame(
                    frame,
                    relative_path=path.relative_to(raw_dir).as_posix(),
                    sheet_name=sheet_name,
                    header_row_index=header_i,
                    load_notes=notes,
                    provenance=provenance,
                )
            )

    empty_reason = EMPTY_REASON if not datasets else None
    recommended_id, join_keys = recommended_works_join_keys(datasets) if datasets else (None, [])
    inventory = DatasetInventory(
        profiled_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        raw_dir=str(raw_dir),
        skipped_names=skipped,
        datasets=datasets,
        empty_reason=empty_reason,
        combined_andhra=combine_andhra(datasets) if datasets else None,
        combined_intelligence=combine_intelligence(datasets),
        join_keys=join_keys,
        recommended_works_dataset_id=recommended_id,
    )
    if write_reports:
        report_text = render_profiling_report(inventory)
        dictionary_text = render_data_dictionary(inventory)
        if report_path.exists():
            report_text = preserve_cleaned_section(
                report_path.read_text(encoding="utf-8"), report_text
            )
        if dictionary_path.exists():
            dictionary_text = preserve_cleaned_section(
                dictionary_path.read_text(encoding="utf-8"), dictionary_text
            )
        report_path.write_text(report_text, encoding="utf-8")
        dictionary_path.write_text(dictionary_text, encoding="utf-8")
    return inventory


def main() -> None:
    inventory = profile_raw_directory()
    print(f"profiled_at={inventory.profiled_at}")
    print(f"raw_dir={inventory.raw_dir}")
    print(f"datasets={len(inventory.datasets)}")
    print(f"skipped={inventory.skipped_names}")
    if inventory.empty_reason:
        print(inventory.empty_reason)


if __name__ == "__main__":
    main()
