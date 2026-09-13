"""CLI: clean the primary free MPLADS work-level extract into data/processed/."""

from __future__ import annotations

from app.pipeline.clean import (
    DEFAULT_OUTPUT_CSV,
    PRIMARY_WORKS_FILENAME,
    clean_primary_dataset,
)


def main() -> None:
    cleaned, stats = clean_primary_dataset()
    print(f"source={PRIMARY_WORKS_FILENAME}")
    print(f"raw_rows={stats.raw_row_count}")
    print(f"cleaned_rows={stats.cleaned_row_count}")
    print(f"andhra_pradesh_cleaned_rows={stats.andhra_pradesh_cleaned_count}")
    print(f"exact_extra_duplicates={stats.exact_extra_duplicate_count}")
    print(f"collapsed_rows={stats.collapsed_row_count}")
    print(f"observed_status_values={stats.observed_status_values}")
    print(f"raw_status_counts={stats.raw_status_counts}")
    print(f"cleaned_status_counts={stats.cleaned_status_counts}")
    print(f"lifecycle_counts={stats.lifecycle_counts}")
    print(f"output={DEFAULT_OUTPUT_CSV}")


if __name__ == "__main__":
    main()
