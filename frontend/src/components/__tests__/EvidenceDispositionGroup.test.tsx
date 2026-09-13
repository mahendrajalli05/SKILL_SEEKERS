import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EvidenceDispositionGroup } from "@/components/EvidenceDispositionGroup";
import type { EvidenceObject } from "@/lib/types";

function evidence(overrides: Partial<EvidenceObject>): EvidenceObject {
  return {
    evidence_id: "ev:1",
    project_id: 1,
    signal_type: "allocation_cost_anomaly",
    finding: "Finding",
    severity: "info",
    score: 10,
    confidence: 0.4,
    source_type: "mplads_project_record",
    source_ids: [],
    evidence_facts: [],
    explanation: "Explanation",
    engine_name: "cost",
    engine_version: "cost-peer-v1.1",
    created_at: null,
    data_mode: "REAL",
    provenance: { data_mode: "REAL", source_type: "mplads_project_record", notes: "" },
    disposition: "WHY_FLAGGED",
    status: "mismatch",
    comparables: [],
    ...overrides,
  };
}

describe("EvidenceDispositionGroup", () => {
  it("groups why flagged, why not flagged, inconclusive, and insufficient evidence", () => {
    render(
      <EvidenceDispositionGroup
        items={[
          evidence({ evidence_id: "a", finding: "Flagged cost", disposition: "WHY_FLAGGED" }),
          evidence({ evidence_id: "b", finding: "Not flagged overlap", disposition: "WHY_NOT_FLAGGED" }),
          evidence({ evidence_id: "c", finding: "Inconclusive time", disposition: "INCONCLUSIVE" }),
          evidence({
            evidence_id: "d",
            finding: "Not assessable compliance",
            disposition: "NOT_ASSESSABLE",
            score: null,
          }),
        ]}
      />,
    );
    expect(screen.getByText("WHY FLAGGED")).toBeInTheDocument();
    expect(screen.getByText("WHY NOT FLAGGED")).toBeInTheDocument();
    expect(screen.getAllByText("INCONCLUSIVE").length).toBeGreaterThan(0);
    expect(screen.getByText("INSUFFICIENT EVIDENCE")).toBeInTheDocument();
    expect(screen.getByText("Flagged cost")).toBeInTheDocument();
    expect(screen.getByText("Not flagged overlap")).toBeInTheDocument();
  });
});
