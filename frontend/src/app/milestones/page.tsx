"use client";

import { MilestoneAdvisorPanel } from "@/components/MilestoneAdvisorPanel";
import { ProjectFeaturePage } from "@/components/system/ProjectFeaturePage";
import { FEATURE_EXPLANATIONS, NO_FUND_RELEASE } from "@/lib/explanations";

export default function MilestonesPage() {
  return (
    <ProjectFeaturePage
      kicker="Lifecycle"
      title="MILESTONE & FUNDING REVIEW"
      explanation={FEATURE_EXPLANATIONS.milestone}
    >
      {(projectId, mode) => (
        <div className="space-y-4">
          <p className="text-sm text-[var(--muted)]">{NO_FUND_RELEASE}</p>
          <MilestoneAdvisorPanel projectId={projectId} mode={mode} />
        </div>
      )}
    </ProjectFeaturePage>
  );
}
