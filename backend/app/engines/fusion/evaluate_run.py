"""CLI: run Risk Fusion V1.1 on selected real and HYBRID evaluation cases."""

from __future__ import annotations

from app.engines.fusion.evaluate import format_evaluation_rows, run_risk_fusion_evaluation


def main() -> None:
    rows = run_risk_fusion_evaluation()
    print(format_evaluation_rows(rows))
    real = [row for row in rows if row.dataset == "REAL"]
    hybrid = [row for row in rows if row.dataset == "HYBRID"]
    if len(real) < 10 or len(hybrid) < 10:
        raise SystemExit(
            f"expected at least 10 REAL and 10 HYBRID rows, got {len(real)} REAL / {len(hybrid)} HYBRID"
        )


if __name__ == "__main__":
    main()
