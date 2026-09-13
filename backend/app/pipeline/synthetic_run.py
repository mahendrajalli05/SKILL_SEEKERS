"""CLI: generate and validate the SYNTHETIC HYBRID enrichment layer."""

from __future__ import annotations

import argparse
from pathlib import Path

from app.pipeline.synthetic import (
    DEFAULT_CLEANED_CSV,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SEED,
    TARGET_RECORD_COUNT,
    generate_and_write,
)
from app.pipeline.synthetic_validate import (
    format_report,
    load_and_validate,
    write_validation_report,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate SYNTHETIC HYBRID enrichment under data/synthetic/ only."
    )
    parser.add_argument("--source-csv", type=Path, default=DEFAULT_CLEANED_CSV)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--n", type=int, default=TARGET_RECORD_COUNT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    if not args.validate_only:
        result = generate_and_write(
            source_csv=args.source_csv,
            output_dir=args.output_dir,
            n=args.n,
            seed=args.seed,
        )
        stats = result.stats
        print(f"output={result.csv_path}")
        print(f"provenance={result.provenance_path}")
        print(f"seed={stats.seed}")
        print(f"total_synthetic_records={stats.generated_records}")
        print(f"unique_internal_project_ids={stats.unique_internal_project_ids}")
        print(f"scenario_distribution={stats.scenario_counts}")
        print(f"demo_case_ids={stats.demo_case_ids}")

    csv_path = args.output_dir / "sarvsakshi_synthetic_enrichment.csv"
    report = load_and_validate(csv_path, args.source_csv, expected_n=args.n)
    report_path = args.output_dir / "VALIDATION_REPORT.md"
    write_validation_report(report, report_path)
    print(format_report(report))
    print(f"validation_report={report_path}")
    if not report.ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
