import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SatellitePceBlock, SatelliteRemoteSensingPanel } from "@/components/SatelliteRemoteSensingPanel";
import type { SatelliteResponse } from "@/lib/types";

const payload: SatelliteResponse = {
  project_id: 1,
  internal_project_id: "internal:test",
  data_mode: "HYBRID",
  overall_result: "SATELLITE_CONSISTENT",
  provider: "test-mock",
  imagery_available: true,
  acquisition_date: "2025-11-12",
  spatial_resolution_m: 0.5,
  coverage: "Covers claimed site",
  change_result: "Potential site-level change detected between before and after observations.",
  evidence_confidence: 0.34,
  confidence_label: "LOW",
  project_location: { available: true, synthetic: true },
  availability: { available: true, provider: "test-mock" },
  location_analysis: { covers_claimed_site: true, result: "SATELLITE_CONSISTENT" },
  temporal_analysis: { window_matches_claim: true },
  change_analysis: { visible_site_change: true },
  resolution_analysis: { sufficient: true, finding: "Spatial resolution is potentially sufficient" },
  image_gps_signals: [],
  scenes: [],
  work_scale: "LARGE_LINEAR",
  limitations: ["TEST/SYNTHETIC mocked provider responses are not official satellite imagery."],
  explanation:
    "Consistent with available imagery. TEST/SYNTHETIC mocked imagery metadata is not official satellite imagery.",
  finding: "Consistent with available imagery",
  plan_claim_evidence: {
    claim: "Site development completed by October 2025.",
    satellite: "Imagery available after claimed completion shows visible site change.",
    result: "SATELLITE_CONSISTENT",
    note: "Satellite evidence does not automatically mark the claim false.",
    claim_marked_false: false,
  },
  evidence_ids: ["ev:satellite:1:SATELLITE_AVAILABILITY:HYBRID:abc"],
  provenance: { notes: "TEST/SYNTHETIC" },
  note: "Decision-support evidence layer.",
  engine_version: "satellite-remote-sensing-v1",
  labelled_synthetic: true,
  official_imagery: false,
  map_available: false,
};

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => payload,
    }),
  );
});

describe("SatelliteRemoteSensingPanel", () => {
  it("shows provider, imagery, acquisition, resolution, coverage, change, and assessment", async () => {
    render(<SatelliteRemoteSensingPanel projectId={1} mode="HYBRID" />);
    expect(await screen.findByText("Satellite / Remote Sensing")).toBeInTheDocument();
    expect(screen.getAllByText(/test-mock/).length).toBeGreaterThan(0);
    expect(screen.getAllByText("2025-11-12").length).toBeGreaterThan(0);
    expect(screen.getByText("0.5 m")).toBeInTheDocument();
    expect(screen.getByText("Covers claimed site")).toBeInTheDocument();
    expect(screen.getAllByText("SATELLITE_CONSISTENT").length).toBeGreaterThan(0);
    expect(screen.getByText(/No satellite map is shown/)).toBeInTheDocument();
    expect(screen.getByText(/TEST\/SYNTHETIC mocked imagery is not official/i)).toBeInTheDocument();
    expect(document.body.textContent?.toLowerCase()).not.toContain("fraud");
  });

  it("runs a TEST provider check in HYBRID", async () => {
    render(<SatelliteRemoteSensingPanel projectId={1} mode="HYBRID" />);
    await screen.findByText("Satellite / Remote Sensing");
    await userEvent.click(screen.getByRole("button", { name: "Run TEST provider check" }));
    expect(fetch).toHaveBeenCalled();
  });
});

describe("SatellitePceBlock", () => {
  it("does not mark the claim false", () => {
    render(<SatellitePceBlock data={payload} />);
    expect(screen.getByText(/Site development completed by October 2025/)).toBeInTheDocument();
    expect(screen.getByText(/The claim is not marked false automatically/)).toBeInTheDocument();
    expect(document.body.textContent?.toLowerCase()).not.toContain("fraud detected");
  });
});

describe("unavailable imagery", () => {
  it("does not render a fake map", async () => {
    const unavailable: SatelliteResponse = {
      ...payload,
      overall_result: "SATELLITE_UNAVAILABLE",
      provider: "unavailable",
      imagery_available: false,
      acquisition_date: null,
      spatial_resolution_m: null,
      coverage: "Unavailable",
      change_result: null,
      labelled_synthetic: false,
      official_imagery: false,
      map_available: false,
      explanation: "No reliable satellite imagery source or API is configured.",
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => unavailable,
      }),
    );
    render(<SatelliteRemoteSensingPanel projectId={1} mode="REAL" />);
    expect(await screen.findByText("SATELLITE_UNAVAILABLE")).toBeInTheDocument();
    expect(screen.getByText(/No satellite map is shown/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Run TEST provider check" })).not.toBeInTheDocument();
  });
});
