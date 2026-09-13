"use client";

import { NeedImpactPanel } from "@/components/NeedImpactPanel";
import { ProjectFeaturePage } from "@/components/system/ProjectFeaturePage";
import { DECISION_SUPPORT_ONLY, FEATURE_EXPLANATIONS } from "@/lib/explanations";

export default function NeedImpactExplainPage() {
  return (
    <ProjectFeaturePage
      kicker="Planning"
      title="NEED & IMPACT"
      explanation={FEATURE_EXPLANATIONS.need}
    >
      {(projectId, mode) => (
        <div className="space-y-4">
          <p className="text-sm text-[var(--muted)]">{DECISION_SUPPORT_ONLY}</p>
          <div className="grid gap-3 md:grid-cols-4 text-sm">
            <article className="svk-card p-4" data-tone="signal">
              <h2 className="text-[0.65rem] font-semibold tracking-[0.14em] text-[var(--muted)]">NEED</h2>
              <p className="mt-2">Observed development need from available constituency and category context.</p>
            </article>
            <article className="svk-card p-4" data-tone="indigo">
              <h2 className="text-[0.65rem] font-semibold tracking-[0.14em] text-[var(--muted)]">IMPACT</h2>
              <p className="mt-2">Expected contribution of the proposed work where inputs exist.</p>
            </article>
            <article className="svk-card p-4" data-tone="saffron">
              <h2 className="text-[0.65rem] font-semibold tracking-[0.14em] text-[var(--muted)]">URGENCY</h2>
              <p className="mt-2">Time-sensitivity of the proposal. Separate from Need, Impact, and Priority.</p>
            </article>
            <article className="svk-card p-4" data-tone="success">
              <h2 className="text-[0.65rem] font-semibold tracking-[0.14em] text-[var(--muted)]">PRIORITY</h2>
              <p className="mt-2">Combined planning rank. Decision support, not an official sanction formula.</p>
            </article>
          </div>
          <NeedImpactPanel projectId={projectId} mode={mode} />
        </div>
      )}
    </ProjectFeaturePage>
  );
}
