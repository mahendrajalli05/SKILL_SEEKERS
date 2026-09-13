import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { RiskFusionV2Panel } from "@/components/RiskFusionV2Panel";
import type { ProjectRiskV2Response } from "@/lib/types";

const baseRisk: ProjectRiskV2Response = {
  project_id: 1,
  internal_project_id: "internal:test",
  investigation_priority: 78,
  investigation_priority_0_100: 78,
  raw_risk: 78,
  evidence_confidence: 74,
  risk_class: "HIGH",
  explanation_type: "WHY_FLAGGED",
  explanation_types: ["WHY_FLAGGED"],
  recommended_action: "INSPECT",
  data_mode: "HYBRID",
  contributing_evidence_groups: [],
  independent_evidence_groups: [
    {
      signal: "cost",
      group_id: "cost",
      display_name: "Cost",
      weight: 0.14,
      state: "ASSESSABLE",
      polarity: "NEGATIVE_SIGNAL",
      raw_evidence_score: 100,
      confidence: 0.8,
      confidence_adjusted_score: 91,
      correlation_factor: 1,
      correlation_reason: null,
      dependency_correlation_adjustment: 1,
      effective_contribution: 12.74,
      evidence_ids: ["ev:cost:1:allocation_cost_anomaly:HYBRID:abc"],
      source_ids: ["internal:test"],
      items: [],
      finding: "Allocation anomaly",
      support: "peer comparison",
      unavailable_reason: null,
      data_mode: "REAL",
      flagged: true,
      peer_quality: 70,
      independent: true,
    },
  ],
  discounted_correlated_evidence: [
    {
      signal: "graph",
      group_id: "graph",
      display_name: "Relationship graph",
      weight: 0.08,
      state: "ASSESSABLE",
      polarity: "NEGATIVE_SIGNAL",
      raw_evidence_score: 95,
      confidence: 0.8,
      confidence_adjusted_score: 86,
      correlation_factor: 0.25,
      correlation_reason: "Graph/Overlap shared semantic signal",
      dependency_correlation_adjustment: 0.25,
      effective_contribution: 1.72,
      evidence_ids: ["ev:graph:1:relationship_graph:HYBRID:def"],
      source_ids: ["internal:test"],
      items: [],
      finding: "Similar works",
      support: "SIMILAR_TO",
      unavailable_reason: null,
      data_mode: "HYBRID",
      flagged: true,
      peer_quality: null,
      independent: false,
    },
  ],
  unavailable_evidence: [],
  not_assessable_evidence: [],
  conflicting_evidence: [
    {
      left_group: "Citizen / Jan-Sakshi",
      right_group: "Milestone",
      left_polarity: "NEGATIVE_SIGNAL",
      right_polarity: "POSITIVE_SIGNAL",
      summary: "Citizen reports incomplete while milestone indicates complete.",
    },
  ],
  evidence_contribution_breakdown: [],
  evidence_ids: ["ev:cost:1:allocation_cost_anomaly:HYBRID:abc"],
  ignored_duplicate_evidence_ids: [],
  explanation: "Investigation Priority: 78/100. Evidence Confidence: 74/100.",
  recommendation: "Inspect supporting documents before taking further action.",
  available_weight: 0.4,
  unavailable_weight: 0.6,
  evidence_coverage: 0.4,
  synthetic_disclosure: "A major contribution relies on HYBRID/TEST enrichment.",
  evidence_fingerprint: "abc",
  engine_version: "risk-fusion-v2",
  weight_note: "Prototype weights only.",
  note: "Investigation Priority is not a fraud probability.",
};

describe("RiskFusionV2Panel", () => {
  it("shows V2 priority, confidence, why, correlated, and conflicting evidence", () => {
    render(<RiskFusionV2Panel risk={baseRisk} />);
    expect(screen.getByText("78/100")).toBeInTheDocument();
    expect(screen.getByText("74/100")).toBeInTheDocument();
    expect(screen.getByText("WHY?")).toBeInTheDocument();
    expect(screen.getByText(/Graph\/Overlap shared semantic signal/)).toBeInTheDocument();
    expect(screen.getByText(/Citizen reports incomplete/)).toBeInTheDocument();
    expect(document.body.textContent?.toLowerCase()).not.toContain("fraud detected");
    expect(document.body.textContent?.toLowerCase()).not.toContain("fraud score");
    expect(screen.getAllByText(/not a fraud probability/i).length).toBeGreaterThan(0);
  });
});
