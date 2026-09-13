"use client";

import { SatelliteRemoteSensingPanel } from "@/components/SatelliteRemoteSensingPanel";
import { ProjectFeaturePage } from "@/components/system/ProjectFeaturePage";
import { FEATURE_EXPLANATIONS } from "@/lib/explanations";

export default function SatellitePage() {
  return (
    <ProjectFeaturePage
      kicker="Verification"
      title="SATELLITE VERIFICATION"
      explanation={FEATURE_EXPLANATIONS.satellite}
    >
      {(projectId, mode) => <SatelliteRemoteSensingPanel projectId={projectId} mode={mode} />}
    </ProjectFeaturePage>
  );
}
