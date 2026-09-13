import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import NeedImpactPage from "@/app/need-impact/page";
import type { NeedImpactRankResponse } from "@/lib/types";

const payload: NeedImpactRankResponse = {
  items: [
    {
      rank: 1,
      project_id: 1,
      internal_project_id: "internal:a",
      constituency: "VIZIANAGARAM",
      category: "Drinking Water",
      requested_amount: 3000000,
      priority_score: 91,
      priority_class: "HIGH PRIORITY",
      evidence_confidence: 0.7,
      rationale: "HIGH PRIORITY: prototype Priority Score 91. Priority recommendation only.",
      why_ranked_above: "Ranked above project 2 because Priority Score 91 > 40.",
      why_ranked_below: null,
      within_hypothetical_budget: true,
      budget_note: "Included in the hypothetical remaining-budget simulation. This is not a sanction.",
      need_score: 90,
      impact_score: 85,
      data_mode: "HYBRID",
      finding: "HIGH PRIORITY",
      top_reasons: [],
      unavailable_inputs: [],
      automatic_sanction: false,
    },
  ],
  unranked: [
    {
      rank: null,
      project_id: 9,
      internal_project_id: "internal:real",
      constituency: "GUNTUR",
      category: "Normal/Others",
      requested_amount: 1000000,
      priority_score: null,
      priority_class: "INCONCLUSIVE",
      evidence_confidence: 0.18,
      rationale: "INCONCLUSIVE: Need and Impact could not both be assessed.",
      why_ranked_above: null,
      why_ranked_below: null,
      within_hypothetical_budget: null,
      budget_note: null,
      need_score: null,
      impact_score: 85,
      data_mode: "HYBRID",
      finding: "INCONCLUSIVE",
      top_reasons: [],
      unavailable_inputs: ["Population need"],
      automatic_sanction: false,
    },
  ],
  available_budget: 500000000,
  available_budget_crore: 50,
  remaining_budget: 497000000,
  data_mode: "HYBRID",
  weight_note: "Prototype weighting — not an official MPLADS sanction formula.",
  governance_note:
    "Priority recommendation only. Authorized officials make final administrative decisions.",
  planning_simulation: true,
  automatic_sanction: false,
  sanction_decision: null,
  explanation: "PLANNING SIMULATION only. Hypothetical budget ranking does not execute payments or sanctions.",
  engine_version: "need-impact-v1",
  priority_recommendation_only: true,
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

describe("Need & Impact ranking page", () => {
  it("runs a budget-constrained ranking simulation without sanction language", async () => {
    render(<NeedImpactPage />);
    expect(screen.getByText("Need & Impact")).toBeInTheDocument();
    expect(screen.getByText(/Planning simulation/)).toBeInTheDocument();
    await userEvent.type(screen.getByLabelText(/Candidate project ids/), "1, 9");
    await userEvent.click(screen.getByRole("button", { name: "Rank proposed works" }));
    expect((await screen.findAllByText("HIGH PRIORITY")).length).toBeGreaterThan(0);
    expect(screen.getByText(/Inside hypothetical budget/)).toBeInTheDocument();
    expect(screen.getByText(/INCONCLUSIVE \/ not ranked/)).toBeInTheDocument();
    expect(screen.getByText(/does not execute payments or sanctions/)).toBeInTheDocument();
    expect(screen.getByText(/Automatic sanctioning: false/)).toBeInTheDocument();
    expect(document.body.textContent?.toLowerCase()).not.toContain("sanction approved");
    expect(document.body.textContent?.toLowerCase()).not.toContain("fraud");
  });
});
