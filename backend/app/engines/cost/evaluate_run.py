"""CLI: run Cost Intelligence V1 on selected real and HYBRID evaluation cases."""

from __future__ import annotations

from app.engines.cost.evaluate import format_evaluation_rows, run_cost_intelligence_evaluation


def main() -> None:
    rows = run_cost_intelligence_evaluation()
    print(format_evaluation_rows(rows))
    if len(rows) != 10:
        raise SystemExit(f"expected 10 evaluation rows, got {len(rows)}")


if __name__ == "__main__":
    main()
