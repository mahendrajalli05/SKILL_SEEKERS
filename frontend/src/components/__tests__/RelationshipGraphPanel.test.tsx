import type { ReactNode } from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { RelationshipGraphPanel } from "@/components/RelationshipGraphPanel";
import {
  graphEvidenceObject,
  isolatedGraph,
  sampleGraph,
  sampleProject,
} from "@/test/graphFixtures";

const fetchGraph = vi.fn();
const fetchProject = vi.fn();
const fetchProjectEvidence = vi.fn();

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock("@/lib/api", () => ({
  fetchGraph: (...args: unknown[]) => fetchGraph(...args),
  fetchProject: (...args: unknown[]) => fetchProject(...args),
  fetchProjectEvidence: (...args: unknown[]) => fetchProjectEvidence(...args),
}));

function noFraud() {
  expect(document.body.textContent?.toLowerCase()).not.toContain("fraud");
}

describe("RelationshipGraphPanel", () => {
  beforeEach(() => {
    fetchGraph.mockReset();
    fetchProject.mockReset();
    fetchProjectEvidence.mockReset();
  });

  it("loads the central project, node types, findings, and evidence", async () => {
    render(
      <RelationshipGraphPanel
        projectId={232}
        mode="REAL"
        graph={sampleGraph()}
        loading={false}
        error={null}
        evidenceItems={[graphEvidenceObject()]}
        schemeId="SVK-AP-000232"
        internalProjectId="internal:232"
      />,
    );
    expect(screen.getByText("RELATIONSHIP GRAPH")).toBeInTheDocument();
    expect(screen.getByText("SVK-AP-000232")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /relationship neighborhood graph/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /PROJECT Construction of roads in Hindupur/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /MP Test MP/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /CONSTITUENCY HINDUPUR/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /CATEGORY Roads/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /IDA Hindupur_IDA/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /STATE Andhra Pradesh/ })).toBeInTheDocument();
    expect(screen.getByText("POTENTIAL_PATTERN_OF_INTEREST")).toBeInTheDocument();
    expect(
      screen.getAllByText(/29 highly similar works in the same constituency/).length,
    ).toBeGreaterThan(0);
    expect(screen.getByText(/real MPLADS project records/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reset" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Return to Investigation Workspace" })).toHaveAttribute(
      "href",
      "/projects/232/investigate?mode=real",
    );
    expect(screen.getByRole("link", { name: "Open Evidence" })).toHaveAttribute(
      "href",
      "/projects/232/investigate?mode=real#evidence-ev:graph:232:relationship_graph:REAL:abc",
    );
    expect(screen.getByText(/does not modify Investigation Priority/)).toBeInTheDocument();
    expect(screen.getAllByText("REAL").length).toBeGreaterThan(0);
    noFraud();
  });

  it("shows relationship details and related-project navigation", async () => {
    const user = userEvent.setup();
    render(
      <RelationshipGraphPanel
        projectId={232}
        mode="REAL"
        graph={sampleGraph()}
        loading={false}
        error={null}
        schemeId="SVK-AP-000232"
      />,
    );
    await user.click(screen.getByRole("button", { name: /SIMILAR_TO PROJECT:232 PROJECT:3700/ }));
    expect(screen.getByText("Relationship details")).toBeInTheDocument();
    expect(screen.getAllByText("SIMILAR_TO").length).toBeGreaterThan(0);
    expect(screen.getAllByText("0.91").length).toBeGreaterThan(0);
    expect(screen.getAllByText("YES").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/18 days/).length).toBeGreaterThan(0);
    expect(screen.getByRole("link", { name: "internal:3700" })).toHaveAttribute(
      "href",
      "/projects/3700?mode=real",
    );
    expect(screen.getByRole("link", { name: "Open related project" })).toHaveAttribute(
      "href",
      "/projects/3700?mode=real",
    );
    noFraud();
  });

  it("limits large neighborhoods until expanded", async () => {
    const user = userEvent.setup();
    render(
      <RelationshipGraphPanel
        projectId={232}
        mode="REAL"
        graph={sampleGraph({}, { similarCount: 20, peerCount: 5 })}
        loading={false}
        error={null}
      />,
    );
    expect(screen.getAllByRole("button", { name: /^PROJECT / })).toHaveLength(13);
    expect(screen.getByRole("button", { name: /Show more similar projects \(8 hidden\)/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Expand cluster peers \(5 hidden\)/ })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /Show more similar projects/ }));
    expect(screen.getAllByRole("button", { name: /^PROJECT / }).length).toBeGreaterThan(13);
    noFraud();
  });

  it("distinguishes HYBRID from REAL and does not present synthetic relationships as official", () => {
    render(
      <RelationshipGraphPanel
        projectId={232}
        mode="HYBRID"
        graph={sampleGraph({ graph_mode: "HYBRID_TEST", dataset_type: "HYBRID", gps_used: true })}
        loading={false}
        error={null}
      />,
    );
    expect(screen.getAllByText("HYBRID").length).toBeGreaterThan(0);
    expect(screen.getByText(/not official MPLADS findings/i)).toBeInTheDocument();
    expect(screen.getByText(/GPS was used only inside Overlap SIMILAR_TO scoring/)).toBeInTheDocument();
    noFraud();
  });

  it("shows isolated and insufficient-evidence neighborhoods", () => {
    render(
      <RelationshipGraphPanel
        projectId={232}
        mode="REAL"
        graph={isolatedGraph()}
        loading={false}
        error={null}
      />,
    );
    expect(screen.getByText(/Isolated neighborhood/)).toBeInTheDocument();
    expect(screen.getByText("INSUFFICIENT_EVIDENCE")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /PROJECT Construction of roads in Hindupur/ })).toBeInTheDocument();
    expect(screen.getByText(/No SIMILAR_TO projects/)).toBeInTheDocument();
    noFraud();
  });

  it("shows loading and API failure states", async () => {
    const { rerender } = render(
      <RelationshipGraphPanel projectId={232} mode="REAL" graph={null} loading error={null} />,
    );
    expect(screen.getByText("Loading relationship graph…")).toBeInTheDocument();
    rerender(
      <RelationshipGraphPanel
        projectId={232}
        mode="REAL"
        graph={null}
        loading={false}
        error="Graph API failed"
      />,
    );
    expect(screen.getByText("Graph API failed")).toBeInTheDocument();
    fetchGraph.mockRejectedValue(new Error("upstream graph unavailable"));
    fetchProject.mockResolvedValue(sampleProject());
    fetchProjectEvidence.mockResolvedValue({ project_id: 232, internal_project_id: "internal:232", items: [], note: "" });
    render(<RelationshipGraphPanel projectId={99} mode="REAL" />);
    expect(await screen.findByText("upstream graph unavailable")).toBeInTheDocument();
    noFraud();
  });

  it("self-fetches the graph API on the dedicated page path", async () => {
    fetchGraph.mockResolvedValue(sampleGraph());
    fetchProject.mockResolvedValue(sampleProject());
    fetchProjectEvidence.mockResolvedValue({
      project_id: 232,
      internal_project_id: "internal:232",
      items: [graphEvidenceObject()],
      note: "",
    });
    render(<RelationshipGraphPanel projectId={232} mode="REAL" />);
    expect(await screen.findByText("SVK-AP-000232")).toBeInTheDocument();
    await waitFor(() => expect(fetchGraph).toHaveBeenCalledWith(232, "real"));
    expect(fetchProject).toHaveBeenCalled();
    expect(screen.getByText("POTENTIAL_PATTERN_OF_INTEREST")).toBeInTheDocument();
    noFraud();
  });
});
