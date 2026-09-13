import type { ReactNode } from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ProjectHeader } from "@/components/ProjectHeader";
import type { ProjectDetail } from "@/lib/types";
import { SCHEME_ID_NOTE, UNAVAILABLE_REAL_LABEL } from "@/lib/display";

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

const project: ProjectDetail = {
  id: 1,
  scheme_id: "SVK-AP-000001",
  scheme_id_note: SCHEME_ID_NOTE,
  internal_project_id: "internal:test",
  internal_id_kind: "internal_surrogate_hash",
  internal_id_scheme: "sarvsakshi_internal_work_v1",
  source_dataset: "github_vonter_india-mplads-works_MPLADS.csv",
  mp_name: "Test MP",
  work_description: "Construction of water tanks",
  category: "Normal/Others",
  state: "Andhra Pradesh",
  constituency: "KURNOOL",
  ida: "Kurnool_IDA",
  city: null,
  ward: null,
  block: null,
  village: null,
  recommended_date: "2023-06-01",
  allocation_amount: 500000,
  ida_approval: null,
  status: "Ongoing",
  house: "Lok Sabha",
  lifecycle_stage: "ONGOING",
  is_synthetic: false,
  synthetic_label: null,
  has_hybrid_enrichment: false,
  hybrid_notice: null,
  amount_unit_note: "Source amount unit is unspecified.",
  unavailable_fields: [],
  snapshot_source_url: null,
  snapshot_extracted_at: null,
  snapshot_download_date: null,
  snapshot_publisher: null,
  snapshot_notes: null,
  snapshot_original_filename: null,
  data_mode_default: "HYBRID",
  data_mode: "REAL",
  synthetic_enrichment: null,
};

describe("ProjectHeader", () => {
  it("renders Scheme ID separately from the internal project ID", () => {
    render(
      <ProjectHeader
        project={{ ...project, constituency: "", status: null }}
        dataMode="REAL"
        investigateHref="/projects/1/investigate"
      />,
    );
    expect(screen.getByText("Construction of water tanks")).toBeInTheDocument();
    expect(screen.getByText("SVK-AP-000001")).toBeInTheDocument();
    expect(screen.getByText("internal:test")).toBeInTheDocument();
    expect(screen.getAllByText(/not an official MPLADS Work ID/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(UNAVAILABLE_REAL_LABEL).length).toBeGreaterThan(0);
    expect(screen.getByText(/unit unspecified/)).toBeInTheDocument();
    expect(screen.getAllByText("REAL").length).toBeGreaterThan(0);
  });
});
