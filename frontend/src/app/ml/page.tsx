"use client";

import { MlEvidencePanel } from "@/components/MlEvidencePanel";
import { ProjectFeaturePage } from "@/components/system/ProjectFeaturePage";
import { FEATURE_EXPLANATIONS } from "@/lib/explanations";
import { useProjectIntelligence } from "@/lib/useProjectIntelligence";
import type { DataMode } from "@/lib/types";

function MlBody({ projectId, mode }: { projectId: number; mode: DataMode }) {
  const intel = useProjectIntelligence(projectId, mode);
  return (
    <MlEvidencePanel
      projectId={projectId}
      mode={mode}
      items={intel.evidence.data?.items ?? []}
      onCreated={intel.reloadEvidence}
    />
  );
}

export default function MlPage() {
  return (
    <ProjectFeaturePage kicker="AI & Models" title="ML Signals" explanation={FEATURE_EXPLANATIONS.ml}>
      {(projectId, mode) => <MlBody projectId={projectId} mode={mode} />}
    </ProjectFeaturePage>
  );
}
