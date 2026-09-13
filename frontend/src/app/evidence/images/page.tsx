"use client";

import { ImageEvidencePanel } from "@/components/ImageEvidencePanel";
import { ImageForensicsPanel } from "@/components/ImageForensicsPanel";
import { ProjectFeaturePage } from "@/components/system/ProjectFeaturePage";
import { FEATURE_EXPLANATIONS } from "@/lib/explanations";

export default function ImagesForensicsPage() {
  return (
    <ProjectFeaturePage
      kicker="Evidence"
      title="IMAGES & FORENSICS"
      explanation={FEATURE_EXPLANATIONS.images}
    >
      {(projectId, mode) => (
        <div className="space-y-6">
          <ImageEvidencePanel projectId={projectId} mode={mode} />
          <ImageForensicsPanel projectId={projectId} mode={mode} />
        </div>
      )}
    </ProjectFeaturePage>
  );
}
