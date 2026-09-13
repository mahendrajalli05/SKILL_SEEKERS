import type { ReactNode } from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const fetchHealth = vi.fn();
const fetchProjects = vi.fn();
const fetchScope = vi.fn();
let params = new URLSearchParams("mode=hybrid");

vi.mock("next/navigation", () => ({
  useSearchParams: () => params,
}));

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock("@/lib/api", () => ({
  fetchHealth: (...args: unknown[]) => fetchHealth(...args),
  fetchProjects: (...args: unknown[]) => fetchProjects(...args),
  fetchScope: (...args: unknown[]) => fetchScope(...args),
  getApiBase: () => "http://127.0.0.1:8000",
}));

import { OfficerDashboard } from "@/components/OfficerDashboard";

function searchBody(total: number) {
  return {
    items: [],
    total,
    page: 1,
    page_size: 1,
    q: null,
    constituency: null,
    category: null,
    status: null,
    state: "Andhra Pradesh",
    scheme_id: null,
    apply_pilot_scope: true,
    effective_state: "Andhra Pradesh",
    data_mode: "HYBRID",
    pilot_label: "Current Pilot: Andhra Pradesh",
    constituency_filter_applied: false,
    ignored_non_geographic_constituency: null,
    scheme_id_note: "",
    note: "Search uses observed real fields.",
  };
}

describe("Officer dashboard", () => {
  beforeEach(() => {
    params = new URLSearchParams("mode=hybrid");
    fetchHealth.mockResolvedValue({
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
    });
    fetchScope.mockResolvedValue({
      current_pilot: "Andhra Pradesh",
      pilot_label: "Current Pilot: Andhra Pradesh",
      default_state: "Andhra Pradesh",
      default_data_mode: "HYBRID",
      scope_configurable: true,
      database_retains_all_states: true,
      note: "Pilot",
    });
    fetchProjects.mockImplementation(async (query: { status?: string }) => {
      if (query.status === "Unsanctioned") return searchBody(10);
      if (query.status === "Sanctioned") return searchBody(5);
      if (query.status === "Ongoing") return searchBody(20);
      if (query.status === "Completed") return searchBody(7);
      return searchBody(42);
    });
  });

  it("shows AP pilot counts without inventing risk statistics", async () => {
    render(<OfficerDashboard />);
    expect(screen.getByText("Loading officer dashboard…")).toBeInTheDocument();
    expect(await screen.findByText("42")).toBeInTheDocument();
    expect(screen.getAllByText("15").length).toBeGreaterThan(0);
    expect(screen.getAllByText("20").length).toBeGreaterThan(0);
    expect(screen.getAllByText("7").length).toBeGreaterThan(0);
    expect(screen.getByText("HYBRID DEMO")).toBeInTheDocument();
    expect(screen.getByText(/Prototype simulation/)).toBeInTheDocument();
    expect(screen.getByText(/prototype\/demo values may use synthetic enrichment/i)).toBeInTheDocument();
    expect(screen.getAllByText("Unavailable").length).toBeGreaterThan(3);
    expect(screen.getByText("KEY WORKFLOWS")).toBeInTheDocument();
    expect(screen.getByText("Find a Project")).toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/fraud confirmed/i);
    expect(fetchProjects.mock.calls.some((call) => call[0].page_size === 1)).toBe(true);
    expect(fetchProjects.mock.calls.some((call) => call[0].page_size === 8)).toBe(true);
  });

  it("shows REAL DATA mode without a prototype simulation notice", async () => {
    params = new URLSearchParams("mode=real");
    render(<OfficerDashboard />);
    expect(await screen.findByText("REAL DATA")).toBeInTheDocument();
    expect(screen.queryByText(/Prototype simulation/)).toBeNull();
  });

  it("shows an API error without blanking the page", async () => {
    fetchHealth.mockRejectedValue(new Error("API request failed"));
    render(<OfficerDashboard />);
    await waitFor(() => expect(screen.getByText(/API request failed/)).toBeInTheDocument());
    expect(screen.getByText("API Error")).toBeInTheDocument();
  });
});
