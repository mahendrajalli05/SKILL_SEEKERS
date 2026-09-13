"use client";

import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useMemo } from "react";

import { ComparableProjects } from "@/components/ComparableProjects";
import { DataAvailabilityPanel } from "@/components/DataAvailabilityPanel";
import { DataModeBanner } from "@/components/DataModeBanner";
import { EvidenceDispositionGroup } from "@/components/EvidenceDispositionGroup";
import { FieldRow } from "@/components/FieldRow";
import { MlEvidencePanel } from "@/components/MlEvidencePanel";
import { OfficerDecisionPanel } from "@/components/OfficerDecisionPanel";
import { PlanClaimEvidencePanel } from "@/components/PlanClaimEvidencePanel";
import { DocumentsBlueprintPanel } from "@/components/DocumentsBlueprintPanel";
import { ImageEvidencePanel } from "@/components/ImageEvidencePanel";
import { ImageForensicsPanel } from "@/components/ImageForensicsPanel";
import { GeospatialEvidencePanel } from "@/components/GeospatialEvidencePanel";
import { SatelliteRemoteSensingPanel } from "@/components/SatelliteRemoteSensingPanel";
import { NeedImpactPanel } from "@/components/NeedImpactPanel";
import { ContextualIntelligencePanel } from "@/components/ContextualIntelligencePanel";
import { MilestoneAdvisorPanel } from "@/components/MilestoneAdvisorPanel";
import { JanSakshiPanel } from "@/components/JanSakshiPanel";
import { InvestigationCopilotPanel } from "@/components/InvestigationCopilotPanel";
import { ProjectHeader } from "@/components/ProjectHeader";
import { RelationshipGraphPanel } from "@/components/RelationshipGraphPanel";
import { RiskFusionV2Panel } from "@/components/RiskFusionV2Panel";
import { ProjectLifecyclePanel } from "@/components/ProjectLifecyclePanel";
import { SignalCard } from "@/components/SignalCard";
import { SyntheticFieldsPanel } from "@/components/SyntheticFieldsPanel";
import { EvidenceTimeline } from "@/components/system/EvidenceTimeline";
import { InvestigationFlow, PceChain } from "@/components/system/SystemPipeline";
import { PageHeader } from "@/components/system/PageHeader";
import { ScoreDisplay } from "@/components/system/ScoreDisplay";
import { PageState } from "@/components/ui/PageState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { WorkspaceTabs } from "@/components/ui/WorkspaceTabs";
import type { DataMode, EvidenceObject } from "@/lib/types";
import {
  SCHEME_ID_NOTE,
  TIME_UNAVAILABLE_MESSAGE,
  parseDataMode,
  recommendedActionLabel,
} from "@/lib/display";
import { FEATURE_EXPLANATIONS } from "@/lib/explanations";
import { useProjectIntelligence } from "@/lib/useProjectIntelligence";

function visibleEvidence(items: EvidenceObject[], mode: DataMode, isSynthetic: boolean) {
  if (mode === "HYBRID" || isSynthetic) {
    return items;
  }
  return items.filter((item) => item.data_mode === "REAL");
}

export default function InvestigatePage() {
  const params = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const router = useRouter();
  const projectId = Number(params.id);
  const mode = parseDataMode(searchParams.get("mode"));
  const intel = useProjectIntelligence(projectId, mode);
  const project = intel.project.data;
  const riskV2 = intel.riskV2.data;

  const evidenceItems = useMemo(
    () => visibleEvidence(intel.evidence.data?.items ?? [], mode, Boolean(project?.is_synthetic)),
    [intel.evidence.data, mode, project?.is_synthetic],
  );

  if (!Number.isFinite(projectId)) {
    return <PageState kind="error" message="Invalid project id." />;
  }
  if (intel.project.loading) {
    return <PageState kind="loading" message="Loading investigation workspace…" />;
  }
  if (!project) {
    return <PageState kind="error" message={intel.project.error ?? "Project not found."} />;
  }

  const setMode = (next: DataMode) => {
    const nextParams = new URLSearchParams(searchParams.toString());
    nextParams.set("mode", next === "REAL" ? "real" : "hybrid");
    router.replace(`/projects/${projectId}/investigate?${nextParams.toString()}`);
  };

  const timeState =
    intel.time.data?.time_anomaly_score == null
      ? mode === "REAL"
        ? "INSUFFICIENT_EVIDENCE"
        : intel.time.data?.outcome
      : intel.time.data?.outcome;
  const timeExplanation =
    mode === "REAL" && intel.time.data?.time_anomaly_score == null
      ? `${TIME_UNAVAILABLE_MESSAGE} ${intel.time.data?.explanation ?? ""}`.trim()
      : intel.time.data?.explanation;

  return (
    <div className="space-y-6">
      <DataModeBanner
        mode={mode}
        hasHybridEnrichment={project.has_hybrid_enrichment}
        hybridNotice={project.hybrid_notice}
        onModeChange={setMode}
      />

      <PageHeader
        kicker="Investigate"
        title="Investigation Workspace"
        explanation={FEATURE_EXPLANATIONS.workspace}
      >
        <p className="mt-1 text-sm text-[var(--muted)]">
          Primary officer screen. Investigation Priority and Evidence Confidence are
          review rankings, not a fraud probability.
        </p>
      </PageHeader>

      <InvestigationFlow />

      <div className="grid gap-6 xl:grid-cols-[15.5rem_minmax(0,1fr)_20rem]">
        <aside className="space-y-4 xl:sticky xl:top-24 xl:self-start">
          <section className="svk-panel p-4">
            <p className="text-[0.62rem] font-semibold uppercase tracking-[0.14em] text-[var(--muted)]">Project</p>
            <p className="svk-mono mt-2 text-sm font-semibold text-[var(--navy)]">{project.scheme_id}</p>
            <p className="mt-1 text-sm text-[var(--navy)]">{project.work_description}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <StatusBadge kind={mode === "REAL" ? "REAL" : "HYBRID"} />
              <StatusBadge value={project.lifecycle_stage} />
            </div>
            <dl className="mt-3 space-y-2 text-xs">
              <div>
                <dt className="text-[var(--muted)]">Constituency</dt>
                <dd>{project.constituency}</dd>
              </div>
              <div>
                <dt className="text-[var(--muted)]">Category</dt>
                <dd>{project.category}</dd>
              </div>
              <div>
                <dt className="text-[var(--muted)]">Internal ID</dt>
                <dd className="svk-mono">{project.internal_project_id}</dd>
              </div>
            </dl>
            <p className="mt-3 text-[0.65rem] text-[var(--muted)]">{SCHEME_ID_NOTE}</p>
          </section>
          <nav aria-label="Investigation sections" className="svk-panel p-3">
            <p className="px-1 text-[0.62rem] font-semibold uppercase tracking-[0.14em] text-[var(--muted)]">
              Investigation
            </p>
            <ul className="mt-2 space-y-1 text-sm">
              {[
                ["why", "Why reviewed"],
                ["evidence", "Evidence"],
                ["signals", "Signals"],
                ["graph", "Relationships"],
                ["pce", "Plan → Claim → Evidence"],
                ["copilot", "Copilot"],
              ].map(([id, label]) => (
                <li key={id}>
                  <a className="block rounded-md px-2 py-1.5 hover:bg-[var(--navy-soft)]" href={`#${id}`}>
                    {label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        </aside>
        <div className="min-w-0 space-y-6">
      <section className="svk-card p-5" data-tone="saffron">
        <h2 className="text-sm font-semibold tracking-[0.12em] text-[var(--navy)]">WHY THIS PROJECT IS BEING REVIEWED</h2>
        <p className="mt-2 text-sm">{riskV2?.explanation ?? "V2 fused explanation is not yet available."}</p>
        <p className="mt-2 text-xs text-[var(--muted)]">
          Review ranking only. The system does not determine legal wrongdoing.
        </p>
      </section>

      <section className="grid gap-3 md:grid-cols-3">
        <article className="svk-panel p-4">
          <h3 className="text-[0.65rem] font-semibold tracking-[0.14em] text-[var(--success)]">WHAT WE KNOW</h3>
          <p className="mt-2 text-sm">
            {evidenceItems.length} stored evidence object{evidenceItems.length === 1 ? "" : "s"} for this view.
          </p>
        </article>
        <article className="svk-unavailable svk-panel p-4">
          <h3 className="text-[0.65rem] font-semibold tracking-[0.14em] text-[var(--muted)]">WHAT WE DON'T KNOW</h3>
          <p className="mt-2 text-sm">
            {(project.unavailable_fields ?? []).length} unavailable government field
            {(project.unavailable_fields ?? []).length === 1 ? "" : "s"} in the current extract.
          </p>
        </article>
        <article className="svk-card p-4" data-tone="saffron">
          <h3 className="text-[0.65rem] font-semibold tracking-[0.14em] text-[var(--saffron)]">WHAT NEEDS VERIFICATION</h3>
          <p className="mt-2 text-sm">
            {riskV2 ? recommendedActionLabel(riskV2.recommended_action) : "Not assessed"}
          </p>
        </article>
      </section>

      <section className="svk-panel p-5">
        <h2 className="text-sm font-semibold tracking-[0.12em] text-[var(--navy)]">RECOMMENDED NEXT STEP</h2>
        <p className="mt-2 text-lg font-semibold text-[var(--navy)]">
          {riskV2 ? recommendedActionLabel(riskV2.recommended_action) : "Not assessed"}
        </p>
        <p className="mt-1 text-xs text-[var(--muted)]">AI recommends. Authorized officers decide.</p>
      </section>

      <section className="svk-panel p-5">
        <dl className="mt-1">
          <FieldRow label="SARVSAKSHI Scheme ID" value={project.scheme_id} hint={SCHEME_ID_NOTE} />
          <FieldRow label="Internal Project ID" value={project.internal_project_id} />
          <FieldRow label="Data Mode" value={mode} />
          <FieldRow label="Lifecycle" value={project.lifecycle_stage} />
        </dl>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <SummaryMetric
            label="Investigation Priority"
            value={riskV2 ? `${riskV2.investigation_priority}/100` : intel.riskV2.loading ? "Loading" : "Not assessed"}
          />
          <SummaryMetric
            label="Evidence Confidence"
            value={riskV2 ? `${riskV2.evidence_confidence}/100` : intel.riskV2.loading ? "Loading" : "Not assessed"}
          />
          <div>
            <p className="text-xs uppercase tracking-wide text-[var(--muted)]">Recommendation</p>
            <p className="mt-1 font-semibold text-[var(--navy)]">
              {riskV2 ? recommendedActionLabel(riskV2.recommended_action) : "Not assessed"}
            </p>
            {riskV2 ? (
              <div className="mt-2">
                <StatusBadge value={riskV2.recommended_action} />
              </div>
            ) : null}
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-[var(--muted)]">Lifecycle</p>
            <p className="mt-1 font-semibold text-[var(--navy)]">{project.lifecycle_stage}</p>
            <div className="mt-2">
              <StatusBadge value={project.lifecycle_stage} />
            </div>
          </div>
        </div>
      </section>

      <ProjectHeader
        project={project}
        dataMode={mode}
        passportHref={`/projects/${projectId}?mode=${mode === "REAL" ? "real" : "hybrid"}`}
      />

      <ProjectLifecyclePanel
        projectId={projectId}
        mode={mode}
        lifecycle={intel.lifecycle.data}
        loading={intel.lifecycle.loading}
        error={intel.lifecycle.error}
        submitting={intel.submitting}
        onPlanningDecision={intel.recordPlanningDecision}
      />

      <WorkspaceTabs
        ariaLabel="Investigation workspace sections"
        defaultTab="why"
        tabs={[
          {
            id: "why",
            label: "Why?",
            content: (
              <RiskFusionV2Panel
                risk={riskV2}
                loading={intel.riskV2.loading}
                error={intel.riskV2.error}
              />
            ),
          },
          {
            id: "evidence",
            label: "Evidence",
            content: (
              <div className="space-y-4">
                <MlEvidencePanel
                  projectId={projectId}
                  mode={mode}
                  items={evidenceItems}
                  onCreated={intel.reloadEvidence}
                />
                {intel.evidence.loading ? (
                  <PageState kind="loading" message="Loading evidence objects…" />
                ) : evidenceItems.length === 0 ? (
                  <PageState kind="unavailable" message="No evidence timestamps are available yet." />
                ) : (
                  <EvidenceDispositionGroup items={evidenceItems} />
                )}
              </div>
            ),
          },
          {
            id: "signals",
            label: "Risk Signals",
            content: (
              <div className="space-y-4">
                <p className="text-sm text-[var(--muted)]">
                  Frozen V1/V1.1 engine outputs. Risk Fusion V2 consumes their Evidence Objects.
                </p>
                <div className="grid gap-4 lg:grid-cols-2">
                  <SignalCard
                    title="Cost"
                    score={intel.cost.data?.cost_anomaly_score}
                    state={intel.cost.data?.outcome}
                    confidence={intel.cost.data?.evidence_confidence}
                    explanation={intel.cost.data?.explanation}
                    flagged={intel.cost.data?.flagged}
                    dataMode="REAL"
                  />
                  <SignalCard
                    title="Time"
                    score={intel.time.data?.time_anomaly_score}
                    state={timeState}
                    confidence={intel.time.data?.evidence_confidence}
                    explanation={timeExplanation}
                    flagged={intel.time.data?.flagged}
                    dataMode={mode}
                  />
                  <SignalCard
                    title="Overlap"
                    score={intel.overlap.data?.overlap_score}
                    state={intel.overlap.data?.outcome}
                    confidence={intel.overlap.data?.evidence_confidence}
                    explanation={intel.overlap.data?.explanation}
                    flagged={intel.overlap.data?.flagged}
                    dataMode={mode}
                  />
                  <SignalCard
                    title="Compliance"
                    score={null}
                    state={intel.compliance.data?.compliance_status}
                    explanation={intel.compliance.data?.explanation}
                    flagged={intel.compliance.data?.flagged}
                    dataMode={mode}
                  />
                </div>
                <section className="border border-[var(--line)] bg-white p-5">
                  <h3 className="font-semibold text-[var(--navy)]">Compliance findings</h3>
                  <p className="mt-2 text-sm">
                    {intel.compliance.data?.explanation ?? "Compliance not yet loaded."}
                  </p>
                  <p className="mt-2 text-sm text-[var(--muted)]">
                    Status: {intel.compliance.data?.compliance_status ?? "Not assessed"}
                  </p>
                  <ul className="mt-3 space-y-2 text-sm">
                    {(intel.compliance.data?.triggered_rules ?? []).map((rule) => (
                      <li key={rule.rule_id}>
                        <span className="font-medium">{rule.rule_id}</span> {rule.title}: {rule.status}.{" "}
                        {rule.explanation}
                      </li>
                    ))}
                    {(intel.compliance.data?.not_assessable_rules ?? []).slice(0, 8).map((rule) => (
                      <li key={rule.rule_id} className="text-[var(--muted)]">
                        {rule.rule_id} {rule.title}: {rule.status}. {rule.explanation}
                      </li>
                    ))}
                  </ul>
                </section>
                <ComparableProjects
                  cost={intel.cost.data?.comparable_projects ?? []}
                  overlap={intel.overlap.data?.matches ?? []}
                />
              </div>
            ),
          },
          {
            id: "pce",
            label: "Plan → Claim → Evidence",
            content: (
              <div className="space-y-4">
                <PceChain />
                <PlanClaimEvidencePanel projectId={projectId} mode={mode} />
              </div>
            ),
          },
          {
            id: "documents",
            label: "Documents",
            content: <DocumentsBlueprintPanel projectId={projectId} mode={mode} />,
          },
          {
            id: "images",
            label: "Images",
            content: <ImageEvidencePanel projectId={projectId} mode={mode} />,
          },
          {
            id: "forensics",
            label: "Forensics",
            content: <ImageForensicsPanel projectId={projectId} mode={mode} />,
          },
          {
            id: "geospatial",
            label: "Geospatial",
            content: <GeospatialEvidencePanel projectId={projectId} mode={mode} />,
          },
          {
            id: "satellite",
            label: "Satellite",
            content: <SatelliteRemoteSensingPanel projectId={projectId} mode={mode} />,
          },
          {
            id: "citizen",
            label: "Citizen",
            content: <JanSakshiPanel projectId={projectId} mode={mode} />,
          },
          {
            id: "milestones",
            label: "Milestones",
            content: <MilestoneAdvisorPanel projectId={projectId} mode={mode} />,
          },
          {
            id: "graph",
            label: "Relationship Graph",
            content: (
              <RelationshipGraphPanel
                projectId={projectId}
                mode={mode}
                graph={intel.graph.data}
                loading={intel.graph.loading}
                error={intel.graph.error}
                evidenceItems={evidenceItems}
                schemeId={project.scheme_id}
                internalProjectId={project.internal_project_id}
                isSynthetic={Boolean(project.is_synthetic)}
              />
            ),
          },
          {
            id: "need-impact",
            label: "Need & Impact",
            content: <NeedImpactPanel projectId={projectId} mode={mode} />,
          },
          {
            id: "context",
            label: "Context",
            content: <ContextualIntelligencePanel projectId={projectId} mode={mode} />,
          },
          {
            id: "copilot",
            label: "Copilot",
            content: (
              <p className="text-sm text-[var(--muted)]">
                The Investigation Copilot is docked in the side panel.
              </p>
            ),
          },
        ]}
      />

      <SyntheticFieldsPanel enrichment={project.synthetic_enrichment} mode={mode} />

      <section className="space-y-4">
        <h2 className="text-xl font-semibold text-[var(--navy)]">Evidence timeline / summary</h2>
        {evidenceItems.length === 0 ? (
          <PageState kind="unavailable" message="No evidence timestamps are available yet." />
        ) : (
          <div className="border border-[var(--line)] bg-[var(--surface)] p-4">
            <EvidenceTimeline items={evidenceItems} />
            <ol className="mt-4 space-y-2 text-sm text-[var(--muted)]">
              {evidenceItems.map((item) => (
                <li key={`tl-${item.evidence_id}`}>
                  {item.created_at ?? "Timestamp unavailable"} · {item.engine_name} · {item.finding} ·{" "}
                  {item.data_mode}
                </li>
              ))}
            </ol>
          </div>
        )}
        <DataAvailabilityPanel
          fields={project.unavailable_fields}
          extraNotes={[TIME_UNAVAILABLE_MESSAGE, project.amount_unit_note]}
        />
        <OfficerDecisionPanel
          decisions={intel.decisions}
          submitting={intel.submitting}
          error={intel.decisionError}
          onSubmit={intel.recordDecision}
        />
      </section>
        </div>
        <aside className="space-y-4 xl:sticky xl:top-24 xl:self-start">
          <section className="border border-[var(--line)] bg-[var(--surface)] p-4">
            <ScoreDisplay
              label="Investigation Priority"
              value={riskV2 ? `${riskV2.investigation_priority}/100` : "Not assessed"}
              kind="priority"
              note="Review ranking"
            />
            <div className="mt-4">
              <ScoreDisplay
                label="Evidence Confidence"
                value={riskV2 ? `${riskV2.evidence_confidence}/100` : "Not assessed"}
                kind="confidence"
              />
            </div>
            <p className="mt-4 text-sm">
              Recommendation: {riskV2 ? recommendedActionLabel(riskV2.recommended_action) : "Not assessed"}
            </p>
            <p className="mt-2 text-xs text-[var(--muted)]">{FEATURE_EXPLANATIONS.risk}</p>
          </section>
          <div>
            <InvestigationCopilotPanel projectId={projectId} mode={mode} />
          </div>
        </aside>
      </div>
    </div>
  );
}

function SummaryMetric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-wide text-[var(--muted)]">{label}</p>
      <p className="mt-1 text-xl font-semibold text-[var(--navy)]">{value}</p>
    </div>
  );
}
