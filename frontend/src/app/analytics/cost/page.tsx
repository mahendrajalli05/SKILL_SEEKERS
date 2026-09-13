"use client";

import { CostAnalyticsView } from "@/components/system/AnalyticsViews";
import { ProjectFeaturePage } from "@/components/system/ProjectFeaturePage";
import { FEATURE_EXPLANATIONS } from "@/lib/explanations";

export default function CostIntelligencePage() {
  return (
    <ProjectFeaturePage
      kicker="Analytics"
      title="COST INTELLIGENCE"
      explanation={FEATURE_EXPLANATIONS.cost}
    >
      {(projectId, mode) => <CostAnalyticsView projectId={projectId} mode={mode} />}
    </ProjectFeaturePage>
  );
}
