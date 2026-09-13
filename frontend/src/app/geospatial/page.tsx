"use client";

import { GeospatialEvidencePanel } from "@/components/GeospatialEvidencePanel";
import { ProjectFeaturePage } from "@/components/system/ProjectFeaturePage";
import { FEATURE_EXPLANATIONS } from "@/lib/explanations";

export default function GeospatialPage() {
  return (
    <ProjectFeaturePage
      kicker="Verification"
      title="GEOSPATIAL VERIFICATION"
      explanation={FEATURE_EXPLANATIONS.geo}
    >
      {(projectId, mode) => <GeospatialEvidencePanel projectId={projectId} mode={mode} />}
    </ProjectFeaturePage>
  );
}
