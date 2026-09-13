import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PlanClaimEvidencePanel, VerificationResultBlock } from "@/components/PlanClaimEvidencePanel";
import type { VerificationRead } from "@/lib/types";

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        project_id: 1,
        internal_project_id: "internal:test",
        data_mode: "REAL",
        sanctioned_scope: "Community hall",
        budget_estimate: 2000000,
        budget_from_extract: true,
        blueprint_document_id: null,
        dimensions_value: null,
        dimensions_unit: null,
        milestone_label: null,
        milestone_amount: null,
        planned_start_date: null,
        planned_completion_date: null,
        source: "project.work_description",
        recorded: false,
        fields: [
          {
            name: "dimensions_value",
            value: null,
            available: false,
            data_mode: "REAL",
            synthetic: false,
            source: "unavailable",
            unavailable_reason: "Dimensions/quantity are not present in the current public MPLADS extract.",
          },
        ],
        provenance: { data_mode: "REAL" },
        note: "",
        items: [],
      }),
    }),
  );
});

function result(overall: VerificationRead["overall_result"]): VerificationRead {
  return {
    project_id: 1,
    internal_project_id: "internal:test",
    overall_result: overall,
    data_mode: "REAL",
    plan_findings: ["Plan dimensions are 2000 sq.ft."],
    claim_findings: ["Recorded claim is a statement under evaluation, not an established fact."],
    evidence_findings: ["1 supporting evidence attachment(s) recorded."],
    mismatches:
      overall === "MISMATCH"
        ? [
            {
              comparison_id: "quantity_claim_vs_evidence",
              pair: "CLAIM_VS_EVIDENCE",
              field: "quantity",
              status: "MISMATCH",
              left_value: 2000,
              right_value: 800,
              explanation: "Claimed quantity is 2,000 sq.ft and evidence quantity is 800 sq.ft.",
              missing_information: [],
            },
          ]
        : [],
    missing_information: overall === "INCONCLUSIVE" ? ["plan dimensions", "claimed quantity"] : [],
    comparisons: [],
    evidence_confidence: overall === "INCONCLUSIVE" ? 0.12 : 0.7,
    explanation:
      overall === "INCONCLUSIVE"
        ? "Claimed completion is 100%, but the submitted evidence does not contain sufficient information to verify the claimed dimensions."
        : overall === "MISMATCH"
          ? "Available evidence indicates a substantially different quantity."
          : "Claimed expenditure is ₹19 lakh and the available milestone allocation is ₹15 lakh. No expenditure mismatch was identified from the supplied evidence.",
    provenance: { data_mode: "REAL", notes: "real MPLADS project records" },
    evidence_ids: ["ev:pce:1:plan_claim_evidence:REAL:abc"],
    note: "Results are CONSISTENT, MISMATCH, or INCONCLUSIVE. This is not a legal finding.",
  };
}

describe("VerificationResultBlock", () => {
  it("shows CONSISTENT without fraud wording", () => {
    render(<VerificationResultBlock result={result("CONSISTENT")} />);
    expect(screen.getByText("CONSISTENT")).toBeInTheDocument();
    expect(screen.getByText(/No expenditure mismatch/)).toBeInTheDocument();
    expect(document.body.textContent?.toLowerCase()).not.toContain("fraud detected");
  });

  it("shows MISMATCH reasons", () => {
    render(<VerificationResultBlock result={result("MISMATCH")} />);
    expect(screen.getByText("MISMATCH")).toBeInTheDocument();
    expect(screen.getByText(/substantially different quantity/)).toBeInTheDocument();
    expect(screen.getByText(/CLAIM_VS_EVIDENCE/)).toBeInTheDocument();
  });

  it("shows INCONCLUSIVE missing information", () => {
    render(<VerificationResultBlock result={result("INCONCLUSIVE")} />);
    expect(screen.getByText("INCONCLUSIVE")).toBeInTheDocument();
    expect(screen.getByText("plan dimensions")).toBeInTheDocument();
    expect(screen.getByText("claimed quantity")).toBeInTheDocument();
    expect(screen.getByText(/sufficient information to verify the claimed dimensions/)).toBeInTheDocument();
  });
});

describe("PlanClaimEvidencePanel tabs", () => {
  it("renders PLAN CLAIM EVIDENCE RESULT controls", async () => {
    render(<PlanClaimEvidencePanel projectId={1} mode="REAL" />);
    expect(screen.getByRole("button", { name: "PLAN" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "CLAIM" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "EVIDENCE" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "RESULT" })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "CLAIM" }));
    expect(screen.getByText(/statements being evaluated/)).toBeInTheDocument();
    expect(document.body.textContent?.toLowerCase()).not.toContain("fraud detected");
  });
});
