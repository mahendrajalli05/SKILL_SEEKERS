"use client";

import { DocumentsBlueprintPanel } from "@/components/DocumentsBlueprintPanel";
import { ProjectFeaturePage } from "@/components/system/ProjectFeaturePage";
import { FEATURE_EXPLANATIONS } from "@/lib/explanations";

export default function DocumentsPage() {
  return (
    <ProjectFeaturePage
      kicker="Evidence"
      title="DOCUMENTS & BLUEPRINT"
      explanation={FEATURE_EXPLANATIONS.documents}
    >
      {(projectId, mode) => <DocumentsBlueprintPanel projectId={projectId} mode={mode} />}
    </ProjectFeaturePage>
  );
}
