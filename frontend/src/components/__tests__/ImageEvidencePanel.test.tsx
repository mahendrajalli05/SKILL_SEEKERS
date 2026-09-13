import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ImageEvidencePanel } from "@/components/ImageEvidencePanel";

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        project_id: 1,
        internal_project_id: "internal:test",
        summary: {
          images_submitted: 5,
          exact_duplicates: 1,
          potential_reuse: 2,
          gps_available: 3,
          gps_unavailable: 2,
          metadata_available: 3,
          metadata_unavailable: 2,
          quality_warnings: 1,
          advanced_authenticity_analysis: "INCONCLUSIVE",
          authenticity_capability: "NOT_IMPLEMENTED",
          evidence_confidence: 0.45,
          note: "supporting evidence only",
        },
        items: [
          {
            image_id: 21,
            project_id: 1,
            filename: "TEST_progress.png",
            mime_type: "image/png",
            file_size: 1200,
            uploaded_at: "2026-09-10T00:00:00+00:00",
            content_sha256: "abc",
            ahash: "11",
            dhash: "22",
            phash: "33",
            integrity_status: "POTENTIAL_IMAGE_REUSE",
            duplicate_of_id: null,
            analysis_status: "ANALYZED",
            attached_to_evidence: false,
            data_mode: "REAL",
            source: "officer_upload",
            provenance: { notes: "officer upload" },
            thumbnail_data_url: "data:image/jpeg;base64,AAAA",
            exact_duplicate: false,
            potential_reuse: true,
            exact_matches: [],
            reuse_matches: [
              {
                image_id: 21,
                matched_image_id: 20,
                matched_project_id: 1,
                hash_name: "dhash",
                distance: 4,
                hash_similarity: 0.94,
                explanation:
                  "Perceptual dhash distance is 4 of 64 bits versus image 20. POTENTIAL_IMAGE_REUSE. High visual similarity alone is not proof of wrongdoing.",
                confidence: 0.8,
                data_mode: "REAL",
              },
            ],
            metadata_status: "METADATA_UNAVAILABLE",
            metadata_fields: [],
            gps_available: false,
            gps_message: "GPS metadata unavailable.",
            capture_timestamp: null,
            latitude: null,
            longitude: null,
            quality: {
              readable: true,
              width: 96,
              height: 96,
              warnings: ["Resolution is below a useful size for site evidence."],
            },
            authenticity: {
              capability: "NOT_IMPLEMENTED",
              result: "INCONCLUSIVE",
              explanation: "Advanced analysis is INCONCLUSIVE.",
              score: null,
            },
            evidence_ids: ["ev:image:1:IMAGE_QUALITY:REAL:abc"],
            evidence_confidence: 0.45,
            engine_version: "image-evidence-v1",
            note: "not a legal finding",
            limitations: [
              "This photograph is supporting evidence only.",
              "Advanced authenticity analysis: INCONCLUSIVE (NOT_IMPLEMENTED).",
            ],
          },
        ],
        note: "",
      }),
    }),
  );
});

describe("ImageEvidencePanel", () => {
  it("shows upload, thumbnail, metadata, hashes, reuse, and limitations", async () => {
    render(<ImageEvidencePanel projectId={1} mode="REAL" />);
    expect(await screen.findByText("Image Evidence")).toBeInTheDocument();
    expect(screen.getByText("TEST_progress.png")).toBeInTheDocument();
    expect(screen.getByText("REAL")).toBeInTheDocument();
    expect(screen.getByText(/SHA-256 abc/)).toBeInTheDocument();
    expect(screen.getAllByText(/POTENTIAL_IMAGE_REUSE/).length).toBeGreaterThan(0);
    expect(screen.getByText(/GPS metadata unavailable/)).toBeInTheDocument();
    expect(screen.getAllByText(/INCONCLUSIVE/).length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Upload image" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Analyze" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Attach to Evidence" })).toBeInTheDocument();
    expect(document.body.textContent).toContain("Images submitted:");
    expect(document.body.textContent).toContain("Advanced authenticity analysis:");
    expect(document.body.textContent?.toLowerCase()).not.toContain("fraud detected");
    expect(document.body.textContent?.toLowerCase()).not.toContain("this is fraud");
    await userEvent.click(screen.getByRole("button", { name: "Attach to Evidence" }));
  });
});
