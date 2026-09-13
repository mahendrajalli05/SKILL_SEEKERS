"use client";

import { useParams, useSearchParams } from "next/navigation";

import { RelationshipGraphPanel } from "@/components/RelationshipGraphPanel";
import { PageHeader } from "@/components/system/PageHeader";
import { FEATURE_EXPLANATIONS } from "@/lib/explanations";
import { parseDataMode } from "@/lib/display";

export default function RelationshipGraphPage() {
  const params = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const projectId = Number(params.id);
  const mode = parseDataMode(searchParams.get("mode"));

  if (!Number.isFinite(projectId)) {
    return <p>Invalid project id.</p>;
  }

  return (
    <div className="space-y-4">
      <PageHeader
        title="Relationship Graph"
        explanation={FEATURE_EXPLANATIONS.graph}
      />
      <p className="text-sm text-[var(--muted)]">
        Officer view of the stored Relationship Graph V1 neighborhood for this work.
        Central project, connected nodes, relationship details, graph finding, and
        graph evidence are shown from the stored graph API.
      </p>
      <RelationshipGraphPanel projectId={projectId} mode={mode} />
    </div>
  );
}
