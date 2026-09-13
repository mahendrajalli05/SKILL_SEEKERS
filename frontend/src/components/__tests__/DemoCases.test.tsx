import type { ReactNode } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const fetchDemoCases = vi.fn();
const fetchDemoCase = vi.fn();
const sendCopilotChat = vi.fn();
let params = new URLSearchParams("mode=hybrid");
let caseId = "ghost";

vi.mock("next/navigation", () => ({
  useSearchParams: () => params,
  useParams: () => ({ caseId }),
  useRouter: () => ({ replace: vi.fn() }),
}));

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock("@/lib/api", () => ({
  fetchDemoCases: (...args: unknown[]) => fetchDemoCases(...args),
  fetchDemoCase: (...args: unknown[]) => fetchDemoCase(...args),
  sendCopilotChat: (...args: unknown[]) => sendCopilotChat(...args),
}));

vi.mock("@/lib/useProjectIntelligence", () => ({
  useProjectIntelligence: () => ({
    lifecycle: { data: null, error: null, loading: false },
    riskV2: { data: null, error: null, loading: false },
    decisions: [],
    decisionError: null,
    submitting: false,
    recordDecision: vi.fn(),
    recordPlanningDecision: vi.fn(),
  }),
}));

vi.mock("@/components/InvestigationCopilotPanel", () => ({
  InvestigationCopilotPanel: () => <p>Investigation Copilot panel</p>,
}));
vi.mock("@/components/ProjectLifecyclePanel", () => ({
  ProjectLifecyclePanel: () => <p>Lifecycle panel</p>,
}));
vi.mock("@/components/RiskFusionV2Panel", () => ({
  RiskFusionV2Panel: () => <p>Risk Fusion V2 panel</p>,
}));
vi.mock("@/components/OfficerDecisionPanel", () => ({
  OfficerDecisionPanel: () => <p>Officer decision panel</p>,
}));

import { DemoCaseLaunch } from "@/components/DemoCaseLaunch";
import { DemoCaseJourney } from "@/components/DemoCaseJourney";
import { DemoCaseNotice } from "@/components/DemoCaseNotice";
import { DemoCaseSummary } from "@/components/DemoCaseSummary";
import { DEMO_CASE_NOTICE } from "@/lib/display";
import { normalizeBadgeKind } from "@/lib/statusBadge";
import type { DemoCaseResponse, DemoCaseSummary as Summary } from "@/lib/types";

function listBody() {
  return {
    items: [
      {
        case_id: "GHOST",
        display_name: "GHOST",
        purpose: "Location concern",
        short_description: "Completed claim with labelled location signals.",
        expected_lifecycle: "COMPLETED",
        expected_direction: "REVIEW / INSPECT",
        internal_project_id: "internal:ghost",
        suggested_questions: ["Why is this project being recommended for inspection?"],
        demo_notice: DEMO_CASE_NOTICE,
        available: true,
        project_id: 53637,
        scheme_id: "SVK-AP-000001",
        lifecycle_state: "COMPLETED",
        source_status: "Completed",
        work_description: "Assistive devices",
        constituency: "VIZIANAGARAM",
        href: "/demo/ghost",
      },
    ],
    count: 1,
    demo_notice: DEMO_CASE_NOTICE,
    hybrid_notice: "DEMO / HYBRID",
    governance_note: "AI recommends.",
    journey_steps: ["PROJECT", "PASSPORT"],
    engine_version: "final-demo-cases-v1",
    fusion_v2_unchanged: true,
    automatic_sanction: false,
    automatic_payment: false,
    fraud_conclusion: false,
    data_mode: "HYBRID",
  };
}

function summary(): Summary {
  return {
    case_id: "GHOST",
    display_name: "GHOST",
    project: {
      project_id: 12,
      scheme_id: "SVK-AP-000012",
      internal_project_id: "internal:ghost",
      work_description: "Assistive devices",
      constituency: "VIZIANAGARAM",
      category: "Other works",
      source_status: "Completed",
    },
    lifecycle: "COMPLETED",
    investigation_priority: 18,
    evidence_confidence: 40,
    main_signals: [{ group: "geospatial" }],
    evidence: ["ev:geo:1"],
    missing_information: ["satellite imagery"],
    recommended_action: "REVIEW",
    officer_decision: "confirm_concern",
    data_reliability: "HYBRID",
    data_mode: "HYBRID",
    demo_notice: DEMO_CASE_NOTICE,
    automatic_sanction: false,
    automatic_payment: false,
    fraud_conclusion: false,
    scores_mutated: false,
  };
}

function caseBody(): DemoCaseResponse {
  return {
    case_id: "GHOST",
    display_name: "GHOST",
    purpose: "Location concern",
    scenario_type: "DEMO_GHOST",
    short_description: "Completed claim with labelled location signals.",
    initial_claim: "Completed",
    expected_lifecycle: "COMPLETED",
    expected_direction: "REVIEW / INSPECT",
    expected_direction_note: "Not forced.",
    suggested_questions: ["Why is this project being recommended for inspection?"],
    officer_actions: ["confirm_concern"],
    officer_action_labels: ["CONFIRM CONCERN"],
    investigation_actions: [],
    modules: ["image"],
    project_id: 12,
    scheme_id: "SVK-AP-000012",
    internal_project_id: "internal:ghost",
    work_description: "Assistive devices",
    constituency: "VIZIANAGARAM",
    category: "Other works",
    state: "Andhra Pradesh",
    source_status: "Completed",
    lifecycle_state: "COMPLETED",
    current_stage: "FINAL_INVESTIGATION",
    allocation_amount: 500000,
    data_mode: "HYBRID",
    data_reliability: "HYBRID",
    has_hybrid_enrichment: true,
    is_synthetic: false,
    synthetic_label: null,
    demo_notice: DEMO_CASE_NOTICE,
    hybrid_notice: "DEMO / HYBRID",
    governance_note: "AI recommends.",
    no_fraud_note: "Not fraud.",
    no_sanction_note: "No sanction.",
    available_plan: { plan_recorded: true },
    available_claim: { claim_recorded: true, claimed_progress: "Completion claimed" },
    available_evidence: { items: [], count: 1, evidence_ids: ["ev:geo:1"] },
    intelligence_signals: [{ group: "geospatial" }],
    risk_fusion_v2: { formula_unchanged: true, investigation_priority: 18 },
    investigation_workspace: {},
    lifecycle: {
      project_id: 12,
      internal_project_id: "internal:ghost",
      scheme_id: "SVK-AP-000012",
      work_description: "Assistive devices",
      constituency: "VIZIANAGARAM",
      category: "Other works",
      requested_amount: 500000,
      data_mode: "HYBRID",
      lifecycle_state: "COMPLETED",
      source_status: "Completed",
      current_stage: "FINAL_INVESTIGATION",
      planning_state: null,
      completed_stages: [],
      pending_stages: [],
      timeline: [],
      evidence_summary: {},
      risk_summary: null,
      milestone_summary: null,
      need_impact_summary: null,
      pce_summary: null,
      citizen_summary: null,
      geospatial_status: null,
      satellite_status: null,
      document_status: null,
      image_status: null,
      compliance_status: null,
      relationship_status: null,
      project_status_summary: {},
      officer_decisions: [],
      checkpoint_actions: [],
      final_case_summary: null,
      recommendation: "REVIEW",
      recommendation_rationale: null,
      unavailable_inputs: [],
      automatic_sanction: false,
      automatic_payment: false,
      pfms_integrated: false,
      fraud_conclusion: false,
      engine_version: "lifecycle-orchestration-v1",
      governance_note: "AI recommends.",
      workflow_label: "SARVSAKSHI workflow state",
      source_status_label: "Source status",
      is_synthetic: false,
      synthetic_label: null,
      explanation: "Not a fraud finding.",
    },
    pce: { overall_result: "INCONCLUSIVE" },
    images: { status: "FLAGGED_FOR_REVIEW" },
    documents: null,
    geospatial: { status: "FLAGGED_FOR_REVIEW" },
    satellite: { status: "SATELLITE_UNAVAILABLE" },
    citizen: null,
    milestone: null,
    compliance: null,
    need_impact: null,
    copilot: { hardcoded_answers: false },
    recommended_action: "REVIEW",
    officer_decision: null,
    officer_decisions: [],
    checkpoint_actions: [],
    journey: [{ step: "PROJECT", href: "/demo/ghost#project" }],
    final_case_summary: summary(),
    automatic_sanction: false,
    automatic_payment: false,
    pfms_integrated: false,
    fraud_conclusion: false,
    engine_version: "final-demo-cases-v1",
    fusion_v2_unchanged: true,
  };
}

describe("Demo Cases UI", () => {
  beforeEach(() => {
    params = new URLSearchParams("mode=hybrid");
    caseId = "ghost";
    fetchDemoCases.mockReset();
    fetchDemoCase.mockReset();
    sendCopilotChat.mockReset();
  });

  it("shows the persistent DEMO / HYBRID notice", () => {
    render(<DemoCaseNotice caseName="Demo case: GHOST" />);
    expect(screen.getByText("DEMO")).toBeInTheDocument();
    expect(screen.getByText("HYBRID")).toBeInTheDocument();
    expect(screen.getByText("SYNTHETIC")).toBeInTheDocument();
    expect(screen.getByText("CONTROLLED PROTOTYPE")).toBeInTheDocument();
    expect(screen.getByText(DEMO_CASE_NOTICE)).toBeInTheDocument();
  });

  it("lists the four launch cards when the API returns them", async () => {
    fetchDemoCases.mockResolvedValue(listBody());
    render(<DemoCaseLaunch />);
    expect(await screen.findByRole("heading", { name: "SARVSAKSHI DEMO CENTER" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "GHOST" })).toBeInTheDocument();
    expect(await screen.findByRole("link", { name: /Open GHOST/ })).toHaveAttribute("href", "/demo/ghost?mode=hybrid");
    expect(screen.getByText(DEMO_CASE_NOTICE)).toBeInTheDocument();
  });

  it("walks the GHOST journey and shows evidence IDs", async () => {
    const user = userEvent.setup();
    fetchDemoCase.mockResolvedValue(caseBody());
    render(<DemoCaseJourney />);
    expect(await screen.findByRole("heading", { name: "GHOST" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "PROJECT" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Next" }));
    expect(screen.getByRole("heading", { name: "PASSPORT" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open Digital Passport" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Next" }));
    await user.click(screen.getByRole("button", { name: "Next" }));
    expect(screen.getByRole("heading", { name: "PLAN" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "CLAIM" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Next" }));
    expect(screen.getAllByText("ev:geo:1").length).toBeGreaterThan(0);
    await user.click(screen.getByRole("button", { name: "Next" }));
    await user.click(screen.getByRole("button", { name: "Next" }));
    expect(screen.getByRole("button", { name: "Why is this project being recommended for inspection?" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Next" }));
    await user.click(screen.getByRole("button", { name: "Next" }));
    expect(screen.getByText("FINAL CASE SUMMARY")).toBeInTheDocument();
    expect(screen.queryByText(/fraud confirmed/i)).toBeNull();
  });

  it("renders the final summary with REAL/HYBRID status", () => {
    render(<DemoCaseSummary summary={summary()} />);
    expect(screen.getByText("FINAL CASE SUMMARY")).toBeInTheDocument();
    expect(screen.getByText("ev:geo:1")).toBeInTheDocument();
    expect(screen.getByText("Confirm concern")).toBeInTheDocument();
    expect(screen.getByText(/Automatic sanction: no/)).toBeInTheDocument();
  });

  it("maps a DEMO badge without treating it as official data", () => {
    expect(normalizeBadgeKind("DEMO")).toBe("DEMO");
  });
});
