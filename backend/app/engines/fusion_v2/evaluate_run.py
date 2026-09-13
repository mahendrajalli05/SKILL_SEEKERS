"""CLI: run Risk Fusion V2 on selected REAL and HYBRID evaluation cases."""

from __future__ import annotations

from app.engines.fusion_v2.evaluate import format_evaluation_rows, run_risk_fusion_v2_evaluation


def main() -> None:
    rows = run_risk_fusion_v2_evaluation()
    print(format_evaluation_rows(rows))
    real = [row for row in rows if row.dataset == "REAL"]
    hybrid = [row for row in rows if row.dataset == "HYBRID"]
    if len(real) < 15 or len(hybrid) < 15:
        raise SystemExit(
            f"expected at least 15 REAL and 15 HYBRID rows, got {len(real)} REAL / {len(hybrid)} HYBRID"
        )


if __name__ == "__main__":
    main()
