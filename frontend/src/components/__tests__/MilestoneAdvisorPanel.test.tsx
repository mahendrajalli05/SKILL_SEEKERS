import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MilestoneAdvisorPanel } from "@/components/MilestoneAdvisorPanel";
import type { MilestoneRecord, ProjectMilestonesResponse } from "@/lib/types";

const current: MilestoneRecord = {
  milestone_id: 9,
  project_id: 11,
  internal_project_id: "internal:milestone:subject",
  milestone_number: 1,
  milestone_name: "M1",
  description: null,
  planned_amount: 200000,
  cumulative_amount: 200000,
  remaining_planned_amount: 0,
  target_date: "2024-06-01",
  completion_claimed: true,
  claimed_progress: 100,
  claimed_expenditure: 190000,
  status: "UNDER_REVIEW",
  data_mode: "HYBRID",
  synthetic: true,
  provenance: {},
  recommendation: "PROCEED",
  evidence_status: "SUPPORTED",
  amounts: {
    planned_amount: 200000,
    cumulative_amount: 200000,
    claimed_expenditure: 190000,
    remaining_planned_amount: 0,
    planned_amount_available: true,
    cumulative_amount_available: true,
    claimed_expenditure_available: true,
    remaining_available: true,
    claimed_expenditure_synthetic: true,
    note: "SYNTHETIC prototype value.",
  },
  progress: {
    claimed_progress: 100,
    evidence_supported_progress: 97,
    planned_progress: 25,
    schedule_mismatch: false,
    schedule_note: null,
    claimed_progress_available: true,
    evidence_supported_available: true,
    planned_progress_available: true,
  },
  assessment: {
    recommendation: "PROCEED",
    pce_result: "CONSISTENT",
    evidence_status: "SUPPORTED",
    supporting_evidence: ["Plan → Claim → Evidence is CONSISTENT."],
    conflicting_evidence: [],
    missing_evidence: [],
    intelligence_signals: ["time: schedule within peer range"],
    independent_concerns: [],
    explanation:
      "Recommendation is PROCEED because the milestone claim is supported. Milestone recommendation only. Authorized officials make the final administrative decision. SARVSAKSHI does not release funds.",
    evidence_confidence: 0.72,
    funds_released: false,
    payment_executed: false,
    automatic_sanction: false,
    pfms_integrated: false,
  },
  officer_action: null,
  officer_reason: null,
  officer_acted_at: null,
  decisions: [],
  work_description: "Construction of community hall",
  investigation_priority: 18,
  evidence_confidence: 58,
  hybrid_notice:
    "Prototype simulation: some execution, financial, location, or milestone fields are synthetic and are not official MPLADS records.",
  enrichment_used: true,
  funds_released: false,
  payment_executed: false,
  automatic_sanction: false,
  pfms_integrated: false,
  engine_version: "milestone-advisor-v1",
  engine_name: "milestone",
  governance_note:
    "Milestone recommendation only. Authorized officials make the final administrative decision. SARVSAKSHI does not release funds.",
  no_payment_note: "No payment was executed. This prototype does not integrate with PFMS and does not release or sanction funds.",
};

const payload: ProjectMilestonesResponse = {
  project_id: 11,
  internal_project_id: "internal:milestone:subject",
  work_description: "Construction of community hall",
  data_mode: "HYBRID",
  current_milestone_id: 9,
  current_milestone_name: "M1",
  current_recommendation: "PROCEED",
  current_milestone: current,
  items: [current],
  timeline: [
    {
      slot: "M1",
      milestone_id: 9,
      milestone_number: 1,
      milestone_name: "M1",
      status: "UNDER_REVIEW",
      planned_date: "2024-06-01",
      claim: "completion claimed",
      evidence: "SUPPORTED",
      result: "PROCEED",
      officer_action: null,
      recorded: true,
    },
    {
      slot: "M2",
      milestone_id: null,
      milestone_number: 2,
      milestone_name: "M2",
      status: null,
      planned_date: null,
      claim: null,
      evidence: "not recorded",
      result: null,
      officer_action: null,
      recorded: false,
    },
    {
      slot: "M3",
      milestone_id: null,
      milestone_number: 3,
      milestone_name: "M3",
      status: null,
      planned_date: null,
      claim: null,
      evidence: "not recorded",
      result: null,
      officer_action: null,
      recorded: false,
    },
    {
      slot: "M4",
      milestone_id: null,
      milestone_number: 4,
      milestone_name: "M4",
      status: null,
      planned_date: null,
      claim: null,
      evidence: "not recorded",
      result: null,
      officer_action: null,
      recorded: false,
    },
    {
      slot: "COMPLETION",
      milestone_id: null,
      milestone_number: null,
      milestone_name: "COMPLETION",
      status: null,
      planned_date: null,
      claim: null,
      evidence: null,
      result: null,
      officer_action: null,
      recorded: false,
    },
  ],
  investigation_priority: 18,
  evidence_confidence: 58,
  hybrid_notice: current.hybrid_notice,
  enrichment_used: true,
  funds_released: false,
  payment_executed: false,
  automatic_sanction: false,
  pfms_integrated: false,
  engine_version: "milestone-advisor-v1",
  engine_name: "milestone",
  governance_note: current.governance_note,
  no_payment_note: current.no_payment_note,
  allowed_officer_actions: ["PROCEED", "HOLD", "INSPECT", "NEED_MORE_INFORMATION"],
  disallowed: ["payment_release", "pfms_payment", "automatic_sanction", "fraud_finding"],
};

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => payload,
    }),
  );
});

describe("MilestoneAdvisorPanel", () => {
  it("shows recommendation, timeline, why, officer actions, and governance wording", async () => {
    render(<MilestoneAdvisorPanel projectId={11} mode="HYBRID" />);
    expect(await screen.findByText("Construction of community hall")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Milestones" })).toBeInTheDocument();
    expect(screen.getAllByText("PROCEED").length).toBeGreaterThan(0);
    expect(screen.getByText(/Prototype simulation/)).toBeInTheDocument();
    expect(screen.getAllByText("M1").length).toBeGreaterThan(0);
    expect(screen.getByText("COMPLETION")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "WHY?" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Proceed" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Hold" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Inspect" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Need more information" })).toBeInTheDocument();
    expect(document.body.textContent?.toLowerCase()).not.toContain("fraud");
    expect(document.body.textContent?.toLowerCase()).toContain("does not release funds");
    expect(document.body.textContent?.toLowerCase()).toContain("does not integrate with pfms");
  });

  it("records an officer action without implying payment release", async () => {
    const user = userEvent.setup();
    render(<MilestoneAdvisorPanel projectId={11} mode="HYBRID" />);
    await screen.findByRole("button", { name: "Hold" });
    await user.click(screen.getByRole("button", { name: "Hold" }));
    expect(globalThis.fetch).toHaveBeenCalled();
    expect(document.body.textContent?.toLowerCase()).not.toContain("funds released");
  });
});
