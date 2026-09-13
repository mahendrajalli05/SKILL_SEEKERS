"use client";

import { ContextualIntelligencePanel } from "@/components/ContextualIntelligencePanel";
import { ProjectFeaturePage } from "@/components/system/ProjectFeaturePage";
import { FEATURE_EXPLANATIONS } from "@/lib/explanations";

export default function ContextPage() {
  return (
    <ProjectFeaturePage
      kicker="Context"
      title="CONTEXTUAL INTELLIGENCE"
      explanation={FEATURE_EXPLANATIONS.context}
    >
      {(projectId, mode) => <ContextualIntelligencePanel projectId={projectId} mode={mode} />}
    </ProjectFeaturePage>
  );
}
