import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
  usePathname: () => "/",
  useSearchParams: () => new URLSearchParams("mode=hybrid"),
}));

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: string; href: string }) => <a href={href}>{children}</a>,
}));

vi.mock("@/lib/api", () => ({
  fetchHealth: vi.fn(async () => ({ status: "ok" })),
  fetchScope: vi.fn(async () => ({
    current_pilot: "Andhra Pradesh",
    pilot_label: "Current Pilot: Andhra Pradesh",
    default_state: "Andhra Pradesh",
    default_data_mode: "HYBRID",
    scope_configurable: true,
    database_retains_all_states: true,
    note: "Pilot",
  })),
}));

import { AppHeader, NAV_GROUPS, navGroupIsActive, navItemIsActive } from "@/components/AppHeader";
import { CapabilityHub } from "@/components/system/CapabilityHub";
import { LifecycleTrack } from "@/components/system/LifecycleTrack";
import {
  ANALYTICS_MODULES,
  DASHBOARD_WORKFLOWS,
  EVIDENCE_MODULES,
  PLANNING_MODULES,
  VERIFICATION_MODULES,
} from "@/lib/explanations";
import { StyledSelect } from "@/components/ui/StyledSelect";

describe("Final UI/UX product refinement V4", () => {
  it("separates major capabilities into task-based sections", () => {
    expect(NAV_GROUPS.map((group) => group.label)).toEqual([
      "OVERVIEW",
      "PROJECTS",
      "INVESTIGATION",
      "EVIDENCE",
      "VERIFICATION",
      "ANALYTICS",
      "PLANNING",
      "LIFECYCLE",
      "AI & MODELS",
      "CONTEXT",
      "ASSESSMENT",
      "DEMO",
    ]);
    expect(NAV_GROUPS.flatMap((group) => group.items.map((item) => item.label))).not.toContain("Intelligence");
    expect(navGroupIsActive("/analytics/cost", NAV_GROUPS.find((group) => group.id === "analytics")!)).toBe(true);
    expect(navGroupIsActive("/geospatial", NAV_GROUPS.find((group) => group.id === "verification")!)).toBe(true);
    expect(navItemIsActive("/evidence/documents", { href: "/evidence/documents", match: "prefix" })).toBe(true);
    expect(navItemIsActive("/evidence", { href: "/evidence", match: "evidence-center" })).toBe(true);
  });

  it("keeps dashboard workflows and capability hubs distinct", () => {
    expect(DASHBOARD_WORKFLOWS.map((item) => item.title)).toContain("Find a Project");
    expect(ANALYTICS_MODULES.map((item) => item.label)).toEqual([
      "COST INTELLIGENCE",
      "TIME INTELLIGENCE",
      "OVERLAP DETECTION",
      "COMPLIANCE",
    ]);
    expect(VERIFICATION_MODULES.map((item) => item.label)).toEqual(["GEOSPATIAL", "SATELLITE", "JAN-SAKSHI"]);
    expect(EVIDENCE_MODULES.map((item) => item.label)).toContain("DOCUMENTS & BLUEPRINT");
    expect(PLANNING_MODULES.map((item) => item.label)).toEqual(["PROJECT PRIORITIZATION", "NEED & IMPACT"]);
  });

  it("renders analytics hub tiles without an Intelligence mega-section", () => {
    render(
      <CapabilityHub
        kicker="Analytics"
        title="ANALYTICS CENTER"
        explanation="Reads cost, time, overlap, and compliance signals."
        items={ANALYTICS_MODULES}
      />,
    );
    expect(screen.getByRole("heading", { name: "ANALYTICS CENTER" })).toBeInTheDocument();
    expect(screen.getByText("COST INTELLIGENCE")).toBeInTheDocument();
    expect(screen.getByText("OVERLAP DETECTION")).toBeInTheDocument();
    expect(screen.queryByText("Intelligence Center")).toBeNull();
  });

  it("keeps UNKNOWN as UNKNOWN on the lifecycle track", () => {
    render(<LifecycleTrack current="UNKNOWN" />);
    expect(screen.getByText("UNKNOWN remains UNKNOWN.")).toBeInTheDocument();
    expect(screen.getByText("FUTURE")).toBeInTheDocument();
    expect(screen.getByText("FINAL REVIEW")).toBeInTheDocument();
  });

  it("expands a sidebar section to reveal children", async () => {
    const user = userEvent.setup();
    render(<AppHeader />);
    await user.click(screen.getByRole("button", { name: /ANALYTICS/i }));
    expect(screen.getByRole("link", { name: "Cost Intelligence" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Overlap Detection" })).toBeInTheDocument();
  });

  it("keeps styled dropdown contrast and selected state", async () => {
    const user = userEvent.setup();
    render(
      <StyledSelect
        label="Project type"
        value=""
        onChange={() => undefined}
        options={[{ value: "Roads", label: "Roads" }]}
        placeholder="Any type"
      />,
    );
    await user.click(screen.getByRole("combobox", { name: "Project type" }));
    expect(screen.getByRole("option", { name: "Roads" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Any type" })).toHaveAttribute("aria-selected", "true");
  });
});
