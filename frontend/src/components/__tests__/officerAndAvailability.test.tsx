import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { DataAvailabilityPanel } from "@/components/DataAvailabilityPanel";
import { DataModeBanner } from "@/components/DataModeBanner";
import { OfficerDecisionPanel } from "@/components/OfficerDecisionPanel";
import { SearchFilters } from "@/components/SearchFilters";
import { SyntheticFieldsPanel } from "@/components/SyntheticFieldsPanel";
import { HYBRID_DEMO_NOTICE, SELECT_STATE_FIRST, UNAVAILABLE_REAL_LABEL } from "@/lib/display";
import type { ProjectSearchOptionsResponse } from "@/lib/types";

describe("DataAvailabilityPanel", () => {
  it("lists unavailable government fields instead of hiding them", () => {
    render(
      <DataAvailabilityPanel
        fields={[
          {
            field: "district",
            status: "UNAVAILABLE",
            reason: "Verified district is not present in the current real work-level extract.",
            display: UNAVAILABLE_REAL_LABEL,
          },
          {
            field: "vendor",
            status: "UNAVAILABLE",
            reason: "Vendor is not present.",
            display: UNAVAILABLE_REAL_LABEL,
          },
        ]}
      />,
    );
    expect(screen.getByText("district")).toBeInTheDocument();
    expect(screen.getByText("vendor")).toBeInTheDocument();
    expect(screen.getByText(/Verified district is not present/)).toBeInTheDocument();
    expect(screen.getAllByText(new RegExp(UNAVAILABLE_REAL_LABEL)).length).toBeGreaterThan(0);
  });
});

describe("DataModeBanner", () => {
  it("distinguishes REAL DATA from HYBRID DEMO and shows the synthetic warning", () => {
    const { rerender } = render(<DataModeBanner mode="REAL" />);
    expect(screen.getByText("REAL DATA")).toBeInTheDocument();
    expect(screen.getByText(/Synthetic enrichment is not used/)).toBeInTheDocument();
    rerender(
      <DataModeBanner
        mode="HYBRID"
        hasHybridEnrichment
        hybridNotice={HYBRID_DEMO_NOTICE}
      />,
    );
    expect(screen.getByText("HYBRID DEMO")).toBeInTheDocument();
    expect(screen.getByText(/Fields marked SYNTHETIC/)).toBeInTheDocument();
    expect(screen.getByText(/Prototype simulation/)).toBeInTheDocument();
  });
});

describe("OfficerDecisionPanel", () => {
  it("offers confirm, dismiss, and need more information without a fraud button", () => {
    render(
      <OfficerDecisionPanel decisions={[]} onSubmit={() => undefined} />,
    );
    expect(screen.getByRole("button", { name: "Confirm concern" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Dismiss" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Need more information" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /fraud/i })).toBeNull();
    expect(document.body.textContent?.toLowerCase()).not.toContain("fraud confirmed");
    expect(document.body.textContent?.toLowerCase()).toContain("does not record a legal fraud finding");
  });
});

const options: ProjectSearchOptionsResponse = {
  states: ["Andhra Pradesh", "Maharashtra"],
  constituencies: ["KURNOOL", "ELURU"],
  excluded_non_geographic_constituencies: ["Sitting Rajya Sabha"],
  categories: ["Normal/Others"],
  statuses: ["Ongoing"],
  constituency_enabled: true,
  constituency_placeholder: null,
  selected_state: "Andhra Pradesh",
  pilot_label: "Current Pilot: Andhra Pradesh",
  note: "State first.",
};

describe("SearchFilters", () => {
  it("disables constituency until a state is selected", async () => {
    const user = userEvent.setup();
    const calls: string[] = [];
    render(
      <SearchFilters
        stateFilter=""
        constituency=""
        category=""
        status=""
        q=""
        options={{ ...options, constituency_enabled: false, constituencies: [] }}
        onStateChange={(value) => calls.push(value)}
        onConstituencyChange={() => undefined}
        onCategoryChange={() => undefined}
        onStatusChange={() => undefined}
        onQueryChange={() => undefined}
      />,
    );
    expect(screen.getByText(SELECT_STATE_FIRST)).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "Constituency" })).toBeDisabled();
    await user.click(screen.getByRole("combobox", { name: "State" }));
    await user.click(screen.getByRole("option", { name: "Andhra Pradesh" }));
    expect(calls).toEqual(["Andhra Pradesh"]);
  });

  it("lists only state-specific geographic constituencies", async () => {
    render(
      <SearchFilters
        stateFilter="Andhra Pradesh"
        constituency=""
        category=""
        status=""
        q=""
        options={options}
        onStateChange={() => undefined}
        onConstituencyChange={() => undefined}
        onCategoryChange={() => undefined}
        onStatusChange={() => undefined}
        onQueryChange={() => undefined}
      />,
    );
    expect(screen.getByRole("combobox", { name: "Constituency" })).not.toBeDisabled();
    await userEvent.click(screen.getByRole("combobox", { name: "Constituency" }));
    expect(screen.getByRole("option", { name: "KURNOOL" })).toBeInTheDocument();
    expect(screen.queryByRole("option", { name: "Sitting Rajya Sabha" })).toBeNull();
    expect(screen.getByPlaceholderText(/Scheme ID/)).toBeInTheDocument();
  });
});

describe("SyntheticFieldsPanel", () => {
  it("hides synthetic values in REAL mode", () => {
    render(
      <SyntheticFieldsPanel
        mode="REAL"
        enrichment={{
          label: "SYNTHETIC",
          disclaimer: "SYNTHETIC prototype enrichment.",
          implementing_district: "Kurnool",
          implementing_agency: null,
          vendor_name: "Prototype Vendor",
          sanction_date: "2023-07-01",
          start_date: "2023-07-20",
          planned_start_date: null,
          planned_completion_date: null,
          completion_date: null,
          actual_start_date: null,
          actual_completion_date: null,
          expenditure: 1,
          gps_latitude: 15.8,
          gps_longitude: 78,
          physical_progress_percent: 0,
          milestones: null,
        }}
      />,
    );
    expect(screen.queryByText("Prototype Vendor")).toBeNull();
    expect(screen.getByText(/does not use synthetic enrichment/)).toBeInTheDocument();
  });

  it("marks synthetic fields in HYBRID mode", () => {
    render(
      <SyntheticFieldsPanel
        mode="HYBRID"
        enrichment={{
          label: "SYNTHETIC",
          disclaimer: "SYNTHETIC prototype enrichment. Not an official MPLADS field.",
          implementing_district: "Kurnool",
          implementing_agency: null,
          vendor_name: "Prototype Vendor",
          sanction_date: "2023-07-01",
          start_date: "2023-07-20",
          planned_start_date: null,
          planned_completion_date: null,
          completion_date: null,
          actual_start_date: null,
          actual_completion_date: null,
          expenditure: 120000,
          gps_latitude: 15.8,
          gps_longitude: 78,
          physical_progress_percent: 40,
          milestones: { number: 2, amount: 60000, total_amount: 120000 },
        }}
      />,
    );
    expect(screen.getByText("Prototype Vendor")).toBeInTheDocument();
    expect(screen.getAllByText("SYNTHETIC").length).toBeGreaterThan(0);
    expect(screen.getByText(/not an official MPLADS field/i)).toBeInTheDocument();
  });
});
