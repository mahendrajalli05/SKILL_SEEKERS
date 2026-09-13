import type { ReactNode } from "react";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { sampleGraph, sampleProject, graphEvidenceObject } from "@/test/graphFixtures";

const fetchGraph = vi.fn();
const fetchProject = vi.fn();
const fetchProjectEvidence = vi.fn();

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "232" }),
  useSearchParams: () => new URLSearchParams("mode=real"),
}));

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

import RelationshipGraphPage from "@/app/projects/[id]/graph/page";

describe("Relationship Graph page", () => {
  beforeEach(() => {
    fetchGraph.mockResolvedValue(sampleGraph());
    fetchProject.mockResolvedValue(sampleProject());
    fetchProjectEvidence.mockResolvedValue({
      project_id: 232,
      internal_project_id: "internal:232",
      items: [graphEvidenceObject()],
      note: "",
    });
  });

  it("renders the visualization route for a selected project", async () => {
    render(<RelationshipGraphPage />);
    expect(await screen.findByText("RELATIONSHIP GRAPH")).toBeInTheDocument();
    expect(screen.getByText("SVK-AP-000232")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /PROJECT Construction of roads in Hindupur/ })).toBeInTheDocument();
    expect(document.body.textContent?.toLowerCase()).not.toContain("fraud");
  });
});
