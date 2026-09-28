import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const fetchProjects = vi.fn();
const fetchScope = vi.fn();

vi.mock("@/lib/api", () => ({
  fetchProjects: (...args: unknown[]) => fetchProjects(...args),
  fetchScope: (...args: unknown[]) => fetchScope(...args),
  getApiBase: () => "https://skill-seekers-y0ru.onrender.com",
}));

import { fetchPilotCounts } from "@/lib/dashboardStats";

describe("fetchPilotCounts", () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it("calls /api/v1/projects/stats and returns consolidated counts when successful", async () => {
    const mockStats = {
      total: 3640,
      future: 300,
      ongoing: 2000,
      completed: 1340,
      pilot_label: "Current Pilot: Andhra Pradesh",
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockStats,
    } as Response);

    const result = await fetchPilotCounts("hybrid");

    expect(globalThis.fetch).toHaveBeenCalledWith(
      "https://skill-seekers-y0ru.onrender.com/api/v1/projects/stats?state=Andhra%20Pradesh&apply_pilot_scope=true",
    );
    expect(result).toEqual({
      total: 3640,
      future: 300,
      ongoing: 2000,
      completed: 1340,
      pilotLabel: "Current Pilot: Andhra Pradesh",
      note: "",
    });
    // Fallback individual queries should not have been called
    expect(fetchProjects).not.toHaveBeenCalled();
    expect(fetchScope).not.toHaveBeenCalled();
  });

  it("falls back to legacy individual queries when /api/v1/projects/stats fails", async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new Error("Network failure"));

    fetchScope.mockResolvedValue({
      pilot_label: "Current Pilot: Andhra Pradesh",
    });
    fetchProjects.mockImplementation(async (query: { status?: string }) => {
      if (query.status === "Unsanctioned") return { total: 100, note: "sample" };
      if (query.status === "Sanctioned") return { total: 200, note: "sample" };
      if (query.status === "Ongoing") return { total: 2000, note: "sample" };
      if (query.status === "Completed") return { total: 1340, note: "sample" };
      return { total: 3640, note: "Search uses observed real fields." };
    });

    const result = await fetchPilotCounts("hybrid");

    expect(globalThis.fetch).toHaveBeenCalledWith(
      "https://skill-seekers-y0ru.onrender.com/api/v1/projects/stats?state=Andhra%20Pradesh&apply_pilot_scope=true",
    );
    expect(result).toEqual({
      total: 3640,
      future: 300,
      ongoing: 2000,
      completed: 1340,
      pilotLabel: "Current Pilot: Andhra Pradesh",
      note: "Search uses observed real fields.",
    });
  });
});
