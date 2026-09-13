import type { ReactNode } from "react";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { sampleProject, sampleGraph, graphEvidenceObject } from "@/test/graphFixtures";
import type { ProjectRiskResponse, ProjectRiskV2Response } from "@/lib/types";

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
vi.mock("@/components/CitizenEvidenceSummary", () => ({
  CitizenEvidenceSummary: () => <p>Jan-Sakshi summary</p>,
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
vi.mock("@/components/GeospatialEvidencePanel", () => ({
  GeospatialEvidencePanel: () => <p>Geospatial panel</p>,
}));
vi.mock("@/components/SatelliteRemoteSensingPanel", () => ({
  SatelliteRemoteSensingPanel: () => <p>Satellite panel</p>,
}));

import ProjectPassportPage from "@/app/projects/[id]/page";

function ok<T>(data: T) {
  return { data, error: null, loading: false };
}

const risk: ProjectRiskResponse = {
  project_id: 232,
  internal_project_id: "internal:232",
  investigation_priority: 36,
  investigation_priority_0_100: 36,
  raw_risk: 36,
  evidence_confidence: 40,
  priority_band: "MEDIUM",
  explanation_type: "WHY_FLAGGED",
  explanation_types: ["WHY_FLAGGED"],
  recommended_action: "REVIEW",
  data_mode: "HYBRID",
  contributing_signals: [],
  unavailable_signals: [],
  evidence_ids: [],
  explanation: "Review ranking only.",
  recommendation: "Review",
  available_signal_weight: 0.4,
  unavailable_signal_weight: 0.6,
  evidence_coverage: 0.4,
  engine_version: "risk-fusion-v1.1",
  weight_note: "Prototype weights only.",
  note: "Investigation Priority is not a fraud probability.",
};

const riskV2: ProjectRiskV2Response = {
  ...risk,
  investigation_priority: 36,
  investigation_priority_0_100: 36,
  evidence_confidence: 40,
  risk_class: "MEDIUM",
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
  engine_version: "risk-fusion-v2",
};

function intelValue() {
  return {
    project: ok(sampleProject({ has_hybrid_enrichment: true, hybrid_notice: null, data_mode: "HYBRID" })),
    risk: ok(risk),
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

describe("Project Digital Passport polish", () => {
  beforeEach(() => {
    intel.mockReturnValue(intelValue());
  });

  it("shows identity, data mode, lifecycle, and named sections", () => {
    render(<ProjectPassportPage />);
    expect(screen.getByRole("heading", { name: "Project Digital Passport" })).toBeInTheDocument();
    expect(screen.getAllByText("SVK-AP-000232").length).toBeGreaterThan(0);
    expect(screen.getAllByText("internal:232").length).toBeGreaterThan(0);
    expect(screen.getAllByText("HYBRID DEMO").length).toBeGreaterThan(0);
    expect(screen.getByText(/Prototype simulation/)).toBeInTheDocument();
    expect(screen.getByText("PROJECT IDENTITY")).toBeInTheDocument();
    expect(screen.getByText("FINANCE / RECOMMENDATION")).toBeInTheDocument();
    expect(screen.getByText("ANALYTICS")).toBeInTheDocument();
    expect(screen.getByText("EVIDENCE")).toBeInTheDocument();
    expect(screen.getByText("PLAN / CLAIM / EVIDENCE")).toBeInTheDocument();
    expect(screen.getByText("DOCUMENTS")).toBeInTheDocument();
    expect(screen.getByText("IMAGES")).toBeInTheDocument();
    expect(screen.getByText("GEOSPATIAL")).toBeInTheDocument();
    expect(screen.getByText("SATELLITE")).toBeInTheDocument();
    expect(screen.getByText("MILESTONES")).toBeInTheDocument();
    expect(screen.getByText("JAN-SAKSHI")).toBeInTheDocument();
    expect(screen.getByText("Relationship summary")).toBeInTheDocument();
    expect(screen.getByText("NEED & IMPACT")).toBeInTheDocument();
    expect(screen.getByText("LIFECYCLE")).toBeInTheDocument();
    expect(screen.getAllByText("36").length).toBeGreaterThan(0);
    expect(screen.getAllByText("40").length).toBeGreaterThan(0);
    expect(screen.queryByText("Documents panel")).toBeNull();
    expect(document.body.textContent?.toLowerCase()).not.toContain("fraud confirmed");
  });

  it("shows loading and error states", () => {
    intel.mockReturnValue({
      ...intelValue(),
      project: { data: null, error: null, loading: true },
    });
    const { rerender } = render(<ProjectPassportPage />);
    expect(screen.getByText("Loading project…")).toBeInTheDocument();
    intel.mockReturnValue({
      ...intelValue(),
      project: { data: null, error: "Project not found.", loading: false },
    });
    rerender(<ProjectPassportPage />);
    expect(screen.getByText("Project not found.")).toBeInTheDocument();
  });
});
