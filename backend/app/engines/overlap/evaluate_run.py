"""CLI: run Overlap Intelligence V1 on selected real and HYBRID evaluation cases."""

from __future__ import annotations

from app.engines.overlap.evaluate import format_evaluation_rows, run_overlap_intelligence_evaluation


def main() -> None:
    rows = run_overlap_intelligence_evaluation()
    print(format_evaluation_rows(rows))
    if len(rows) != 20:
        raise SystemExit(f"expected 20 evaluation rows, got {len(rows)}")


if __name__ == "__main__":
    main()
