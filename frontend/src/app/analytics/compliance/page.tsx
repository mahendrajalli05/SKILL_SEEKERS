"use client";

import { ComplianceAnalyticsView } from "@/components/system/AnalyticsViews";
import { ProjectFeaturePage } from "@/components/system/ProjectFeaturePage";
import { FEATURE_EXPLANATIONS } from "@/lib/explanations";

export default function CompliancePage() {
  return (
    <ProjectFeaturePage
      kicker="Analytics"
      title="COMPLIANCE"
      explanation={FEATURE_EXPLANATIONS.compliance}
    >
      {(projectId, mode) => <ComplianceAnalyticsView projectId={projectId} mode={mode} />}
    </ProjectFeaturePage>
  );
}
