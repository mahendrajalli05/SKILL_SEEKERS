"use client";

import { InvestigationCopilotPanel } from "@/components/InvestigationCopilotPanel";
import { ProjectFeaturePage } from "@/components/system/ProjectFeaturePage";
import { FEATURE_EXPLANATIONS } from "@/lib/explanations";

export default function CopilotPage() {
  return (
    <ProjectFeaturePage
      kicker="AI & Models"
      title="INVESTIGATION COPILOT"
      explanation={FEATURE_EXPLANATIONS.copilot}
    >
      {(projectId, mode) => <InvestigationCopilotPanel projectId={projectId} mode={mode} />}
    </ProjectFeaturePage>
  );
}
