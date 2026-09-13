import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { createProjectMlEvidence } = vi.hoisted(() => ({
  createProjectMlEvidence: vi.fn(),
}));

vi.mock("@/lib/api", () => ({
  createProjectMlEvidence,
}));

import { EvidenceCard } from "@/components/EvidenceCard";
import { MlEvidencePanel } from "@/components/MlEvidencePanel";
import type { EvidenceObject } from "@/lib/types";

function evidence(overrides: Partial<EvidenceObject> = {}): EvidenceObject {
  return {
    evidence_id: "ev:ml:1:ML_ANOMALY_SIGNAL:REAL:abc",
    project_id: 1,
    signal_type: "ML_ANOMALY_SIGNAL",
    finding: "ELEVATED_ANOMALY_SIGNAL: unsupervised Isolation Forest placed this work in the upper tail.",
    severity: "watch",
    score: 91,
    confidence: 0.8,
    source_type: "ml_model",
    source_ids: ["internal:1"],
    evidence_facts: [
      { key: "model_name", value: "cost-anomaly-v1", source: "ml", kind: "DERIVED", statement: null },
      { key: "model_version", value: "cost-anomaly-v1-9d0c62e3b384", source: "ml", kind: "DERIVED", statement: null },
      { key: "feature_schema_version", value: "cost-features-v1", source: "ml", kind: "DERIVED", statement: null },
      { key: "training_data_hash", value: "abc123", source: "ml", kind: "DERIVED", statement: null },
      { key: "training_mode", value: "REAL", source: "ml", kind: "DERIVED", statement: null },
      { key: "ml_anomaly_score", value: 91, source: "ml", kind: "DERIVED", statement: null },
      {
        key: "feature_availability",
        value: { available: ["log_allocation", "freq_category"], missing: [], unseen: [], unsupported: [], coverage: 0.8 },
        source: "ml",
        kind: "DERIVED",
        statement: null,
      },
      { key: "limitations", value: ["Not fused into Investigation Priority."], source: "ml", kind: "DERIVED", statement: null },
    ],
    explanation: "Allocation is unusual relative to the training distribution.",
    engine_name: "ml",
    engine_version: "cost-anomaly-v1-9d0c62e3b384",
    created_at: null,
    data_mode: "REAL",
    provenance: { data_mode: "REAL", source_type: "ml_model", notes: "ML model source." },
    disposition: "WHY_FLAGGED",
    status: "mismatch",
    comparables: [],
    ...overrides,
  };
}

describe("ML evidence UI", () => {
  beforeEach(() => {
    createProjectMlEvidence.mockReset();
  });

  it("shows ML provenance separately from evidence confidence", () => {
    render(<EvidenceCard evidence={evidence()} />);
    expect(screen.getByText(/ML anomaly signal, not fraud confirmation/i)).toBeInTheDocument();
    expect(screen.getByText("ML anomaly score")).toBeInTheDocument();
    expect(screen.getByText("Evidence confidence")).toBeInTheDocument();
    expect(screen.getByText(/cost-anomaly-v1/)).toBeInTheDocument();
    expect(screen.getByText("cost-features-v1")).toBeInTheDocument();
    expect(screen.getByText("abc123")).toBeInTheDocument();
    expect(screen.getByText(/log_allocation/)).toBeInTheDocument();
    expect(document.body.textContent?.toLowerCase()).not.toContain("fraud confirmed");
  });

  it("can generate stored ML evidence", async () => {
    createProjectMlEvidence.mockResolvedValue({
      evidence_id: "ev:ml:1:ML_ANOMALY_SIGNAL:REAL:new",
      assessment_kind: "PROJECT_STORED_EVIDENCE",
    });
    const onCreated = vi.fn();
    render(<MlEvidencePanel projectId={7} mode="REAL" items={[]} onCreated={onCreated} />);
    expect(screen.getByText("ML Evidence")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Generate ML evidence" }));
    expect(await screen.findByText(/Stored ev:ml:1:ML_ANOMALY_SIGNAL:REAL:new/)).toBeInTheDocument();
    expect(createProjectMlEvidence).toHaveBeenCalledWith(7, { data_mode: "REAL" });
    expect(onCreated).toHaveBeenCalled();
  });
});
