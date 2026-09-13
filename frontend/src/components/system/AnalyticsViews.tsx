"use client";

import { ComparableProjects } from "@/components/ComparableProjects";
import { SignalCard } from "@/components/SignalCard";
import { PageState } from "@/components/ui/PageState";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ScoreBar } from "@/components/system/ScoreDisplay";
import { ContributionBars } from "@/components/system/VisualKit";
import {
  TIME_UNAVAILABLE_MESSAGE,
  displayText,
  formatAllocation,
  formatDate,
} from "@/lib/display";
import { FEATURE_EXPLANATIONS } from "@/lib/explanations";
import { useProjectIntelligence } from "@/lib/useProjectIntelligence";
import type { DataMode } from "@/lib/types";

function Metric({
  label,
  value,
  tone = "signal",
}: {
  label: string;
  value: string;
  tone?: "signal" | "saffron" | "indigo" | "success";
}) {
  return (
    <article className="svk-card p-4" data-tone={tone}>
      <p className="text-[0.62rem] font-semibold uppercase tracking-[0.14em] text-[var(--muted)]">{label}</p>
      <p className="svk-mono mt-2 text-xl font-semibold text-[var(--navy)]">{value}</p>
    </article>
  );
}

export function CostAnalyticsView({ projectId, mode }: { projectId: number; mode: DataMode }) {
  const intel = useProjectIntelligence(projectId, mode);
  const cost = intel.cost.data;
  const project = intel.project.data;
  const amounts = (cost?.comparable_projects ?? [])
    .map((item) => item.allocation_amount)
    .filter((item): item is number => item != null && Number.isFinite(item));
  const peerMin = amounts.length ? Math.min(...amounts) : null;
  const peerMax = amounts.length ? Math.max(...amounts) : null;

  if (intel.cost.loading) return <PageState kind="loading" message="Loading cost intelligence…" />;
  if (intel.cost.error) return <PageState kind="error" message={intel.cost.error} />;
  if (!cost) return <PageState kind="unavailable" message="Cost intelligence is unavailable for this project." />;

  return (
    <div className="space-y-5">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Metric label="Allocation" value={formatAllocation(project?.allocation_amount ?? null)} />
        <Metric label="Peer group" value={displayText(cost.peer_scope_label)} tone="indigo" />
        <Metric label="Peer count" value={String(cost.peer_count)} />
        <Metric
          label="Anomaly score"
          value={cost.cost_anomaly_score == null ? "UNAVAILABLE" : String(cost.cost_anomaly_score)}
          tone="saffron"
        />
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <Metric
          label="Percentile"
          value="UNAVAILABLE"
          tone="indigo"
        />
        <Metric
          label="Peer allocation range"
          value={
            peerMin == null || peerMax == null
              ? "INSUFFICIENT EVIDENCE"
              : `${formatAllocation(peerMin)} – ${formatAllocation(peerMax)}`
          }
        />
      </div>
      <SignalCard
        title="COST INTELLIGENCE"
        score={cost.cost_anomaly_score}
        state={cost.outcome}
        confidence={cost.evidence_confidence}
        explanation={cost.explanation}
        flagged={cost.flagged}
        dataMode="REAL"
      />
      <p className="text-xs text-[var(--muted)]">{cost.amount_unit_note}</p>
      <details>
        <summary className="cursor-pointer text-sm text-[var(--navy)]">More details</summary>
        <p className="mt-2 text-sm text-[var(--muted)]">{FEATURE_EXPLANATIONS.cost} Cost V1.1 logic is unchanged.</p>
      </details>
      <ComparableProjects cost={cost.comparable_projects} overlap={[]} costNote={cost.amount_unit_note} />
    </div>
  );
}

export function TimeAnalyticsView({ projectId, mode }: { projectId: number; mode: DataMode }) {
  const intel = useProjectIntelligence(projectId, mode);
  const time = intel.time.data;
  const project = intel.project.data;
  const inconclusive = mode === "REAL" && (time?.time_anomaly_score == null);

  if (intel.time.loading) return <PageState kind="loading" message="Loading time intelligence…" />;
  if (intel.time.error) return <PageState kind="error" message={intel.time.error} />;
  if (!time) return <PageState kind="unavailable" message="Time intelligence is unavailable for this project." />;

  return (
    <div className="space-y-5">
      {inconclusive ? (
        <PageState kind="inconclusive" message={TIME_UNAVAILABLE_MESSAGE} />
      ) : null}
      {mode === "HYBRID" ? (
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--saffron)]">HYBRID TEST</p>
      ) : null}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Metric label="Recommendation date" value={formatDate(project?.recommended_date)} />
        <Metric label="Duration / progress" value="UNAVAILABLE" tone="indigo" />
        <Metric label="Result" value={inconclusive ? "INCONCLUSIVE" : displayText(time.outcome)} tone="saffron" />
        <Metric label="Time mode" value={displayText(time.time_mode)} />
      </div>
      <SignalCard
        title="TIME INTELLIGENCE"
        score={time.time_anomaly_score}
        state={inconclusive ? "INCONCLUSIVE" : time.outcome}
        confidence={time.evidence_confidence}
        explanation={inconclusive ? `${TIME_UNAVAILABLE_MESSAGE} ${time.explanation}`.trim() : time.explanation}
        flagged={time.flagged}
        dataMode={mode}
      />
      <details>
        <summary className="cursor-pointer text-sm text-[var(--navy)]">More details</summary>
        <p className="mt-2 text-sm text-[var(--muted)]">
          Dataset type: {displayText(time.dataset_type)}. Delay detected: {String(time.delay_detected)}.
          Execution dates are not fabricated for REAL records.
        </p>
      </details>
    </div>
  );
}

export function OverlapAnalyticsView({ projectId, mode }: { projectId: number; mode: DataMode }) {
  const intel = useProjectIntelligence(projectId, mode);
  const overlap = intel.overlap.data;

  if (intel.overlap.loading) return <PageState kind="loading" message="Loading overlap detection…" />;
  if (intel.overlap.error) return <PageState kind="error" message={intel.overlap.error} />;
  if (!overlap) return <PageState kind="unavailable" message="Overlap detection is unavailable for this project." />;

  return (
    <div className="space-y-5">
      <div className="grid gap-3 sm:grid-cols-3">
        <Metric
          label="Potential matches"
          value={String(overlap.matches.length)}
          tone="saffron"
        />
        <Metric
          label="Similarity"
          value={overlap.overlap_score == null ? "UNAVAILABLE" : String(overlap.overlap_score)}
        />
        <Metric label="Result" value={displayText(overlap.outcome)} />
      </div>
      <p className="text-sm text-[var(--muted)]">
        Potential overlap only. This is not a confirmed duplicate.
      </p>
      <p className="text-sm">{overlap.explanation}</p>
      {overlap.matches.length === 0 ? (
        <PageState kind="empty" message="No potential overlap matches were returned for this work." />
      ) : (
        <div className="grid gap-3 lg:grid-cols-2">
          {overlap.matches.map((item) => (
            <article key={item.linked_project_id} className="svk-card p-4" data-tone="saffron">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <p className="svk-mono text-sm font-semibold">{item.linked_internal_project_id}</p>
                <StatusBadge value={item.outcome} />
              </div>
              <p className="mt-2 text-sm">{item.linked_work_description}</p>
              <dl className="mt-3 grid gap-2 text-xs sm:grid-cols-2">
                <div>
                  <dt className="text-[var(--muted)]">Constituency</dt>
                  <dd>{item.linked_constituency}</dd>
                </div>
                <div>
                  <dt className="text-[var(--muted)]">Category</dt>
                  <dd>{item.linked_category}</dd>
                </div>
                <div>
                  <dt className="text-[var(--muted)]">Amount</dt>
                  <dd>{formatAllocation(item.linked_allocation_amount)}</dd>
                </div>
                <div>
                  <dt className="text-[var(--muted)]">Date</dt>
                  <dd>{formatDate(item.linked_recommended_date)}</dd>
                </div>
              </dl>
              <div className="mt-3">
                <ScoreBar value={item.overall_overlap_score} label="Similarity" tone="priority" />
              </div>
              <p className="mt-2 text-xs text-[var(--muted)]">{item.explanation}</p>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}

export function ComplianceAnalyticsView({ projectId, mode }: { projectId: number; mode: DataMode }) {
  const intel = useProjectIntelligence(projectId, mode);
  const compliance = intel.compliance.data;

  if (intel.compliance.loading) return <PageState kind="loading" message="Loading compliance…" />;
  if (intel.compliance.error) return <PageState kind="error" message={intel.compliance.error} />;
  if (!compliance) return <PageState kind="unavailable" message="Compliance is unavailable for this project." />;

  const groups = [
    { label: "TRIGGERED", items: compliance.triggered_rules, tone: "danger" as const },
    { label: "NOT_TRIGGERED", items: compliance.non_triggered_rules, tone: "success" as const },
    { label: "NOT_ASSESSABLE", items: compliance.not_assessable_rules, tone: "saffron" as const },
  ];

  return (
    <div className="space-y-5">
      <div className="grid gap-3 sm:grid-cols-3">
        {groups.map((group) => (
          <Metric key={group.label} label={group.label} value={String(group.items.length)} tone={group.tone === "danger" ? "saffron" : group.tone} />
        ))}
      </div>
      <p className="text-sm">{compliance.explanation}</p>
      <p className="text-xs text-[var(--muted)]">Status: {compliance.compliance_status} · Mode: {compliance.compliance_mode}</p>
      {groups.map((group) => (
        <section key={group.label} className="space-y-3">
          <h3 className="text-sm font-semibold tracking-[0.12em] text-[var(--navy)]">{group.label}</h3>
          {group.items.length === 0 ? (
            <p className="text-sm text-[var(--muted)]">No rules in this group.</p>
          ) : (
            <div className="grid gap-3 lg:grid-cols-2">
              {group.items.map((rule) => (
                <article key={rule.rule_id} className="svk-card p-4" data-tone={group.tone === "danger" ? "danger" : group.tone}>
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <p className="svk-mono text-xs font-semibold">{rule.rule_id}</p>
                    <StatusBadge value={rule.status} />
                  </div>
                  <h4 className="mt-2 text-sm font-semibold text-[var(--navy)]">{rule.title}</h4>
                  <p className="mt-1 text-xs text-[var(--muted)]">{rule.category} · {rule.severity}</p>
                  <p className="mt-2 text-sm">{rule.explanation}</p>
                  {rule.missing_fields.length ? (
                    <p className="mt-2 text-xs text-[var(--muted)]">Missing: {rule.missing_fields.join(", ")}</p>
                  ) : null}
                </article>
              ))}
            </div>
          )}
        </section>
      ))}
    </div>
  );
}

export function AnalyticsSummaryBars({
  cost,
  time,
  overlap,
}: {
  cost?: number | null;
  time?: number | null;
  overlap?: number | null;
}) {
  return (
    <ContributionBars
      items={[
        { label: "COST", value: cost ?? null, unavailable: cost == null, reason: cost == null ? "Unavailable" : null },
        { label: "TIME", value: time ?? null, unavailable: time == null, reason: time == null ? "Unavailable" : null },
        { label: "OVERLAP", value: overlap ?? null, unavailable: overlap == null, reason: overlap == null ? "Unavailable" : null },
      ]}
    />
  );
}
