import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { NeedImpactPanel } from "@/components/NeedImpactPanel";
import type { NeedImpactResponse } from "@/lib/types";

const payload: NeedImpactResponse = {
  project_id: 11,
  internal_project_id: "internal:need-impact:subject",
  data_mode: "HYBRID",
  constituency: "VIZIANAGARAM",
  category: "Drinking Water",
  work_description: "Construction of drinking water facility",
  requested_amount: 2000000,
  lifecycle_stage: "FUTURE",
  status: "Unsanctioned",
  need_score: 90.1,
  impact_score: 88.6,
  urgency_score: 80,
  priority_score: 87.5,
  priority_class: "HIGH PRIORITY",
  evidence_confidence: 0.7,
  need: {
    name: "need",
    score: 90.1,
    available: true,
    confidence: 0.7,
    finding: "NEED_ASSESSED",
    explanation: "Need Score combines labelled TEST/SYNTHETIC need components.",
    components: [],
    unavailable_inputs: [],
    top_reasons: ["TEST/SYNTHETIC population-need index. Not a census fact."],
  },
  impact: {
    name: "impact",
    score: 88.6,
    available: true,
    confidence: 0.7,
    finding: "IMPACT_ASSESSED",
    explanation: "Impact Score combines available components.",
    components: [],
    unavailable_inputs: ["Beneficiary count"],
    top_reasons: [],
  },
  urgency: {
    name: "urgency",
    score: 80,
    available: true,
    confidence: 0.55,
    finding: "URGENCY_ASSESSED",
    explanation: "Urgency uses supported inputs.",
    components: [],
    unavailable_inputs: [],
    top_reasons: [],
  },
  top_reasons: ["TEST/SYNTHETIC population-need index. Not a census fact."],
  unavailable_inputs: ["Beneficiary count"],
  contextual_evidence: ["Historical project counts are contextual evidence only."],
  explanation:
    "Priority recommendation only. Authorized officials make final administrative decisions. Prototype weighting — not an official MPLADS sanction formula.",
  finding: "HIGH PRIORITY: prototype Priority Score 87.5. Priority recommendation only.",
  weights: { need: 0.45, impact: 0.4, urgency: 0.15 },
  weight_note: "Prototype weighting — not an official MPLADS sanction formula.",
  governance_note:
    "Priority recommendation only. Authorized officials make final administrative decisions.",
  limitations: [],
  constituency_context: {
    constituency: "VIZIANAGARAM",
    usable_as_geography: true,
    constituency_work_count: 12,
    category_work_count: 3,
    used_as_need_score: false,
  },
  enrichment_used: true,
  enrichment_label: "TEST/SYNTHETIC",
  automatic_sanction: false,
  sanction_decision: null,
  evidence_ids: [],
  provenance: {},
  engine_version: "need-impact-v1",
  engine_name: "need",
  priority_recommendation_only: true,
  planning_simulation: false,
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

describe("NeedImpactPanel", () => {
  it("shows scores, unavailable inputs, data mode, and governance wording", async () => {
    render(<NeedImpactPanel projectId={11} mode="HYBRID" />);
    expect((await screen.findAllByText("HIGH PRIORITY")).length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: "Need & Impact" })).toBeInTheDocument();
    expect(screen.getByText("VIZIANAGARAM")).toBeInTheDocument();
    expect(screen.getByText("Drinking Water")).toBeInTheDocument();
    expect(screen.getAllByText("HIGH PRIORITY").length).toBeGreaterThan(0);
    expect(screen.getAllByText("90.1").length).toBeGreaterThan(0);
    expect(screen.getAllByText("88.6").length).toBeGreaterThan(0);
    expect(screen.getAllByText("87.5").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/TEST\/SYNTHETIC/).length).toBeGreaterThan(0);
    expect(screen.getByText(/Beneficiary count/)).toBeInTheDocument();
    expect(screen.getAllByText(/Prototype weighting/).length).toBeGreaterThan(0);
    expect(document.body.textContent?.toLowerCase()).not.toContain("fraud");
    expect(document.body.textContent?.toLowerCase()).not.toContain("sanction approved");
    expect(document.body.textContent?.toLowerCase()).toContain("automatic sanctioning is false");
  });
});
