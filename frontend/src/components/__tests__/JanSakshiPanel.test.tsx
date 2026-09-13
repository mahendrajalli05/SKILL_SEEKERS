import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { JanSakshiPanel } from "@/components/JanSakshiPanel";
import { CitizenEvidenceSummary } from "@/components/CitizenEvidenceSummary";
import type { CitizenReportList, CitizenSummary } from "@/lib/types";

const summary: CitizenSummary = {
  project_id: 11,
  internal_project_id: "internal:citizen:subject",
  scheme_id: "SVK-AP-000001",
  data_mode: "HYBRID",
  total_submissions: 3,
  verified_location_submissions: 3,
  rejected_submissions: 0,
  inconclusive_submissions: 0,
  average_satisfaction: 2,
  satisfaction_distribution: { "1": 0, "2": 3, "3": 0, "4": 0, "5": 0 },
  recurring_issue_categories: [{ category: "incomplete_work", label: "Incomplete work", count: 3 }],
  repeated_complaint_themes: ["Incomplete work"],
  citizen_evidence_confidence: 0.32,
  sample_size_status: "Insufficient citizen sample",
  aggregate_finding: "POTENTIAL_COMMUNITY_CONCERN",
  explanation: "Potential community concern: multiple independent citizen reports share a recurring issue category.",
  synthetic_badge: "HYBRID/TEST: labelled SYNTHETIC prototype citizen evidence.",
  investigation_priority_unchanged: true,
  engine_version: "jan-sakshi-v1",
  engine_name: "citizen",
  governance_note: "Jan-Sakshi citizen submissions are supporting field evidence only.",
  privacy_note: "Citizen GPS is verification data and is not exposed in public-facing aggregate results.",
  limitations: ["Citizen evidence is supporting evidence only."],
};

const list: CitizenReportList = {
  project_id: 11,
  internal_project_id: "internal:citizen:subject",
  data_mode: "HYBRID",
  items: [
    {
      citizen_report_id: 1,
      project_id: 11,
      scheme_id: "SVK-AP-000001",
      internal_project_id: "internal:citizen:subject",
      satisfaction_rating: 2,
      observation_text: "Road remains incomplete in section X.",
      issue_category: "incomplete_work",
      submitted_at: "2026-09-10T09:15:00+00:00",
      image_id: 4,
      submission_status: "ACCEPTED",
      verification_result: "LOCATION_VERIFIED",
      timestamp_status: "TIMESTAMP_RECORDED",
      data_mode: "HYBRID",
      provenance: {},
      location_verification: { result: "LOCATION_VERIFIED" },
      analysis: { sentiment: "negative" },
      duplicate: { flagged: false },
      watermark: { generated: true, original_preserved: true },
      plan_claim_evidence: { result: "CITIZEN_CONTRADICTION", claim_marked_false: false },
      evidence_ids: [],
      rejection_reason: null,
      reasons: [],
      synthetic: true,
      synthetic_badge: "TEST/SYNTHETIC",
      thumbnail_data_url: null,
      original_image_preserved: true,
      engine_version: "jan-sakshi-v1",
      engine_name: "citizen",
      governance_note: "supporting field evidence only",
    },
  ],
  privacy_note: "Citizen GPS is verification data.",
  threshold_note: "500 m is a prototype rule.",
  governance_note: "supporting evidence only",
  engine_version: "jan-sakshi-v1",
  engine_name: "citizen",
};

vi.mock("@/lib/api", () => ({
  fetchCitizenSummary: vi.fn(async () => summary),
  fetchCitizenReports: vi.fn(async () => list),
}));

describe("Jan-Sakshi officer surfaces", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows citizen summary without GPS", async () => {
    render(<CitizenEvidenceSummary projectId={11} mode="HYBRID" />);
    expect(await screen.findByText("Citizen Evidence")).toBeInTheDocument();
    expect(await screen.findByText("Insufficient citizen sample")).toBeInTheDocument();
    expect(screen.queryByText(/18\.11/)).not.toBeInTheDocument();
    expect(screen.getByText(/Investigation Priority is not changed/i)).toBeInTheDocument();
  });

  it("shows verified citizen reports and PCE framing", async () => {
    render(<JanSakshiPanel projectId={11} mode="HYBRID" />);
    expect(await screen.findByText("JAN-SAKSHI")).toBeInTheDocument();
    expect(await screen.findByText(/ACCEPTED \/ LOCATION_VERIFIED/)).toBeInTheDocument();
    expect(screen.getByText(/Claim is not marked false/)).toBeInTheDocument();
    expect(screen.queryByText(/longitude/i)).not.toBeInTheDocument();
  });
});
