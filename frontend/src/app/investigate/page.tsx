"use client";

import { useRouter, useSearchParams } from "next/navigation";

import { DataModeBanner } from "@/components/DataModeBanner";
import { PageHeader } from "@/components/system/PageHeader";
import { ProjectSelector } from "@/components/system/ProjectSelector";
import { FEATURE_EXPLANATIONS } from "@/lib/explanations";
import { parseDataMode, withModePath } from "@/lib/display";

export default function InvestigateHubPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const mode = parseDataMode(searchParams.get("mode"));
  return (
    <div className="space-y-6">
      <PageHeader
        kicker="Investigation"
        title="Investigation Workspace"
        explanation={FEATURE_EXPLANATIONS.workspace}
      />
      <DataModeBanner mode={mode} />
      <ProjectSelector
        mode={mode}
        heading="Choose a project to investigate"
        onSelect={(item) => router.push(withModePath(`/projects/${item.id}/investigate`, mode))}
      />
    </div>
  );
}
