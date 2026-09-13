import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  ContextualIntelligencePanel,
  observationKey,
} from "@/components/ContextualIntelligencePanel";
import type { ProjectContextResponse } from "@/lib/types";

const payload: ProjectContextResponse = {
  project_id: 1,
  internal_project_id: "internal:1",
  engine: "context",
  engine_version: "contextual-data-enrichment-v1",
  data_mode: "REAL",
  assessment_kind: null,
  persisted: true,
  governance_note: "External contextual indicators are supporting context only.",
  requested_geographic_level: "STATE",
  matched_geographic_level: "STATE",
  project_state: "Andhra Pradesh",
  recommended_date: "2023-06-01",
  allocation_amount: 2000000,
  observations: [
    {
      indicator: "state_population",
      status: "AVAILABLE",
      value: 52787000,
      unit: "persons",
      geographic_level: "STATE",
      geo_key: "Andhra Pradesh",
      reference_year: 2021,
      reference_date: "2021-03-01",
      source_id: "mohfw_ncp_population_projections_2011_2036",
      source_name: "Population Projections for India and States, 2011-2036",
      publisher: "National Commission on Population, Ministry of Health and Family Welfare, Government of India",
      source_url: "https://main.mohfw.gov.in/",
      retrieval_date: "2026-09-11",
      dataset_version: "July 2020",
      transformation: "thousands × 1000",
      limitations: ["Not a beneficiary count."],
      data_mode: "REAL",
      confidence: 0.7,
      quality: "observed",
      context_kind: "OBSERVED_EXTERNAL_INDICATOR",
      failure_code: null,
      notes: "OBSERVED EXTERNAL INDICATOR at STATE level.",
    },
    {
      indicator: "mplads_allocation",
      status: "AVAILABLE",
      value: 2000000,
      unit: "unspecified_allocation_amount",
      geographic_level: null,
      geo_key: null,
      reference_year: null,
      reference_date: null,
      source_id: "mplads_project_record",
      source_name: "Cleaned MPLADS work-level extract",
      publisher: "SARVSAKSHI",
      source_url: null,
      retrieval_date: null,
      dataset_version: null,
      transformation: null,
      limitations: [],
      data_mode: "REAL",
      confidence: 0.9,
      quality: "project_observation",
      context_kind: "PROJECT_SPECIFIC_FACT",
      failure_code: null,
      notes: "PROJECT-SPECIFIC FACT: recorded allocation_amount.",
    },
    {
      indicator: "allocation_vs_reference_rate",
      status: "INCONCLUSIVE",
      value: null,
      unit: null,
      geographic_level: null,
      geo_key: null,
      reference_year: null,
      reference_date: null,
      source_id: null,
      source_name: null,
      publisher: null,
      source_url: null,
      retrieval_date: null,
      dataset_version: null,
      transformation: null,
      limitations: ["Units are incompatible."],
      data_mode: "REAL",
      confidence: 0.12,
      quality: "incompatible_units",
      context_kind: "DERIVED_CONTEXT",
      failure_code: "INCOMPATIBLE_UNIT",
      notes: "DERIVED COMPARISON is INCONCLUSIVE.",
    },
    {
      indicator: "reference_unit_rate",
      status: "UNAVAILABLE",
      value: null,
      unit: null,
      geographic_level: "STATE",
      geo_key: "Andhra Pradesh",
      reference_year: null,
      reference_date: null,
      source_id: "cpwd_delhi_schedule_of_rates",
      source_name: "CPWD Delhi Schedule of Rates",
      publisher: "Central Public Works Department",
      source_url: null,
      retrieval_date: null,
      dataset_version: null,
      transformation: null,
      limitations: ["Official SoR extract is not bundled."],
      data_mode: "HYBRID",
      confidence: 0.12,
      quality: "unavailable",
      context_kind: "OBSERVED_EXTERNAL_INDICATOR",
      failure_code: "SOURCE_UNAVAILABLE",
      notes: "Official schedule-of-rate source is not available.",
    },
    {
      indicator: "reference_unit_rate",
      status: "AVAILABLE",
      value: 1850,
      unit: "INR_per_sqm",
      geographic_level: "STATE",
      geo_key: "Andhra Pradesh",
      reference_year: 2023,
      reference_date: "2023-04-01",
      source_id: "hybrid_reference_cost_test",
      source_name: "HYBRID/TEST reference-cost fixture",
      publisher: "SARVSAKSHI labelled test fixture",
      source_url: null,
      retrieval_date: null,
      dataset_version: "hybrid-v1",
      transformation: null,
      limitations: ["Not an official schedule of rates."],
      data_mode: "HYBRID",
      confidence: 0.35,
      quality: "test_fixture",
      context_kind: "OBSERVED_EXTERNAL_INDICATOR",
      failure_code: null,
      notes: "OBSERVED EXTERNAL INDICATOR from a labelled HYBRID/TEST fixture.",
    },
  ],
  unavailable_indicators: [],
  evidence_ids: ["ev:context:1:DEVELOPMENT_NEED_CONTEXT:REAL:abc"],
  limitations: ["External context is supporting context only."],
  processing_version: "contextual-data-enrichment-v1",
  cost_v1_1_unchanged: true,
  need_impact_formula_unchanged: true,
  risk_fusion_unchanged: true,
  fraud_probability: null,
};

describe("ContextualIntelligencePanel", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => payload,
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows external context versus project observation", async () => {
    render(<ContextualIntelligencePanel projectId={1} mode="REAL" />);
    expect(await screen.findAllByText("EXTERNAL CONTEXT")).not.toHaveLength(0);
    expect(screen.getByRole("heading", { name: "Contextual Intelligence" })).toBeInTheDocument();
    expect(screen.getByText("PROJECT OBSERVATION")).toBeInTheDocument();
    expect(screen.getByText("DERIVED COMPARISON")).toBeInTheDocument();
    expect(screen.getByText("Development need context")).toBeInTheDocument();
    expect(screen.getByText("Reference cost context")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Refresh contextual snapshot" }));
    expect(fetch).toHaveBeenCalled();
  });

  it("keeps distinct keys when two observations share indicator", () => {
    const sameIndicator = payload.observations.filter((item) => item.indicator === "reference_unit_rate");
    expect(sameIndicator).toHaveLength(2);
    const keys = sameIndicator.map((item, index) => observationKey(item, index));
    expect(new Set(keys).size).toBe(keys.length);
    expect(keys[0]).not.toBe("reference_unit_rate");
    expect(keys[1]).not.toBe("reference_unit_rate");
    expect(keys[0]).not.toBe(keys[1]);
  });

  it("renders both reference_unit_rate observations from different sources", async () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});
    render(<ContextualIntelligencePanel projectId={1} mode="HYBRID" />);
    expect(await screen.findByText("CPWD Delhi Schedule of Rates")).toBeInTheDocument();
    expect(screen.getByText("HYBRID/TEST reference-cost fixture")).toBeInTheDocument();
    expect(screen.getAllByText("reference_unit_rate")).toHaveLength(2);
    expect(consoleError.mock.calls.flat().join(" ")).not.toMatch(/same key/i);
    consoleError.mockRestore();
  });
});
