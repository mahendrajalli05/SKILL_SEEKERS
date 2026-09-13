import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EvidenceCard } from "@/components/EvidenceCard";
import type { EvidenceObject } from "@/lib/types";

const evidence: EvidenceObject = {
  evidence_id: "ev:cost:1:allocation_cost_anomaly:REAL:abc",
  project_id: 1,
  signal_type: "allocation_cost_anomaly",
  finding: "Allocation is within the peer range.",
  severity: "info",
  score: 12,
  confidence: 0.4,
  source_type: "mplads_project_record",
  source_ids: ["internal:test"],
  evidence_facts: [],
  explanation: "WHY NOT FLAGGED: allocation is close to the peer median.",
  engine_name: "cost",
  engine_version: "cost-peer-v1.1",
  created_at: "2026-09-10T00:00:00Z",
  data_mode: "REAL",
  provenance: {
    data_mode: "REAL",
    source_type: "mplads_project_record",
    notes: "Observed extract fields.",
  },
  disposition: "WHY_NOT_FLAGGED",
  status: "consistent",
  comparables: [],
};

describe("EvidenceCard", () => {
  it("shows finding, score, confidence, source, data mode, and explanation", () => {
    render(<EvidenceCard evidence={evidence} />);
    expect(screen.getByText("Allocation is within the peer range.")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText(/mplads_project_record/)).toBeInTheDocument();
    expect(screen.getAllByText("REAL").length).toBeGreaterThan(0);
    expect(screen.getByText(/WHY NOT FLAGGED/)).toBeInTheDocument();
  });

  it("labels HYBRID evidence as synthetic prototype enrichment", () => {
    render(
      <EvidenceCard
        evidence={{
          ...evidence,
          data_mode: "HYBRID",
          provenance: {
            data_mode: "HYBRID",
            source_type: "hybrid_enrichment",
            notes: "Synthetic enrichment.",
            enrichment_used: true,
          },
        }}
      />,
    );
    expect(screen.getByText(/SYNTHETIC prototype enrichment/)).toBeInTheDocument();
    expect(screen.getByText(/not official MPLADS data/)).toBeInTheDocument();
  });

  it("does not render a fake zero for NOT_ASSESSABLE evidence", () => {
    render(
      <EvidenceCard
        evidence={{
          ...evidence,
          score: null,
          disposition: "NOT_ASSESSABLE",
          finding: "Time Anomaly was not assessed.",
        }}
      />,
    );
    expect(screen.getByText("Not assessable")).toBeInTheDocument();
    expect(screen.getByText("NOT_ASSESSABLE")).toBeInTheDocument();
    expect(screen.queryByText("0")).toBeNull();
  });
});
