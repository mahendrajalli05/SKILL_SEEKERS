import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import AssessNewProjectPage from "@/app/assess-new-project/page";
import type { NewProjectAssessResponse } from "@/lib/types";

const payload: NewProjectAssessResponse = {
  assessment_kind: "NEW_PROJECT_ASSESSMENT",
  is_new_project: true,
  project_id: null,
  data_mode: "REAL",
  ml: {
    cost: {
      model_name: "cost-anomaly-v1",
      model_version: "cost-anomaly-v1-abc",
      model_type: "IsolationForest",
      training_mode: "REAL",
      training_data_hash: "abc",
      feature_schema_version: "cost-features-v1",
      created_at: "2026-09-10T00:00:00+00:00",
      status: "SCORED",
      ml_anomaly_score: 40,
      decision_label: "WITHIN_TRAINING_DISTRIBUTION",
      feature_availability: {
        available: ["allocation_amount", "category"],
        missing: [],
        unseen: [],
        unsupported: [],
        coverage: 0.8,
      },
      feature_values: {},
      contributions: [],
      explanation: "The unsupervised model did not place this proposal in the upper tail. Not a fraud probability.",
      limitations: ["Cost Intelligence V1.1 remains the authoritative interpretable peer baseline."],
      data_mode: "REAL",
      fraud_probability: null,
    },
    time: {
      model_name: "time-anomaly-v1",
      model_version: null,
      model_type: "IsolationForest",
      training_mode: "HYBRID_TEST",
      training_data_hash: null,
      feature_schema_version: null,
      created_at: null,
      status: "INCONCLUSIVE",
      ml_anomaly_score: null,
      decision_label: "INCONCLUSIVE",
      feature_availability: {
        available: [],
        missing: ["execution_start_date"],
        unseen: [],
        unsupported: [],
        coverage: 0,
      },
      feature_values: {},
      contributions: [],
      explanation: "INCONCLUSIVE: REAL MPLADS records have no verified execution dates.",
      limitations: [],
      data_mode: "REAL",
      fraud_probability: null,
    },
    error: null,
  },
  cost_v1_1: {
    outcome: "WITHIN_PEER_RANGE",
    cost_anomaly_score: 12,
    explanation: "Not flagged as an Allocation Cost Anomaly.",
  },
  time_v1: { explanation: "Insufficient execution timing." },
  overlap_v1: { outcome: "NOT_LINKED", explanation: "No potential overlap above the review flag." },
  compliance_v1: { status: "INCONCLUSIVE", explanation: "Most rules are not assessable on REAL fields." },
  risk_fusion_v2: {
    available: false,
    investigation_priority: null,
    evidence_confidence: null,
    recommended_action: null,
    reason: "A new project that has not been recorded has no historical evidence to fuse.",
  },
  limitations: ["ML anomaly scores are unsupervised distributional signals."],
  fraud_probability: null,
  automatic_sanction: false,
  automatic_payment: false,
  pfms_integrated: false,
};

vi.mock("@/lib/api", () => ({
  assessNewProject: vi.fn(async () => payload),
}));

describe("Assess New Project page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("submits the assessment form and shows ML plus frozen engine signals", async () => {
    const user = userEvent.setup();
    render(<AssessNewProjectPage />);
    expect(screen.getByText("NEW PROJECT ASSESSMENT")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Assess" }));
    expect(await screen.findByText(/Isolation Forest/i)).toBeInTheDocument();
    expect(screen.getByText("Cost signal (V1.1)")).toBeInTheDocument();
    expect(screen.getByText("Overlap signal")).toBeInTheDocument();
    expect(screen.getByText("Compliance")).toBeInTheDocument();
    expect(
      screen.getByText(/no historical evidence to fuse/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/not stored project evidence/i)).toBeInTheDocument();
    expect(screen.queryByText(/fraud confirmed/i)).toBeNull();
  });
});
