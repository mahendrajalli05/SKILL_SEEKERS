import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { RiskScoreCard } from "@/components/RiskScoreCard";
import type { ProjectRiskResponse } from "@/lib/types";

const baseRisk: ProjectRiskResponse = {
  project_id: 1,
  internal_project_id: "internal:test",
  investigation_priority: 0,
  investigation_priority_0_100: 0,
  raw_risk: 0,
  evidence_confidence: 0,
  priority_band: "LOW",
  explanation_type: "INSUFFICIENT_EVIDENCE",
  explanation_types: ["INSUFFICIENT_EVIDENCE"],
  recommended_action: "MONITOR",
  data_mode: "REAL",
  contributing_signals: [],
  unavailable_signals: [],
  evidence_ids: [],
  explanation: "No assessable fused signals.",
  recommendation: "Monitor using available records.",
  available_signal_weight: 0,
  unavailable_signal_weight: 0.7,
  evidence_coverage: 0,
  engine_version: "risk-fusion-v1.1",
  weight_note: "Prototype weights only.",
  note: "Investigation Priority is not a fraud probability.",
};

describe("RiskScoreCard", () => {
  it("does not display an assessed zero for insufficient evidence", () => {
    render(<RiskScoreCard risk={baseRisk} />);
    expect(screen.getAllByText(/not a fraud probability/i).length).toBeGreaterThan(0);
    expect(document.body.textContent?.toLowerCase()).not.toContain("fraud score");
  });

  it("displays assessed Investigation Priority when fusion produced a score", () => {
    render(
      <RiskScoreCard
        risk={{
          ...baseRisk,
          investigation_priority: 36,
          evidence_confidence: 40,
          explanation_type: "WHY_FLAGGED",
          recommended_action: "REVIEW",
        }}
      />,
    );
    expect(screen.getByText("36")).toBeInTheDocument();
    expect(screen.getByText("40")).toBeInTheDocument();
    expect(screen.getByText("Review")).toBeInTheDocument();
    expect(screen.getByText("REVIEW")).toBeInTheDocument();
  });
});
