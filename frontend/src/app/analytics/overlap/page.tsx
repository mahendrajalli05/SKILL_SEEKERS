"use client";

import { OverlapAnalyticsView } from "@/components/system/AnalyticsViews";
import { ProjectFeaturePage } from "@/components/system/ProjectFeaturePage";
import { FEATURE_EXPLANATIONS } from "@/lib/explanations";

export default function OverlapDetectionPage() {
  return (
    <ProjectFeaturePage
      kicker="Analytics"
      title="OVERLAP DETECTION"
      explanation={FEATURE_EXPLANATIONS.overlap}
    >
      {(projectId, mode) => <OverlapAnalyticsView projectId={projectId} mode={mode} />}
    </ProjectFeaturePage>
  );
}
