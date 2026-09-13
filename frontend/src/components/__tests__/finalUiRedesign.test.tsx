import type { ReactNode } from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { PageHeader } from "@/components/system/PageHeader";
import { FeatureExplanation } from "@/components/system/FeatureExplanation";
import { SystemPipeline } from "@/components/system/SystemPipeline";
import { EvidenceTimeline } from "@/components/system/EvidenceTimeline";
import { ScoreDisplay } from "@/components/system/ScoreDisplay";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { PageState } from "@/components/ui/PageState";
import { FEATURE_EXPLANATIONS } from "@/lib/explanations";
import { graphEvidenceObject } from "@/test/graphFixtures";

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

describe("Final UI/UX redesign primitives", () => {
  it("renders page headers with one-line explanations", () => {
    render(
      <PageHeader title="Project Search" explanation={FEATURE_EXPLANATIONS.search} />,
    );
    expect(screen.getByRole("heading", { name: "Project Search" })).toBeInTheDocument();
    expect(screen.getByText(FEATURE_EXPLANATIONS.search)).toBeInTheDocument();
  });

  it("keeps REAL, HYBRID, and SYNTHETIC visually distinct", () => {
    render(
      <>
        <StatusBadge kind="REAL" />
        <StatusBadge kind="HYBRID" />
        <StatusBadge kind="SYNTHETIC" />
      </>,
    );
    expect(screen.getByText("REAL")).toBeInTheDocument();
    expect(screen.getByText("HYBRID")).toBeInTheDocument();
    expect(screen.getByText("SYNTHETIC")).toBeInTheDocument();
  });

  it("shows the intelligence pipeline without invented metrics", () => {
    render(<SystemPipeline />);
    expect(screen.getByText("DISCOVER")).toBeInTheDocument();
    expect(screen.getByText("UNDERSTAND")).toBeInTheDocument();
    expect(screen.getByText("VERIFY")).toBeInTheDocument();
    expect(screen.getByText("ANALYSE")).toBeInTheDocument();
    expect(screen.getByText("ASSESS")).toBeInTheDocument();
    expect(screen.getByText("DECIDE")).toBeInTheDocument();
  });

  it("renders evidence timeline timestamps and data mode", () => {
    render(<EvidenceTimeline items={[graphEvidenceObject()]} />);
    expect(screen.getByText(/2026-09-10/)).toBeInTheDocument();
    expect(screen.getByText(/highly similar works/)).toBeInTheDocument();
    expect(screen.getByText("REAL")).toBeInTheDocument();
  });

  it("shows unavailable and inconclusive states without generic Error", () => {
    const { rerender } = render(
      <PageState kind="unavailable" message="This capability is not currently available for this project." />,
    );
    expect(screen.getByText("Unavailable")).toBeInTheDocument();
    expect(screen.getByText("This capability is not currently available for this project.")).toBeInTheDocument();
    rerender(
      <PageState kind="inconclusive" message="Not enough verified evidence is available to assess this signal." />,
    );
    expect(screen.getByText("Inconclusive")).toBeInTheDocument();
    rerender(<PageState kind="loading" message="Loading search results…" />);
    expect(screen.getByText("Loading search results…")).toBeInTheDocument();
    rerender(<PageState kind="error" message="API request failed" />);
    expect(screen.getByText("API Error")).toBeInTheDocument();
  });

  it("labels investigation priority as a review ranking, not fraud probability", () => {
    render(
      <ScoreDisplay label="Investigation Priority" value="78/100" kind="priority" note="Review ranking" />,
    );
    expect(screen.getByText("Investigation Priority")).toBeInTheDocument();
    expect(screen.getByText("78/100")).toBeInTheDocument();
    expect(screen.getByText("Review ranking")).toBeInTheDocument();
    expect(document.body.textContent?.toLowerCase()).not.toContain("fraud confirmed");
  });

  it("keeps micro-explanations for core functions", () => {
    render(<FeatureExplanation text={FEATURE_EXPLANATIONS.ml} />);
    expect(screen.getByText(/training distribution/)).toBeInTheDocument();
    expect(document.body.textContent?.toLowerCase()).not.toContain("fraud probability");
  });
});
