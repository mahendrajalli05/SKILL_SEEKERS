import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { GeospatialEvidencePanel, GeospatialPceBlock } from "@/components/GeospatialEvidencePanel";
import type { GeospatialResponse } from "@/lib/types";

const payload: GeospatialResponse = {
  project_id: 1,
  internal_project_id: "internal:test",
  data_mode: "HYBRID",
  project_location: {
    project_id: 1,
    latitude: 18.1167,
    longitude: 83.4,
    source: "SYNTHETIC hybrid enrichment coordinates. Not official MPLADS GPS.",
    data_mode: "HYBRID",
    confidence: 0.35,
    timestamp: null,
    provenance: {},
    available: true,
    unavailable_reason: null,
    synthetic: true,
    label: "SYNTHETIC",
  },
  image_locations: [],
  images: [
    {
      image_id: 21,
      location: {
        image_id: 21,
        latitude: 18.117,
        longitude: 83.4,
        source: "Reported GPS metadata from uploaded file",
        extraction_method: "exif",
        confidence: 0.45,
        data_mode: "HYBRID",
        gps_status: "GPS_METADATA_PRESENT",
        gps_available: true,
        unavailable_reason: null,
      },
      result: "LOCATION_CONSISTENT",
      distance_meters: 148,
      distance_km: 0.148,
      threshold_meters: 500,
      finding: "LOCATION_CONSISTENT",
      explanation:
        "Uploaded image GPS is 148 meters from the supplied project location, within the configured 500 meter prototype threshold.",
      confidence: 0.35,
      score: 0,
      evidence_id: "ev:geo:1:GEOSPATIAL_LOCATION_CONSISTENCY:HYBRID:abc",
    },
  ],
  summary: {
    image_count: 1,
    gps_available_count: 1,
    gps_unavailable_count: 0,
    consistent_count: 1,
    mismatch_count: 0,
    inconclusive_count: 0,
    mixed_results: false,
    distances_meters: [148],
  },
  overall_result: "LOCATION_CONSISTENT",
  location_consistency: "LOCATION_CONSISTENT",
  threshold_meters: 500,
  evidence_confidence: 0.35,
  satellite: {
    capability: "SATELLITE_VERIFICATION_NOT_AVAILABLE",
    result: "SATELLITE_VERIFICATION_NOT_AVAILABLE",
    available: false,
    imagery: null,
    explanation: "Satellite verification is not available.",
    score: null,
  },
  plan_claim_evidence: {
    claim: "Progress photograph was taken at the project site.",
    evidence: "image 21 GPS = 148 meters from project location",
    result: "LOCATION_CONSISTENT",
    note: "Location consistency does not prove the photograph depicts the claimed work.",
  },
  evidence_ids: ["ev:geo:1:summary"],
  provenance: {},
  explanation: "Uploaded image GPS is 148 meters from the supplied project location.",
  limitations: ["This is a location consistency check, not proof of project authenticity."],
  note: "Geospatial Consistency V1 is a location consistency check.",
  engine_version: "geospatial-consistency-v1",
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

describe("GeospatialEvidencePanel", () => {
  it("shows availability, distance, threshold, and result", async () => {
    render(<GeospatialEvidencePanel projectId={1} mode="HYBRID" />);
    expect(await screen.findByText("GEOSPATIAL VERIFICATION")).toBeInTheDocument();
    expect(screen.getByText(/Project location:/)).toBeInTheDocument();
    expect(screen.getAllByText("Available").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/148 meters/).length).toBeGreaterThan(0);
    expect(screen.getByText(/500m prototype threshold/)).toBeInTheDocument();
    expect(screen.getAllByText("LOCATION_CONSISTENT").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/SYNTHETIC/).length).toBeGreaterThan(0);
    expect(screen.getByText(/SATELLITE_VERIFICATION_NOT_AVAILABLE/)).toBeInTheDocument();
    expect(document.body.textContent?.toLowerCase()).not.toContain("fraud");
    await userEvent.click(screen.getByRole("button", { name: "Run location check" }));
    expect(screen.getByText(/does not prove the photograph depicts/)).toBeInTheDocument();
  });
});

describe("GeospatialPceBlock", () => {
  it("frames claim versus image GPS", () => {
    render(<GeospatialPceBlock data={payload} />);
    expect(screen.getByText(/Progress photograph was taken at the project site/)).toBeInTheDocument();
    expect(screen.getByText(/148 meters from project location/)).toBeInTheDocument();
    expect(screen.getByText(/LOCATION_CONSISTENT/)).toBeInTheDocument();
  });
});
