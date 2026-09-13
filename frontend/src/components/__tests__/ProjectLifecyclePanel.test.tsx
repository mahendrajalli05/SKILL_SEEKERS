import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ProjectLifecyclePanel } from "@/components/ProjectLifecyclePanel";
import type { ProjectLifecycleResponse } from "@/lib/types";

const baseLifecycle: ProjectLifecycleResponse = {
  project_id: 1,
  internal_project_id: "internal:test",
  scheme_id: "SVK-AP-000001",
  work_description: "Construction of community hall",
  constituency: "KURNOOL",
  category: "Normal/Others",
  requested_amount: 500000,
  data_mode: "HYBRID",
  lifecycle_state: "FUTURE",
  source_status: "Unsanctioned",
  current_stage: "PRIORITIZATION",
  planning_state: "PLANNING",
  completed_stages: ["FUTURE"],
  pending_stages: ["PRIORITIZATION"],
  timeline: [
    {
      stage: "FUTURE",
      status: "COMPLETED",
      label: "Future / proposed",
      available: true,
      href: "",
      note: null,
    },
    {
      stage: "PRIORITIZATION",
      status: "CURRENT",
      label: "Prioritization (Need & Impact)",
      available: true,
      href: "#need-impact",
      note: null,
    },
    {
      stage: "ONGOING",
      status: "NOT AVAILABLE",
      label: "Ongoing",
      available: false,
      href: null,
      note: "NOT AVAILABLE — this work is in the FUTURE / proposed workflow.",
    },
  ],
  evidence_summary: { count: 0, engines: [], modules: [], evidence_ids: [] },
  risk_summary: {
    appropriate: false,
    reason: "Need & Impact is the primary FUTURE workflow. Risk Fusion V2 is used for ONGOING and COMPLETED investigation.",
  },
  milestone_summary: null,
  need_impact_summary: {
    need_score: 72,
    impact_score: 61,
    priority_class: "HIGH PRIORITY",
    evidence_confidence: 54,
    unavailable_inputs: ["census population need"],
  },
  pce_summary: null,
  citizen_summary: null,
  geospatial_status: null,
  satellite_status: { available: false, status: "SATELLITE_UNAVAILABLE" },
  document_status: null,
  image_status: null,
  compliance_status: null,
  relationship_status: null,
  project_status_summary: {
    lifecycle_state: "FUTURE",
    source_status: "Unsanctioned",
    current_stage: "PRIORITIZATION",
    data_mode: "HYBRID",
    need_score: 72,
  },
  officer_decisions: [],
  checkpoint_actions: ["PRIORITIZE", "DEFER", "NEED_MORE_INFORMATION"],
  final_case_summary: null,
  recommendation: "HIGH PRIORITY",
  recommendation_rationale: "Priority recommendation only. Not a sanction.",
  unavailable_inputs: ["census population need"],
  automatic_sanction: false,
  automatic_payment: false,
  pfms_integrated: false,
  fraud_conclusion: false,
  engine_version: "lifecycle-orchestration-v1",
  governance_note:
    "SARVSAKSHI workflow state is an application lifecycle label. It is not an official MPLADS status.",
  workflow_label: "SARVSAKSHI workflow state",
  source_status_label: "Source status",
  is_synthetic: false,
  synthetic_label: null,
  explanation: "HYBRID lifecycle. Not a fraud finding.",
};

describe("ProjectLifecyclePanel", () => {
  it("highlights Future and shows Need & Impact for the future workflow", () => {
    render(
      <ProjectLifecyclePanel projectId={1} mode="HYBRID" lifecycle={baseLifecycle} />,
    );
    expect(screen.getByText(/Future \(current\)/)).toBeInTheDocument();
    expect(screen.getByText("SARVSAKSHI workflow state")).toBeInTheDocument();
    expect(screen.getByText("Source status")).toBeInTheDocument();
    expect(screen.getByText("Need Score")).toBeInTheDocument();
    expect(screen.getByText("does not sanction automatically", { exact: false })).toBeInTheDocument();
    expect(screen.queryByText(/fraud detected/i)).not.toBeInTheDocument();
  });

  it("shows INCONCLUSIVE completed summary when provided", () => {
    render(
      <ProjectLifecyclePanel
        projectId={2}
        mode="REAL"
        lifecycle={{
          ...baseLifecycle,
          lifecycle_state: "COMPLETED",
          current_stage: "FINAL_INVESTIGATION",
          planning_state: null,
          need_impact_summary: null,
          risk_summary: {
            appropriate: true,
            investigation_priority: 12,
            evidence_confidence: 40,
            recommended_action: "NEED_MORE_INFORMATION",
          },
          final_case_summary: {
            result: "INCONCLUSIVE",
            note: "INCONCLUSIVE because stored evidence is insufficient.",
          },
        }}
      />,
    );
    expect(screen.getByText(/Completed \(current\)/)).toBeInTheDocument();
    expect(screen.getByText("INCONCLUSIVE")).toBeInTheDocument();
    expect(screen.getByText("Investigation Priority")).toBeInTheDocument();
  });
});
