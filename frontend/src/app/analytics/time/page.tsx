"use client";

import { TimeAnalyticsView } from "@/components/system/AnalyticsViews";
import { ProjectFeaturePage } from "@/components/system/ProjectFeaturePage";
import { FEATURE_EXPLANATIONS } from "@/lib/explanations";

export default function TimeIntelligencePage() {
  return (
    <ProjectFeaturePage
      kicker="Analytics"
      title="TIME INTELLIGENCE"
      explanation={FEATURE_EXPLANATIONS.time}
    >
      {(projectId, mode) => <TimeAnalyticsView projectId={projectId} mode={mode} />}
    </ProjectFeaturePage>
  );
}
