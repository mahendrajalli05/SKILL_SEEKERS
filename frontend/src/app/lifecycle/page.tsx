"use client";

import { ProjectLifecyclePanel } from "@/components/ProjectLifecyclePanel";
import { LifecycleTrack } from "@/components/system/LifecycleTrack";
import { ProjectFeaturePage } from "@/components/system/ProjectFeaturePage";
import { FEATURE_EXPLANATIONS } from "@/lib/explanations";
import { useProjectIntelligence } from "@/lib/useProjectIntelligence";
import type { DataMode } from "@/lib/types";

function LifecycleBody({ projectId, mode }: { projectId: number; mode: DataMode }) {
  const intel = useProjectIntelligence(projectId, mode);
  const state = intel.lifecycle.data?.lifecycle_state ?? intel.project.data?.lifecycle_stage ?? "UNKNOWN";
  return (
    <div className="space-y-5">
      <LifecycleTrack current={state} />
      <ProjectLifecyclePanel
        projectId={projectId}
        mode={mode}
        lifecycle={intel.lifecycle.data}
        loading={intel.lifecycle.loading}
        error={intel.lifecycle.error}
        submitting={intel.submitting}
        onPlanningDecision={intel.recordPlanningDecision}
      />
    </div>
  );
}

export default function LifecyclePage() {
  return (
    <ProjectFeaturePage kicker="Lifecycle" title="PROJECT LIFECYCLE" explanation={FEATURE_EXPLANATIONS.lifecycle}>
      {(projectId, mode) => <LifecycleBody projectId={projectId} mode={mode} />}
    </ProjectFeaturePage>
  );
}
