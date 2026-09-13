import type { ReactNode } from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { RelationshipSummary } from "@/components/RelationshipSummary";
import { sampleGraph } from "@/test/graphFixtures";

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

describe("RelationshipSummary", () => {
  it("shows compact passport counts and opens the visualization", () => {
    render(
      <RelationshipSummary
        graph={sampleGraph({}, { similarCount: 3, peerCount: 2 })}
        openHref="/projects/232/graph?mode=real"
      />,
    );
    expect(screen.getByText("Connected nodes")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
    expect(screen.getByText("Similar projects")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("Graph finding")).toBeInTheDocument();
    expect(screen.getByText("POTENTIAL_PATTERN_OF_INTEREST")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open Relationship Graph" })).toHaveAttribute(
      "href",
      "/projects/232/graph?mode=real",
    );
    expect(screen.getByText("REAL")).toBeInTheDocument();
    expect(document.body.textContent?.toLowerCase()).not.toContain("fraud");
  });

  it("shows loading and error states", () => {
    const { rerender } = render(<RelationshipSummary loading />);
    expect(screen.getByText("Loading relationship neighborhood…")).toBeInTheDocument();
    rerender(<RelationshipSummary error="Graph API failed" />);
    expect(screen.getByText("Graph API failed")).toBeInTheDocument();
  });
});
