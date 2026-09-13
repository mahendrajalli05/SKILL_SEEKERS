import { describe, expect, it } from "vitest";

import {
  UNAVAILABLE_REAL_LABEL,
  displayBoundedScore,
  displayEvidenceConfidence,
  displayInvestigationPriority,
  displayText,
  formatAllocation,
  parseDataMode,
  withModePath,
} from "@/lib/display";
import type { ProjectRiskResponse } from "@/lib/types";

function risk(overrides: Partial<ProjectRiskResponse>): ProjectRiskResponse {
  return {
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
    explanation: "Insufficient evidence.",
    recommendation: "Monitor",
    available_signal_weight: 0,
    unavailable_signal_weight: 0.7,
    evidence_coverage: 0,
    engine_version: "risk-fusion-v1.1",
    weight_note: "Prototype weights only.",
    note: "Not a fraud probability.",
    ...overrides,
  };
}

describe("display helpers", () => {
  it("does not treat missing text as a zero value", () => {
    expect(displayText(null)).toBe(UNAVAILABLE_REAL_LABEL);
    expect(displayText("")).toBe(UNAVAILABLE_REAL_LABEL);
    expect(displayText(null)).not.toBe("0");
    expect(displayText(null)).not.toBe("N/A");
  });

  it("does not invent an amount unit", () => {
    expect(formatAllocation(250000)).toContain("unit unspecified");
    expect(formatAllocation(null)).toBe(UNAVAILABLE_REAL_LABEL);
  });

  it("does not show 0 when Investigation Priority is not assessed", () => {
    const shown = displayInvestigationPriority(risk({ investigation_priority: 0 }));
    expect(shown.assessed).toBe(false);
    expect(shown.label).toContain("insufficient evidence");
    expect(shown.label).not.toBe("0");
  });

  it("shows assessed 0 only when evidence exists", () => {
    const shown = displayInvestigationPriority(
      risk({
        investigation_priority: 0,
        explanation_type: "WHY_NOT_FLAGGED",
      }),
    );
    expect(shown.assessed).toBe(true);
    expect(shown.label).toBe("0");
  });

  it("keeps Evidence Confidence unassessed when evidence is insufficient", () => {
    const shown = displayEvidenceConfidence(risk({ evidence_confidence: 0 }));
    expect(shown.assessed).toBe(false);
    expect(shown.label).not.toBe("0");
  });

  it("renders Not assessable instead of a fake zero score", () => {
    const shown = displayBoundedScore(0, "NOT_ASSESSABLE");
    expect(shown.assessed).toBe(false);
    expect(shown.label).toBe("Not assessable");
  });

  it("defaults application data mode to HYBRID", () => {
    expect(parseDataMode(null)).toBe("HYBRID");
    expect(parseDataMode("hybrid")).toBe("HYBRID");
    expect(parseDataMode("real")).toBe("REAL");
  });

  it("keeps URL hashes after the data-mode query", () => {
    expect(withModePath("/projects/1/investigate#copilot", "REAL")).toBe(
      "/projects/1/investigate?mode=real#copilot",
    );
  });
});
