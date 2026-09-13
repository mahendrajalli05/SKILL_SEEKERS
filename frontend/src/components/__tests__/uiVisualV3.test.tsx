import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
  usePathname: () => "/",
  useSearchParams: () => new URLSearchParams("mode=hybrid"),
}));

import { NAV_GROUPS } from "@/components/AppHeader";
import { DataModeBanner } from "@/components/DataModeBanner";
import { AnomalyScale, ContributionBars, LifecycleChart } from "@/components/system/VisualKit";
import { DASHBOARD_WORKFLOWS, SYSTEM_PIPELINE_NODES } from "@/lib/explanations";

describe("Visual transformation V3", () => {
  it("keeps hub labels short and workflow titles operational", () => {
    expect(NAV_GROUPS.flatMap((group) => group.items.map((item) => item.label))).toContain("Projects");
    expect(DASHBOARD_WORKFLOWS.map((item) => item.title)).toEqual([
      "Find a Project",
      "Investigate a Project",
      "Assess a New Project",
      "Prioritize Projects",
      "Verify Field Evidence",
      "Review Project Stage",
      "Ask Copilot",
    ]);
    expect(SYSTEM_PIPELINE_NODES.map((node) => node.title)).toEqual([
      "DISCOVER",
      "UNDERSTAND",
      "VERIFY",
      "ANALYSE",
      "ASSESS",
      "DECIDE",
    ]);
  });

  it("renders compact environment chips without dropping provenance", () => {
    render(<DataModeBanner mode="HYBRID" />);
    expect(screen.getByText("HYBRID DEMO")).toBeInTheDocument();
    expect(screen.getByText("Controlled prototype")).toBeInTheDocument();
    expect(screen.getByText(/Fields marked SYNTHETIC/)).toBeInTheDocument();
  });

  it("renders contribution bars and lifecycle shares from provided values only", () => {
    render(
      <>
        <LifecycleChart future={10} ongoing={5} completed={3} unknown={2} total={20} />
        <ContributionBars
          items={[
            { label: "COST", value: 80 },
            { label: "TIME", value: null, unavailable: true, reason: "Unavailable" },
          ]}
        />
        <AnomalyScale score={47} />
      </>,
    );
    expect(screen.getByText("COST")).toBeInTheDocument();
    expect(screen.getAllByText("Unavailable").length).toBeGreaterThan(0);
    expect(screen.getByText("Typical")).toBeInTheDocument();
  });
});
