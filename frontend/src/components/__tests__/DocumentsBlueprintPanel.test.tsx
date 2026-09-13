import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { DocumentsBlueprintPanel } from "@/components/DocumentsBlueprintPanel";

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        project_id: 1,
        items: [
          {
            document_id: 11,
            project_id: 1,
            filename: "TEST_blueprint.pdf",
            mime_type: "application/pdf",
            document_type: "BLUEPRINT",
            uploaded_at: "2026-09-10T00:00:00+00:00",
            data_mode: "REAL",
            provenance: { notes: "officer upload" },
            content_sha256: "abc",
            file_size: 1200,
            extraction_status: "EXTRACTED",
            integrity_status: "UNIQUE",
            duplicate_of_id: null,
            attached_to_plan: false,
            attached_to_evidence: false,
            observed_quantity: 2000,
            observed_quantity_unit: "sq.ft",
            observed_expenditure: null,
            extraction: {
              status: "EXTRACTED",
              extraction_method: "pdf_text",
              fields: [
                {
                  name: "area",
                  value: 2000,
                  unit: "sq.ft",
                  confidence: 0.94,
                  extraction_method: "regex",
                  source_location: "page 1",
                  available: true,
                  unavailable_reason: null,
                },
              ],
              structure: {},
              page_count: 1,
              raw_text_available: true,
              notes: [],
              text_sha256: "def",
            },
            engine_version: "document-blueprint-v1",
            note: "not a legal finding",
          },
        ],
        conflicts: [
          {
            field: "area",
            result: "PLAN_DATA_CONFLICT",
            sources: [],
            explanation: "Blueprint 2000 sq.ft and BOQ 800 sq.ft. No source was chosen as truth.",
          },
        ],
        note: "",
      }),
    }),
  );
});

describe("DocumentsBlueprintPanel", () => {
  it("shows documents, REAL label, confidence, and conflicts", async () => {
    render(<DocumentsBlueprintPanel projectId={1} mode="REAL" />);
    expect(await screen.findByText("Documents / Blueprint")).toBeInTheDocument();
    expect(screen.getByText("TEST_blueprint.pdf")).toBeInTheDocument();
    expect(screen.getByText("REAL")).toBeInTheDocument();
    expect(screen.getByText(/EXTRACTION CONFIDENCE: 94%/)).toBeInTheDocument();
    expect(screen.getByText(/page 1/)).toBeInTheDocument();
    expect(screen.getByText("PLAN DATA CONFLICT")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Extract" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Attach to Plan" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Attach to Evidence" })).toBeInTheDocument();
    expect(document.body.textContent?.toLowerCase()).not.toContain("fraud detected");
    await userEvent.selectOptions(screen.getByLabelText("Document type"), "BOQ_ESTIMATE");
    expect((screen.getByLabelText("Document type") as HTMLSelectElement).value).toBe("BOQ_ESTIMATE");
  });
});
