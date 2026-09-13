import type { ReactNode } from "react";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const nav = vi.hoisted(() => ({
  pathname: "/",
  params: new URLSearchParams("mode=hybrid"),
  projectId: "232",
  replace: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: nav.replace }),
  usePathname: () => nav.pathname,
  useSearchParams: () => nav.params,
  useParams: () => ({ id: nav.projectId }),
}));

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock("@/lib/api", () => ({
  fetchScope: vi.fn(async () => ({
    current_pilot: "Andhra Pradesh",
    pilot_label: "Current Pilot: Andhra Pradesh",
    default_state: "Andhra Pradesh",
    default_data_mode: "HYBRID",
    scope_configurable: true,
    database_retains_all_states: true,
    note: "Pilot",
  })),
  fetchHealth: vi.fn(async () => ({
    status: "ok",
    service: "sarvsakshi",
    environment: "development",
    database: { connected: true, dialect: "sqlite", path: "x", tables: [] },
    llm_enabled: false,
    engine_version: "x",
    fusion_config_version: "x",
    governance: {
      outputs: ["Investigation Priority", "Evidence Confidence"],
      does_not_output: ["legal fraud probability"],
      principle: "AI recommends. Authorized officers decide.",
    },
  })),
}));

import { AppHeader, navItemIsActive } from "@/components/AppHeader";
import { AppShell } from "@/components/AppShell";
import { ProjectSubNav, projectNavIsActive } from "@/components/ProjectSubNav";

describe("global navigation", () => {
  beforeEach(() => {
    nav.pathname = "/";
    nav.params = new URLSearchParams("mode=hybrid");
    nav.projectId = "232";
  });

  it("shows SARVSAKSHI identity, AP pilot, and operational nav items", async () => {
    render(<AppHeader />);
    expect(screen.getByRole("link", { name: "SARVSAKSHI" })).toBeInTheDocument();
    expect(await screen.findByText("Current Pilot: Andhra Pradesh")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /OVERVIEW/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /PROJECTS/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /EVIDENCE/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /VERIFICATION/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /ANALYTICS/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /PLANNING/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /AI & MODELS/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Dashboard" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Intelligence" })).toBeNull();
    expect(screen.queryByRole("link", { name: "Evidence & Verification" })).toBeNull();
    expect(screen.queryByRole("link", { name: "Reviews" })).toBeNull();
    expect(screen.getByRole("button", { name: "HYBRID DEMO" })).toHaveAttribute("aria-pressed", "true");
  });

  it("marks Search as the current page on /search", () => {
    expect(navItemIsActive("/search", { href: "/search", match: "prefix" })).toBe(true);
    expect(navItemIsActive("/", { href: "/search", match: "prefix" })).toBe(false);
  });

  it("exposes a skip link and main landmark", async () => {
    render(
      <AppShell>
        <p>Page body</p>
      </AppShell>,
    );
    expect(screen.getByRole("link", { name: "Skip to main content" })).toHaveAttribute(
      "href",
      "#main-content",
    );
    expect(screen.getByRole("main")).toBeInTheDocument();
    expect(await screen.findByText("Current Pilot: Andhra Pradesh")).toBeInTheDocument();
  });

  it("links to passport, workspace, graph, milestones, and copilot", () => {
    nav.pathname = "/projects/232/investigate";
    nav.params = new URLSearchParams("mode=real");
    render(<ProjectSubNav />);
    expect(screen.getByRole("link", { name: "Digital Passport" })).toHaveAttribute(
      "href",
      "/projects/232?mode=real",
    );
    expect(screen.getByRole("link", { name: "Investigation Workspace" })).toHaveAttribute(
      "href",
      "/projects/232/investigate?mode=real",
    );
    expect(screen.getByRole("link", { name: "Relationship Graph" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Milestones" })).toHaveAttribute(
      "href",
      "/projects/232/investigate?mode=real#milestones",
    );
    expect(screen.getByRole("link", { name: "Copilot" })).toBeInTheDocument();
    expect(projectNavIsActive("/projects/232/investigate", "investigate", "232")).toBe(true);
  });
});
