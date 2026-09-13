"use client";

import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useMemo } from "react";

import { ComparableProjects } from "@/components/ComparableProjects";
import { DataAvailabilityPanel } from "@/components/DataAvailabilityPanel";
import { DataModeBanner } from "@/components/DataModeBanner";
import { EvidenceCard } from "@/components/EvidenceCard";
import { MlEvidencePanel } from "@/components/MlEvidencePanel";
import { FieldRow } from "@/components/FieldRow";
import { NeedImpactPanel } from "@/components/NeedImpactPanel";
import { ContextualIntelligencePanel } from "@/components/ContextualIntelligencePanel";
import { ProjectLifecyclePanel } from "@/components/ProjectLifecyclePanel";
import { MilestoneAdvisorPanel } from "@/components/MilestoneAdvisorPanel";
import { CitizenEvidenceSummary } from "@/components/CitizenEvidenceSummary";
import { ProjectHeader } from "@/components/ProjectHeader";
import { RelationshipSummary } from "@/components/RelationshipSummary";
import { RiskScoreCard } from "@/components/RiskScoreCard";
import { SignalCard } from "@/components/SignalCard";
import { SyntheticFieldsPanel } from "@/components/SyntheticFieldsPanel";
import { PlanClaimEvidencePanel } from "@/components/PlanClaimEvidencePanel";
import { DocumentsBlueprintPanel } from "@/components/DocumentsBlueprintPanel";
import { ImageEvidencePanel } from "@/components/ImageEvidencePanel";
import { GeospatialEvidencePanel } from "@/components/GeospatialEvidencePanel";
import { SatelliteRemoteSensingPanel } from "@/components/SatelliteRemoteSensingPanel";
import { EvidenceTimeline } from "@/components/system/EvidenceTimeline";
import { FeatureExplanation } from "@/components/system/FeatureExplanation";
import { PageHeader } from "@/components/system/PageHeader";
import { LazyDisclosure } from "@/components/ui/LazyDisclosure";
import { PageState } from "@/components/ui/PageState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import type { DataMode, EvidenceObject } from "@/lib/types";
import {
  SCHEME_ID_NOTE,
  TIME_UNAVAILABLE_MESSAGE,
  displayText,
  formatAllocation,
  formatDate,
  parseDataMode,
  recommendedActionLabel,
  withModePath,
} from "@/lib/display";
import { FEATURE_EXPLANATIONS } from "@/lib/explanations";
import { useProjectIntelligence } from "@/lib/useProjectIntelligence";

function visibleEvidence(items: EvidenceObject[], mode: DataMode, isSynthetic: boolean) {
  if (mode === "HYBRID" || isSynthetic) {
    return items;
  }
  return items.filter((item) => item.data_mode === "REAL");
}

export default function ProjectPassportPage() {
  const params = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const router = useRouter();
  const projectId = Number(params.id);
  const mode = parseDataMode(searchParams.get("mode"));
  const intel = useProjectIntelligence(projectId, mode);
  const project = intel.project.data;

  const evidenceItems = useMemo(
    () => visibleEvidence(intel.evidence.data?.items ?? [], mode, Boolean(project?.is_synthetic)),
    [intel.evidence.data, mode, project?.is_synthetic],
  );

  if (!Number.isFinite(projectId)) {
    return <PageState kind="error" message="Invalid project id." />;
  }
  if (intel.project.loading) {
    return <PageState kind="loading" message="Loading project…" />;
  }
  if (!project) {
    return <PageState kind="error" message={intel.project.error ?? "Project not found."} />;
  }

  const setMode = (next: DataMode) => {
    const nextParams = new URLSearchParams(searchParams.toString());
    nextParams.set("mode", next === "REAL" ? "real" : "hybrid");
    router.replace(`/projects/${projectId}?${nextParams.toString()}`);
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
      {project.is_synthetic ? (
        <PageState kind="unavailable" message={project.synthetic_label ?? "SYNTHETIC prototype record."} />
      ) : null}

      <PageHeader kicker="PROJECT OVERVIEW" title="Project Digital Passport" explanation={FEATURE_EXPLANATIONS.passport} />

      <section className="svk-panel p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="svk-mono text-sm font-semibold text-[var(--signal)]">{displayText(project.scheme_id)}</p>
            <h2 className="svk-display mt-1 text-2xl font-semibold text-[var(--navy)]">
              {displayText(project.work_description)}
            </h2>
            <p className="mt-1 text-sm text-[var(--muted)]">
              {displayText(project.constituency)} · {displayText(project.category)} · {formatAllocation(project.allocation_amount)}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <StatusBadge kind={mode === "REAL" ? "REAL" : "HYBRID"} />
            <StatusBadge value={project.lifecycle_stage} />
            <StatusBadge value={project.status} />
          </div>
        </div>
        <dl className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-md bg-[var(--surface-2)] p-3">
            <dt className="text-[0.62rem] uppercase tracking-[0.14em] text-[var(--muted)]">Scheme ID</dt>
            <dd className="svk-mono mt-1 text-sm">{displayText(project.scheme_id)}</dd>
          </div>
          <div className="rounded-md bg-[var(--surface-2)] p-3">
            <dt className="text-[0.62rem] uppercase tracking-[0.14em] text-[var(--muted)]">Constituency</dt>
            <dd className="mt-1 text-sm">{displayText(project.constituency)}</dd>
          </div>
          <div className="rounded-md bg-[var(--surface-2)] p-3">
            <dt className="text-[0.62rem] uppercase tracking-[0.14em] text-[var(--muted)]">Category</dt>
            <dd className="mt-1 text-sm">{displayText(project.category)}</dd>
          </div>
          <div className="rounded-md bg-[var(--surface-2)] p-3">
            <dt className="text-[0.62rem] uppercase tracking-[0.14em] text-[var(--muted)]">Amount</dt>
            <dd className="mt-1 text-sm">{formatAllocation(project.allocation_amount)}</dd>
          </div>
        </dl>
        <p className="mt-3 text-xs text-[var(--muted)]">{SCHEME_ID_NOTE}</p>
      </section>

      <section className="grid gap-4 sm:grid-cols-2">
        <article className="svk-card p-5" data-tone="saffron">
          <p className="text-[0.65rem] font-semibold uppercase tracking-[0.14em] text-[var(--muted)]">Review Priority</p>
          <p className="svk-mono mt-2 text-4xl font-semibold text-[var(--saffron)]">
            {intel.risk.data?.investigation_priority ?? intel.riskV2.data?.investigation_priority ?? "Not assessed"}
          </p>
          <p className="mt-1 text-xs text-[var(--muted)]">Investigation Priority — not a fraud score</p>
        </article>
        <article className="svk-card p-5" data-tone="signal">
          <p className="text-[0.65rem] font-semibold uppercase tracking-[0.14em] text-[var(--muted)]">Evidence Confidence</p>
          <p className="svk-mono mt-2 text-4xl font-semibold text-[var(--signal)]">
            {intel.risk.data?.evidence_confidence ?? intel.riskV2.data?.evidence_confidence ?? "Not assessed"}
          </p>
        </article>
      </section>

      <section>
        <h2 className="mb-3 svk-display text-xl font-semibold text-[var(--navy)]">SIGNAL MATRIX</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
          <SignalCard compact title="Cost" score={intel.cost.data?.cost_anomaly_score} state={intel.cost.data?.outcome} flagged={intel.cost.data?.flagged} dataMode="REAL" explanation={intel.cost.data?.explanation} />
          <SignalCard compact title="Time" score={intel.time.data?.time_anomaly_score} state={timeState} flagged={intel.time.data?.flagged} dataMode={mode} explanation={timeExplanation} />
          <SignalCard compact title="Overlap" score={intel.overlap.data?.overlap_score} state={intel.overlap.data?.outcome} flagged={intel.overlap.data?.flagged} dataMode={mode} explanation={intel.overlap.data?.explanation} />
          <SignalCard compact title="Compliance" score={null} state={intel.compliance.data?.compliance_status} flagged={intel.compliance.data?.flagged} dataMode={mode} explanation={intel.compliance.data?.explanation} />
          <SignalCard compact title="ML" score={null} state={evidenceItems.some((item) => item.engine_name === "ml") ? "Stored" : "Unavailable"} dataMode={mode} explanation={FEATURE_EXPLANATIONS.ml} />
          <SignalCard compact title="Context" score={null} state="See section" dataMode={mode} explanation={FEATURE_EXPLANATIONS.context} />
          <SignalCard compact title="Geo" score={null} state="See section" dataMode={mode} explanation={FEATURE_EXPLANATIONS.geo} />
          <SignalCard compact title="Satellite" score={null} state="See section" dataMode={mode} explanation={FEATURE_EXPLANATIONS.satellite} />
          <SignalCard compact title="Citizen" score={null} state="See section" dataMode={mode} explanation={FEATURE_EXPLANATIONS.citizen} />
          <SignalCard compact title="Milestone" score={null} state="See section" dataMode={mode} explanation={FEATURE_EXPLANATIONS.milestone} />
        </div>
      </section>

      <section className="svk-panel p-5">
        <h2 className="svk-display text-xl font-semibold text-[var(--navy)]">EVIDENCE TIMELINE</h2>
        <div className="mt-4">
          <EvidenceTimeline items={evidenceItems} />
        </div>
      </section>

      <section className="svk-panel p-5">
        <h2 className="mb-3 svk-display text-xl font-semibold text-[var(--navy)]">PLAN → CLAIM → EVIDENCE → RESULT</h2>
        <LazyDisclosure
          title="PLAN / CLAIM / EVIDENCE"
          summary="Open to load Plan → Claim → Evidence. Unavailable until this section is opened."
        >
          <PlanClaimEvidencePanel projectId={projectId} mode={mode} />
        </LazyDisclosure>
      </section>

      <section>
        <h2 className="mb-3 svk-display text-xl font-semibold text-[var(--navy)]">RELATED PROJECTS</h2>
        <ComparableProjects
          cost={intel.cost.data?.comparable_projects ?? []}
          overlap={intel.overlap.data?.matches ?? []}
          costNote={intel.cost.data?.amount_unit_note}
        />
      </section>

      <section>
        <h2 className="mb-3 font-semibold text-[var(--navy)]">PROJECT IDENTITY</h2>
        <ProjectHeader
          project={project}
          dataMode={mode}
          investigateHref={`/projects/${projectId}/investigate?mode=${mode === "REAL" ? "real" : "hybrid"}`}
        />
        <div className="mt-4 border border-[var(--line)] bg-[var(--surface)] p-5">
          <dl>
            <FieldRow label="IDA" value={project.ida} />
            <FieldRow label="House" value={project.house} />
            <FieldRow label="Lifecycle stage" value={project.lifecycle_stage} />
            <FieldRow label="City (place text)" value={project.city} />
            <FieldRow label="Ward (place text)" value={project.ward} />
            <FieldRow label="Block (place text)" value={project.block} />
            <FieldRow label="Village (place text)" value={project.village} />
          </dl>
        </div>
      </section>

      <section>
        <h2 className="mb-3 font-semibold text-[var(--navy)]">FINANCE / RECOMMENDATION</h2>
        <div className="border border-[var(--line)] bg-[var(--surface)] p-5">
          <p className="text-sm text-[var(--muted)]">
            Observed MPLADS extract fields only. These values are not relabelled.
          </p>
          <dl className="mt-3">
            <FieldRow label="Recommendation date" value={formatDate(project.recommended_date)} />
            <FieldRow
              label="Allocation amount"
              value={formatAllocation(project.allocation_amount)}
              hint={project.amount_unit_note}
            />
            <FieldRow label="Source dataset" value={project.source_dataset} />
            <FieldRow label="Source URL" value={project.snapshot_source_url} />
            <FieldRow label="Extracted at" value={project.snapshot_extracted_at} />
            <FieldRow label="Download date" value={project.snapshot_download_date} />
            <FieldRow label="Publisher" value={project.snapshot_publisher} />
          </dl>
          <p className="mt-3 text-sm text-[var(--muted)]">
            {displayText(project.snapshot_notes)} The source amount unit is unspecified.
          </p>
        </div>
        <div className="mt-4">
          <SyntheticFieldsPanel enrichment={project.synthetic_enrichment} mode={mode} />
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="font-semibold text-[var(--navy)]">ANALYTICS</h2>
        <RiskScoreCard risk={intel.risk.data} loading={intel.risk.loading} error={intel.risk.error} />
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
        {intel.cost.error ? <PageState kind="error" message={intel.cost.error} compact /> : null}
        {intel.time.loading ? (
          <PageState kind="loading" message="Assessing time intelligence…" compact />
        ) : null}
      </section>

      <section className="space-y-3">
        <h2 className="font-semibold text-[var(--navy)]">EVIDENCE</h2>
        <MlEvidencePanel
          projectId={projectId}
          mode={mode}
          items={evidenceItems}
          onCreated={intel.reloadEvidence}
        />
        {intel.evidence.loading ? (
          <PageState kind="loading" message="Loading evidence objects…" compact />
        ) : null}
        {intel.evidence.error ? <PageState kind="error" message={intel.evidence.error} compact /> : null}
        {evidenceItems.length === 0 && !intel.evidence.loading ? (
          <PageState
            kind="unavailable"
            message="No stored evidence objects for this view. Intelligence APIs persist evidence when they complete."
          />
        ) : (
          evidenceItems
            .filter((item) => item.engine_name !== "ml" && item.signal_type !== "ML_ANOMALY_SIGNAL")
            .map((item) => <EvidenceCard key={item.evidence_id} evidence={item} />)
        )}
      </section>

      <LazyDisclosure
          title="DOCUMENTS"
          summary="Open to load document and blueprint records. Unavailable until this section is opened."
        >
          <DocumentsBlueprintPanel projectId={projectId} mode={mode} />
        </LazyDisclosure>

      <LazyDisclosure
          title="IMAGES"
          summary="Open to load image evidence. Unavailable until this section is opened."
        >
          <ImageEvidencePanel projectId={projectId} mode={mode} />
        </LazyDisclosure>

      <LazyDisclosure
          title="GEOSPATIAL"
          summary="Open to load geospatial consistency. Unavailable until this section is opened."
        >
          <GeospatialEvidencePanel projectId={projectId} mode={mode} />
        </LazyDisclosure>

      <LazyDisclosure
          title="SATELLITE"
          summary="Open to load satellite / remote-sensing status. Unavailable until this section is opened."
        >
          <SatelliteRemoteSensingPanel projectId={projectId} mode={mode} />
        </LazyDisclosure>

      <section>
        <h2 className="mb-3 font-semibold text-[var(--navy)]">MILESTONES</h2>
        <FeatureExplanation text={FEATURE_EXPLANATIONS.milestone} />
        <MilestoneAdvisorPanel projectId={projectId} mode={mode} compact />
      </section>

      <section>
        <h2 className="mb-3 font-semibold text-[var(--navy)]">JAN-SAKSHI</h2>
        <FeatureExplanation text={FEATURE_EXPLANATIONS.citizen} />
        <CitizenEvidenceSummary projectId={projectId} mode={mode} />
      </section>

      <RelationshipSummary
          graph={intel.graph.data}
          loading={intel.graph.loading}
          error={intel.graph.error}
          openHref={withModePath(`/projects/${projectId}/graph`, mode)}
        />

      <section>
        <h2 className="mb-3 font-semibold text-[var(--navy)]">NEED & IMPACT</h2>
        <FeatureExplanation text={FEATURE_EXPLANATIONS.need} />
        <NeedImpactPanel projectId={projectId} mode={mode} />
      </section>

      <section>
        <h2 className="mb-3 font-semibold text-[var(--navy)]">CONTEXTUAL INTELLIGENCE</h2>
        <FeatureExplanation text={FEATURE_EXPLANATIONS.context} />
        <ContextualIntelligencePanel projectId={projectId} mode={mode} />
      </section>

      <ProjectLifecyclePanel
          projectId={projectId}
          mode={mode}
          lifecycle={intel.lifecycle.data}
          loading={intel.lifecycle.loading}
          error={intel.lifecycle.error}
          submitting={intel.submitting}
          onPlanningDecision={intel.recordPlanningDecision}
        />

      <section>
        <h2 className="mb-3 font-semibold text-[var(--navy)]">DATA AVAILABILITY</h2>
        <DataAvailabilityPanel
          fields={project.unavailable_fields}
          extraNotes={[TIME_UNAVAILABLE_MESSAGE, project.amount_unit_note]}
        />
      </section>

      <section className="border border-[var(--line)] bg-[var(--surface)] p-5">
        <h2 className="font-semibold text-[var(--navy)]">NEXT ACTION</h2>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Recommendation from stored Risk Fusion only. Authorized officers decide.
        </p>
        <p className="mt-2 text-lg font-semibold text-[var(--navy)]">
          {intel.risk.data
            ? recommendedActionLabel(intel.risk.data.recommended_action)
            : "Not assessed"}
        </p>
      </section>
    </div>
  );
}
