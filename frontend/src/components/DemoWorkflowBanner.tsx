"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";

import { DemoCaseNotice } from "@/components/DemoCaseNotice";
import { parseDataMode, withModePath } from "@/lib/display";

const CASE_LABEL: Record<string, string> = {
  ghost: "GHOST",
  overbill: "OVER-BILL",
  stuck: "STUCK",
  clean: "CLEAN",
};

export function DemoWorkflowBanner() {
  const params = useParams<{ id?: string }>();
  const searchParams = useSearchParams();
  const demo = (searchParams.get("demo") || "").trim().toLowerCase();
  const label = CASE_LABEL[demo];
  if (!label) {
    return null;
  }
  const mode = parseDataMode(searchParams.get("mode"));
  const id = params.id;
  return (
    <div className="mb-6 space-y-3">
      <DemoCaseNotice caseName={`Demo case: ${label}`} />
      <div className="flex flex-wrap gap-2 text-sm">
        <Link href={withModePath(`/demo/${demo}`, mode)} className="svk-btn svk-btn-primary">
          Open demo journey
        </Link>
        {id ? (
          <Link href={withModePath(`/projects/${id}/investigate`, mode)} className="svk-btn">
            Investigation Workspace
          </Link>
        ) : null}
      </div>
    </div>
  );
}
