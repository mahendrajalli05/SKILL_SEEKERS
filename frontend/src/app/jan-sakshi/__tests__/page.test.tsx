import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import JanSakshiPage from "@/app/jan-sakshi/page";

vi.mock("@/lib/api", () => ({
  fetchProjectOptions: vi.fn(async () => ({
    states: ["Andhra Pradesh"],
    constituencies: ["VIZIANAGARAM"],
    excluded_non_geographic_constituencies: [],
    categories: ["Roads"],
    statuses: ["Ongoing"],
    constituency_enabled: true,
    constituency_placeholder: null,
    selected_state: "Andhra Pradesh",
    pilot_label: "Andhra Pradesh",
    note: "",
  })),
  fetchProjects: vi.fn(async () => ({
    items: [
      {
        id: 11,
        scheme_id: "SVK-AP-000011",
        internal_project_id: "internal:citizen:ui",
        work_description: "Construction of rural road",
        constituency: "VIZIANAGARAM",
        category: "Roads",
        status: "Ongoing",
        state: "Andhra Pradesh",
        mp_name: "Test MP",
        allocation_amount: 1500000,
        recommended_date: "2023-06-01",
        has_hybrid_enrichment: true,
        data_mode: "HYBRID",
        is_synthetic: false,
        synthetic_label: null,
      },
    ],
    total: 1,
    page: 1,
    page_size: 8,
    q: "road",
    constituency: null,
    category: null,
    status: null,
    state: null,
    scheme_id: null,
    apply_pilot_scope: true,
    effective_state: "Andhra Pradesh",
    data_mode: "HYBRID",
    pilot_label: "Andhra Pradesh",
    constituency_filter_applied: false,
    ignored_non_geographic_constituency: null,
    scheme_id_note: "",
    note: "",
  })),
  submitCitizenReport: vi.fn(async () => ({
    citizen_report_id: 1,
    project_id: 11,
    scheme_id: "SVK-AP-000011",
    internal_project_id: "internal:citizen:ui",
    satisfaction_rating: 4,
    observation_text: "The completed road is useful and in good condition for villagers.",
    issue_category: "other",
    submitted_at: "2026-09-10T09:15:00+00:00",
    image_id: null,
    submission_status: "ACCEPTED",
    verification_result: "LOCATION_VERIFIED",
    timestamp_status: "TIMESTAMP_RECORDED",
    data_mode: "HYBRID",
    provenance: {},
    location_verification: { result: "LOCATION_VERIFIED" },
    analysis: { sentiment: "positive" },
    duplicate: null,
    watermark: null,
    plan_claim_evidence: null,
    evidence_ids: [],
    rejection_reason: null,
    reasons: ["Citizen GPS is within the configured 500 metre prototype threshold."],
    synthetic: true,
    synthetic_badge: "HYBRID/TEST",
    thumbnail_data_url: null,
    original_image_preserved: true,
    engine_version: "jan-sakshi-v1",
    engine_name: "citizen",
    governance_note: "supporting field evidence only",
  })),
}));

describe("Jan-Sakshi citizen page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("lets a citizen select a project and see the validation result", async () => {
    const user = userEvent.setup();
    render(<JanSakshiPage />);
    expect(screen.getByText("JAN-SAKSHI")).toBeInTheDocument();
    await user.type(screen.getByPlaceholderText(/Scheme ID/i), "road");
    await user.click(screen.getByRole("button", { name: "Search" }));
    await user.click(await screen.findByText(/SVK-AP-000011/));
    await user.type(
      screen.getByLabelText("Observation"),
      "The completed road is useful and in good condition for villagers.",
    );
    await user.click(screen.getByRole("button", { name: "Submit Field Evidence" }));
    expect(await screen.findByText(/LOCATION_VERIFIED/)).toBeInTheDocument();
    expect(screen.getByText(/supporting field evidence only/i)).toBeInTheDocument();
  });
});
