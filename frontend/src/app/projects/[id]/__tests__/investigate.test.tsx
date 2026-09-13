import type { ReactNode } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { sampleProject, sampleGraph, graphEvidenceObject } from "@/test/graphFixtures";
import type { ProjectRiskV2Response } from "@/lib/types";

const intel = vi.fn();

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "232" }),
  useRouter: () => ({ replace: vi.fn() }),
  useSearchParams: () => new URLSearchParams("mode=hybrid"),
}));

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock("@/lib/useProjectIntelligence", () => ({
  useProjectIntelligence: () => intel(),
}));

vi.mock("@/components/NeedImpactPanel", () => ({
  NeedImpactPanel: () => <p>Need & Impact panel</p>,
}));
vi.mock("@/components/MilestoneAdvisorPanel", () => ({
  MilestoneAdvisorPanel: () => <p>Milestones panel</p>,
}));
vi.mock("@/components/JanSakshiPanel", () => ({
  JanSakshiPanel: () => <p>Citizen panel</p>,
}));
vi.mock("@/components/PlanClaimEvidencePanel", () => ({
  PlanClaimEvidencePanel: () => <p>PCE panel</p>,
}));
vi.mock("@/components/DocumentsBlueprintPanel", () => ({
  DocumentsBlueprintPanel: () => <p>Documents panel</p>,
}));
vi.mock("@/components/ImageEvidencePanel", () => ({
  ImageEvidencePanel: () => <p>Images panel</p>,
}));
vi.mock("@/components/ImageForensicsPanel", () => ({
  ImageForensicsPanel: () => <p>Forensics panel</p>,
}));
vi.mock("@/components/GeospatialEvidencePanel", () => ({
  GeospatialEvidencePanel: () => <p>Geospatial panel</p>,
}));
vi.mock("@/components/SatelliteRemoteSensingPanel", () => ({
  SatelliteRemoteSensingPanel: () => <p>Satellite panel</p>,
}));
vi.mock("@/components/InvestigationCopilotPanel", () => ({
  InvestigationCopilotPanel: () => <p>INVESTIGATION COPILOT</p>,
}));
vi.mock("@/components/RelationshipGraphPanel", () => ({
  RelationshipGraphPanel: () => <p>RELATIONSHIP GRAPH</p>,
}));

import InvestigatePage from "@/app/projects/[id]/investigate/page";

function ok<T>(data: T) {
  return { data, error: null, loading: false };
}

const riskV2: ProjectRiskV2Response = {
  project_id: 232,
  internal_project_id: "internal:232",
  investigation_priority: 78,
  investigation_priority_0_100: 78,
  raw_risk: 78,
  evidence_confidence: 74,
  priority_band: "HIGH",
  explanation_type: "WHY_FLAGGED",
  explanation_types: ["WHY_FLAGGED"],
  recommended_action: "INSPECT",
  data_mode: "HYBRID",
  contributing_signals: [],
  unavailable_signals: [],
  evidence_ids: [],
  explanation: "Investigation Priority: 78/100.",
  recommendation: "Inspect supporting documents.",
  available_signal_weight: 0.4,
  unavailable_signal_weight: 0.6,
  evidence_coverage: 0.4,
  engine_version: "risk-fusion-v2",
  weight_note: "Prototype weights only.",
  note: "Investigation Priority is not a fraud probability.",
  risk_class: "HIGH",
  contributing_evidence_groups: [],
  independent_evidence_groups: [],
  discounted_correlated_evidence: [],
  unavailable_evidence: [],
  not_assessable_evidence: [],
  conflicting_evidence: [],
  evidence_contribution_breakdown: [],
  ignored_duplicate_evidence_ids: [],
  available_weight: 0.4,
  unavailable_weight: 0.6,
  synthetic_disclosure: null,
  evidence_fingerprint: "abc",
};

function intelValue() {
  return {
    project: ok(sampleProject({ data_mode: "HYBRID", has_hybrid_enrichment: true })),
    risk: ok(null),
    riskV2: ok(riskV2),
    lifecycle: ok(null),
    evidence: ok({
      project_id: 232,
      internal_project_id: "internal:232",
      items: [graphEvidenceObject()],
      note: "",
    }),
    cost: ok(null),
    time: ok(null),
    overlap: ok(null),
    compliance: ok(null),
    graph: ok(sampleGraph()),
    decisions: [],
    decisionError: null,
    submitting: false,
    recordDecision: vi.fn(),
    recordPlanningDecision: vi.fn(),
    reloadEvidence: vi.fn(),
  };
}

describe("Investigation Workspace polish", () => {
  beforeEach(() => {
    intel.mockReturnValue(intelValue());
  });

  it("shows summary scores and lazy tabs", async () => {
    const user = userEvent.setup();
    render(<InvestigatePage />);
    expect(screen.getByRole("heading", { name: "Investigation Workspace" })).toBeInTheDocument();
    expect(screen.getAllByText("78/100").length).toBeGreaterThan(0);
    expect(screen.getAllByText("74/100").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Inspect").length).toBeGreaterThan(0);
    expect(screen.getByText("WHY?")).toBeInTheDocument();
    expect(screen.getByText("INVESTIGATION COPILOT")).toBeInTheDocument();
    expect(screen.queryByText("Documents panel")).toBeNull();
    await user.click(screen.getByRole("tab", { name: "Copilot" }));
    expect(screen.getByText("INVESTIGATION COPILOT")).toBeInTheDocument();
    await user.click(screen.getByRole("tab", { name: "Evidence" }));
    expect(screen.getByText("WHY FLAGGED")).toBeInTheDocument();
    expect(document.body.textContent?.toLowerCase()).not.toContain("fraud confirmed");
  });

  it("shows a loading state", () => {
    intel.mockReturnValue({
      ...intelValue(),
      project: { data: null, error: null, loading: true },
    });
    render(<InvestigatePage />);
    expect(screen.getByText("Loading investigation workspace…")).toBeInTheDocument();
  });
});
