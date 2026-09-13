import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { ProjectSearchItem, ProjectSearchOptionsResponse, ProjectSearchResponse } from "@/lib/types";

const fetchProjects = vi.fn();
const fetchProjectOptions = vi.fn();
const fetchScope = vi.fn();
const replace = vi.fn();
let currentParams = new URLSearchParams("state=Andhra+Pradesh&mode=hybrid");

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace }),
  useSearchParams: () => currentParams,
}));

vi.mock("@/lib/api", () => ({
  fetchProjects: (...args: unknown[]) => fetchProjects(...args),
  fetchProjectOptions: (...args: unknown[]) => fetchProjectOptions(...args),
  fetchScope: (...args: unknown[]) => fetchScope(...args),
}));

import SearchPage from "@/app/search/page";

const options: ProjectSearchOptionsResponse = {
  states: ["Andhra Pradesh", "Maharashtra"],
  constituencies: ["ONGOLE", "ELURU"],
  excluded_non_geographic_constituencies: [],
  categories: ["Roads", "Education"],
  statuses: ["Ongoing", "Completed"],
  constituency_enabled: true,
  constituency_placeholder: null,
  selected_state: "Andhra Pradesh",
  pilot_label: "Current Pilot: Andhra Pradesh",
  note: "State first.",
};

function item(overrides: Partial<ProjectSearchItem> = {}): ProjectSearchItem {
  return {
    id: 101,
    scheme_id: "SVK-AP-000139",
    internal_project_id: "internal:abc",
    work_description: "Construction of roads",
    constituency: "ONGOLE",
    category: "Roads",
    status: "Ongoing",
    state: "Andhra Pradesh",
    mp_name: "Y. S. JALLI",
    allocation_amount: 500000,
    recommended_date: "2023-08-01",
    has_hybrid_enrichment: false,
    data_mode: "REAL",
    is_synthetic: false,
    synthetic_label: null,
    ...overrides,
  };
}

function response(overrides: Partial<ProjectSearchResponse> = {}): ProjectSearchResponse {
  return {
    items: [item()],
    total: 1,
    page: 1,
    page_size: 20,
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
    scheme_id_note: "Internal SARVSAKSHI application identifier — not an official MPLADS Work ID.",
    note: "Search uses observed real fields.",
    ...overrides,
  };
}

describe("Search page text search", () => {
  beforeEach(() => {
    currentParams = new URLSearchParams("state=Andhra+Pradesh&mode=hybrid");
    replace.mockReset();
    fetchProjects.mockReset();
    fetchProjectOptions.mockReset();
    fetchScope.mockReset();
    fetchScope.mockResolvedValue({
      current_pilot: "Andhra Pradesh",
      pilot_label: "Current Pilot: Andhra Pradesh",
      default_state: "Andhra Pradesh",
      default_data_mode: "HYBRID",
      scope_configurable: true,
      database_retains_all_states: true,
      note: "Pilot",
    });
    fetchProjectOptions.mockResolvedValue(options);
    fetchProjects.mockResolvedValue(response());
  });

  it("shows a loading state, then Scheme ID results", async () => {
    render(<SearchPage />);
    expect(screen.getByText("Loading search results…")).toBeInTheDocument();
    expect(await screen.findByText("SVK-AP-000139")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Construction of roads/ })).toBeInTheDocument();
    expect(screen.getAllByText("ONGOLE").length).toBeGreaterThan(0);
    expect(screen.getByText("HYBRID DEMO")).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "State" })).toHaveAccessibleName("State");
  });

  it("does not search on each keystroke; Search and Enter commit the query", async () => {
    const user = userEvent.setup();
    render(<SearchPage />);
    await screen.findByText("SVK-AP-000139");
    fetchProjects.mockClear();

    await user.type(screen.getByPlaceholderText(/Scheme ID/), "school");
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(fetchProjects).not.toHaveBeenCalled();

    fetchProjects.mockResolvedValueOnce(
      response({
        items: [item({ id: 202, scheme_id: "SVK-AP-000002", work_description: "Construction of school building" })],
        q: "school",
      }),
    );
    await user.click(screen.getByRole("button", { name: "Search" }));
    await waitFor(() => expect(fetchProjects).toHaveBeenCalled());
    expect(fetchProjects.mock.calls.at(-1)?.[0]).toMatchObject({ q: "school", page: 1 });
    expect(await screen.findByRole("link", { name: /Construction of school building/ })).toBeInTheDocument();
  });

  it("shows no matching projects found when a query returns zero rows", async () => {
    fetchProjects.mockResolvedValue(response({ items: [], total: 0, q: "zzzz-none" }));
    currentParams = new URLSearchParams("q=zzzz-none&state=Andhra+Pradesh&mode=hybrid");
    render(<SearchPage />);
    expect(await screen.findByText("No matching projects found")).toBeInTheDocument();
    expect(screen.queryByText("SVK-AP-000139")).toBeNull();
  });

  it("keeps filters while searching and renders pagination", async () => {
    const user = userEvent.setup();
    fetchProjects.mockResolvedValue(response({ total: 40 }));
    render(<SearchPage />);
    await screen.findByText("SVK-AP-000139");
    await user.click(screen.getByRole("combobox", { name: "Constituency" }));
    await user.click(screen.getByRole("option", { name: "ONGOLE" }));
    await waitFor(() =>
      expect(fetchProjects.mock.calls.at(-1)?.[0]).toMatchObject({
        constituency: "ONGOLE",
        state: "Andhra Pradesh",
      }),
    );
    expect(screen.getByRole("button", { name: "Next" })).not.toBeDisabled();
  });
});
