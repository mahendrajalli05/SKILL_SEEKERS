"""CLI: initialise SQLite and load the cleaned MPLADS extract."""

from __future__ import annotations

from app.pipeline.db_load import load_cleaned_works


def main() -> None:
    result = load_cleaned_works()
    print(f"database={result.database_path}")
    print(f"tables={result.table_count}")
    print(f"csv_rows={result.csv_row_count}")
    print(f"loaded_rows={result.loaded_row_count}")
    print(f"failed_rows={len(result.failed_rows)}")
    print(f"snapshot_id={result.snapshot_id}")
    print(f"replaced_previous={result.replaced_previous}")
    if result.failed_rows:
        for row in result.failed_rows[:20]:
            print(
                f"failed csv_row={row.csv_row_number} "
                f"internal_project_id={row.internal_project_id} reason={row.reason}"
            )
        raise SystemExit(1)
    if not result.ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
