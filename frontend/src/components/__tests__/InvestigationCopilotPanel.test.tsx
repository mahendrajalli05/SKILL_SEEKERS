import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { InvestigationCopilotPanel } from "@/components/InvestigationCopilotPanel";

const context = {
  project_id: 11,
  internal_project_id: "internal:copilot:subject",
  scheme_id: "SVK-AP-000011",
  data_mode: "HYBRID",
  data_mode_notice:
    "This answer uses the HYBRID prototype enrichment for some fields. Those values are synthetic and are not official MPLADS records.",
  engines_present: ["cost"],
  evidence_count: 1,
  suggested_questions: [
    "Why is this project flagged?",
    "What evidence is strongest?",
    "Why is Time Intelligence inconclusive?",
    "Show comparable projects.",
    "What should I inspect next?",
    "Summarize Plan → Claim → Evidence.",
  ],
  session_id: "session-1",
  turns: [],
  limitations: [],
  governance_note: "AI recommends. Authorized officers decide.",
  engine_version: "investigation-copilot-v1",
  llm_provider: "deterministic",
};

const chat = {
  project_id: 11,
  internal_project_id: "internal:copilot:subject",
  scheme_id: "SVK-AP-000011",
  session_id: "session-1",
  question: "Why is this project flagged?",
  intent: "WHY_FLAGGED",
  answer: "ANSWER:\nInvestigation Priority is elevated.\n\nWHY:\nCost and overlap signals.",
  sections: {
    answer: "Investigation Priority is elevated.",
    why: "Cost and overlap signals.",
    evidence: "ev:cost:11:allocation_cost_anomaly:HYBRID:abc",
    missing: "Verified completion date is unavailable.",
    recommended_action: "REVIEW",
  },
  evidence_ids: ["ev:cost:11:allocation_cost_anomaly:HYBRID:abc"],
  source_refs: [
    { id: "SVK-AP-000011", kind: "project", label: "Scheme ID" },
    { id: "ev:cost:11:allocation_cost_anomaly:HYBRID:abc", kind: "evidence", label: "cost allocation_cost_anomaly" },
  ],
  data_mode: "HYBRID",
  data_mode_notice: context.data_mode_notice,
  limitations: [context.data_mode_notice],
  recommended_action: "REVIEW",
  observed_facts: [],
  derived_findings: [],
  unavailable: [],
  insufficient_evidence: false,
  hybrid_used: true,
  provider: "deterministic",
  used_llm: false,
  governance_note: "AI recommends. Authorized officers decide.",
  engine_version: "investigation-copilot-v1",
};

vi.mock("@/lib/api", () => ({
  fetchCopilotContext: vi.fn(),
  sendCopilotChat: vi.fn(),
}));

import { fetchCopilotContext, sendCopilotChat } from "@/lib/api";

describe("InvestigationCopilotPanel", () => {
  beforeEach(() => {
    vi.mocked(fetchCopilotContext).mockResolvedValue(context);
    vi.mocked(sendCopilotChat).mockResolvedValue(chat);
  });

  it("shows suggested questions, data mode, and grounded answer sources", async () => {
    const user = userEvent.setup();
    render(<InvestigationCopilotPanel projectId={11} mode="HYBRID" />);
    expect(await screen.findByText("INVESTIGATION COPILOT")).toBeInTheDocument();
    expect(screen.getByText(/HYBRID prototype enrichment/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Why is this project flagged?" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Why is this project high priority?" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "What evidence supports this?" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "What information is missing?" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Why is this project flagged?" }));
    expect(await screen.findByText(/Investigation Priority is elevated/)).toBeInTheDocument();
    expect(screen.getByText(/cost allocation_cost_anomaly/)).toBeInTheDocument();
    expect(screen.getByText("Recommended action:")).toBeInTheDocument();
    expect(screen.getByText("REVIEW")).toBeInTheDocument();
  });

  it("shows an insufficient-evidence state", async () => {
    vi.mocked(sendCopilotChat).mockResolvedValue({
      ...chat,
      insufficient_evidence: true,
      answer: "That information is not available in the current evidence.",
    });
    const user = userEvent.setup();
    render(<InvestigationCopilotPanel projectId={11} mode="HYBRID" />);
    await screen.findByText("INVESTIGATION COPILOT");
    await user.click(screen.getByRole("button", { name: "What evidence is strongest?" }));
    expect(await screen.findByText(/Insufficient evidence/)).toBeInTheDocument();
  });
});
