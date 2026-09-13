"use client";

import { EvidenceCenter } from "@/components/system/EvidenceCenter";
import { EvidenceTimeline } from "@/components/system/EvidenceTimeline";
import { ProjectFeaturePage } from "@/components/system/ProjectFeaturePage";
import { HubTile } from "@/components/system/VisualKit";
import { FEATURE_EXPLANATIONS, EVIDENCE_MODULES } from "@/lib/explanations";
import { withModePath } from "@/lib/display";
import { useProjectIntelligence } from "@/lib/useProjectIntelligence";
import type { DataMode } from "@/lib/types";

function EvidenceBody({ projectId, mode }: { projectId: number; mode: DataMode }) {
  const intel = useProjectIntelligence(projectId, mode);
  const officerMode = mode === "REAL" ? "REAL" : "HYBRID";
  const items = intel.evidence.data?.items ?? [];
  return (
    <div className="space-y-6">
      <div className="grid gap-3 sm:grid-cols-3">
        {EVIDENCE_MODULES.map((item) => (
          <HubTile
            key={item.href}
            href={withModePath(`${item.href}?project=${projectId}`, officerMode)}
            icon={item.icon}
            title={item.label}
            explanation={item.explanation}
            tone={item.tone}
          />
        ))}
      </div>
      <section className="svk-panel p-5">
        <h2 className="svk-display text-xl font-semibold text-[var(--navy)]">EVIDENCE TIMELINE</h2>
        <div className="mt-4">
          <EvidenceTimeline items={items} />
        </div>
      </section>
      <EvidenceCenter items={items} loading={intel.evidence.loading} error={intel.evidence.error} />
    </div>
  );
}

export default function EvidencePage() {
  return (
    <ProjectFeaturePage kicker="Evidence" title="EVIDENCE CENTER" explanation={FEATURE_EXPLANATIONS.evidence}>
      {(projectId, mode) => <EvidenceBody projectId={projectId} mode={mode} />}
    </ProjectFeaturePage>
  );
}
