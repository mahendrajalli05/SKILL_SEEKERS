import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ImageForensicsPanel } from "@/components/ImageForensicsPanel";
import type { ImageForensicsResponse } from "@/lib/types";

const forensic: ImageForensicsResponse = {
  image_id: 21,
  project_id: 1,
  data_mode: "REAL",
  integrity: {
    status: "INTEGRITY_OK",
    readable: true,
    content_sha256: "abc",
    stored_sha256: "abc",
    bytes_unmodified: true,
    mime_type: "image/png",
    file_size: 1200,
    notes: ["Original bytes are unchanged."],
  },
  metadata_signal: {
    name: "metadata_signal",
    result: "INCONCLUSIVE",
    confidence_label: "INCONCLUSIVE",
    confidence: 0.18,
    available: false,
    findings: [],
    notes: ["Missing EXIF is not proof of manipulation."],
    details: { display: "TIMESTAMP_AVAILABLE" },
  },
  transformation: {},
  manipulation_signal: {
    name: "manipulation_signal",
    result: "POTENTIAL_MANIPULATION",
    confidence_label: "MEDIUM",
    confidence: 0.5,
    available: true,
    findings: ["Potential signal"],
    notes: ["not proof"],
    details: {},
  },
  ai_generation_signal: {
    name: "ai_generation_signal",
    result: "AI_GENERATION_ANALYSIS_UNAVAILABLE",
    confidence_label: "INCONCLUSIVE",
    confidence: 0,
    available: false,
    findings: ["No suitable detector"],
    notes: [],
    details: {},
  },
  reuse_signal: {
    name: "reuse_signal",
    result: "UNIQUE",
    confidence_label: "LOW",
    confidence: 0.4,
    available: true,
    findings: [],
    notes: [],
    details: {},
  },
  quality_signal: {
    name: "quality_signal",
    result: "NO_STRONG_FORENSIC_SIGNAL",
    confidence_label: "LOW",
    confidence: 0.4,
    available: true,
    findings: [],
    notes: [],
    details: {},
  },
  overall_assessment: "REVIEW_REQUIRED",
  prototype_assessment_label: "Prototype forensic assessment — not a validated authenticity decision.",
  evidence_confidence: 0.4,
  confidence_label: "MEDIUM",
  explanation: "Prototype forensic assessment for review.",
  limitations: ["No validated AI-generated-image detector is bundled in V1."],
  plan_claim_evidence: {
    claim: "Photo shows completed work.",
    forensic: "Potential image reuse detected.",
    result: "Review required.",
    note: "Forensic findings do not mark the claim false.",
    claim_marked_false: false,
  },
  evidence_ids: ["ev:forensics:1:IMAGE_FORENSIC_MANIPULATION:REAL:abc"],
  provenance: { notes: "officer upload" },
  engine_version: "image-forensics-v1",
  note: "decision-support only",
  external_transmission: false,
  bytes_unmodified: true,
  thumbnail_data_url: "data:image/jpeg;base64,AAAA",
  finding: "REVIEW_REQUIRED",
  source: "image-forensics-v1",
  filename: "TEST_progress.png",
  mime_type: "image/png",
  file_size: 1200,
  ahash: "11",
  dhash: "22",
  phash: "33",
  content_sha256: "abc",
  synthetic: false,
  synthetic_label: null,
  ai_generation_analysis: "AI_GENERATION_ANALYSIS_UNAVAILABLE",
};

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation(async (url: string) => {
      const text = String(url);
      if (text.includes("/forensics")) {
        return { ok: true, json: async () => forensic };
      }
      return {
        ok: true,
        json: async () => ({
          project_id: 1,
          internal_project_id: "internal:test",
          summary: {
            images_submitted: 1,
            exact_duplicates: 0,
            potential_reuse: 0,
            gps_available: 0,
            gps_unavailable: 1,
            metadata_available: 0,
            metadata_unavailable: 1,
            quality_warnings: 0,
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
              data_mode: "REAL",
              thumbnail_data_url: "data:image/jpeg;base64,AAAA",
              authenticity: { capability: "NOT_IMPLEMENTED", result: "INCONCLUSIVE", explanation: "", score: null },
              engine_version: "image-evidence-v1",
              limitations: [],
              exact_matches: [],
              reuse_matches: [],
              metadata_fields: [],
              quality: {},
              evidence_ids: [],
              note: "",
            },
          ],
          note: "",
        }),
      };
    }),
  );
});

describe("ImageForensicsPanel", () => {
  it("shows image, signals, confidence, overall assessment, and limitations", async () => {
    render(<ImageForensicsPanel projectId={1} mode="REAL" />);
    expect(await screen.findByText("Image Forensics")).toBeInTheDocument();
    expect(screen.getByText("TEST_progress.png")).toBeInTheDocument();
    expect(screen.getByText(/Integrity:/)).toBeInTheDocument();
    expect(screen.getByText(/Timestamp available/)).toBeInTheDocument();
    expect(screen.getByText(/No match/)).toBeInTheDocument();
    expect(screen.getByText(/Potential signal/)).toBeInTheDocument();
    expect(screen.getByText(/Inconclusive/)).toBeInTheDocument();
    expect(screen.getByText(/REVIEW REQUIRED/)).toBeInTheDocument();
    expect(screen.getByText(/Photo shows completed work/)).toBeInTheDocument();
    expect(screen.getByText(/Review required/)).toBeInTheDocument();
    expect(screen.getAllByText(/not a validated authenticity decision/).length).toBeGreaterThan(0);
    expect(document.body.textContent?.toLowerCase()).not.toContain("fraud");
    expect(document.body.textContent?.toLowerCase()).not.toContain("this image is fake");
    expect(document.body.textContent?.toLowerCase()).not.toContain("definitely ai-generated");
    await userEvent.click(screen.getByRole("button", { name: "Run forensics" }));
  });
});
